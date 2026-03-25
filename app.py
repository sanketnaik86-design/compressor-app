import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Compressor Digital Twin", layout="wide")

st.title("🌀 Compressor Digital Twin Dashboard")

# ---------------- GLOBAL INPUT ----------------
st.header("📥 Global Input")

flow = st.number_input("Mass Flow (kg/hr)", value=10000.0)
stages = st.selectbox("Number of Stages", [1, 2, 3], index=2)

mass_flow = flow / 3600

# ---------------- STAGE INPUT ----------------
def stage_input(name):
    st.subheader(name)

    Pin = st.number_input(f"{name} Pin (bar)", key=name+"Pin", min_value=0.0)
    Pout = st.number_input(f"{name} Pout (bar)", key=name+"Pout", min_value=0.0)

    Tin = st.number_input(f"{name} Tin (°C)", key=name+"Tin")
    Tout = st.number_input(f"{name} Tout (°C)", key=name+"Tout")

    MW = st.number_input(f"{name} MW", key=name+"MW", value=28.0)
    Cp = st.number_input(f"{name} Cp", key=name+"Cp", value=1.005)
    Cv = st.number_input(f"{name} Cv", key=name+"Cv", value=0.718)

    return Pin, Pout, Tin, Tout, MW, Cp, Cv

stage_data = [stage_input(f"Stage {i+1}") for i in range(stages)]

# ---------------- SAFE CALC ----------------
def calc_stage(data, i):
    try:
        Pin, Pout, Tin, Tout, MW, Cp, Cv = data

        if Pin <= 0 or Pout <= Pin:
            return None

        if Cp <= Cv:
            return None

        Tin_K = Tin + 273.15
        Tout_K = Tout + 273.15

        if Tout_K <= Tin_K:
            return None

        K = Cp / Cv
        R = 8.314 / MW

        PR = Pout / Pin

        T2s = Tin_K * (PR)**((K - 1)/K)

        dT_act = Tout_K - Tin_K
        if dT_act <= 0.001:
            return None

        eta = (T2s - Tin_K) / dT_act
        eta = max(0.01, min(eta, 1))

        N = ((K - 1)/(K * eta)) + 1

        # 🔥 SAFETY
        if abs(N - 1) < 0.01:
            return None

        Head = (N/(N-1)) * R * Tin_K * ((PR)**((N-1)/N) - 1)
        Power = mass_flow * Head

        Pin_Pa = Pin * 1e5
        Q = (mass_flow * R * 1000 * Tin_K) / Pin_Pa

        return {
            "stage": i,
            "eff": eta*100,
            "power": Power,
            "PR": PR,
            "flow": Q,
            "Tout": Tout_K,
            "T2s": T2s
        }

    except Exception as e:
        st.error(f"Stage {i} Error: {e}")
        return None

# ---------------- RESULTS ----------------
st.header("⚙️ Results")

results = []
total_power = 0

for i, data in enumerate(stage_data):
    res = calc_stage(data, i+1)

    if res:
        st.write(f"### Stage {i+1}")
        st.write(f"Efficiency: {res['eff']:.1f} %")
        st.write(f"Power: {res['power']:.1f} kW")
        st.write(f"PR: {res['PR']:.2f}")

        results.append(res)
        total_power += res["power"]
    else:
        st.warning(f"Stage {i+1} → Invalid Data")

# ---------------- TOTAL ----------------
st.header("⚡ Total")

st.write(f"Total Power: {total_power:.2f} kW")

# ---------------- INTERCOOLER ----------------
if len(results) > 1:
    st.header("❄️ Intercooler")

    for i in range(len(results)-1):
        delta = results[i]["Tout"] - (stage_data[i+1][2] + 273.15)

        if delta < 10:
            st.warning(f"Stage {i+1}-{i+2}: Poor cooling")
        else:
            st.success(f"Stage {i+1}-{i+2}: OK")

# ---------------- GRAPH ----------------
if st.button("Show Trend"):
    try:
        time = np.arange(0, 50)

        fig, ax = plt.subplots()

        for i in range(stages):
            eff = 75 + 5*np.sin(0.2*time + i)
            ax.plot(time, eff, label=f"Stage {i+1}")

        ax.legend()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Graph error: {e}")
