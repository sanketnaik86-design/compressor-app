import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Compressor Digital Twin", layout="wide")

st.title("🌀 Compressor Digital Twin Dashboard")

# ---------------- GLOBAL INPUT ----------------
st.header("📥 Global Input")

col1, col2 = st.columns(2)

with col1:
    flow = st.number_input("Mass Flow (kg/hr)", value=10000.0)

with col2:
    stages = st.selectbox("Number of Stages", [1, 2, 3], index=2)

mass_flow = flow / 3600  # kg/s

# ---------------- STAGE INPUT ----------------
def stage_input(name):
    st.subheader(f"🔹 {name}")

    c1, c2, c3 = st.columns(3)

    with c1:
        Pin = st.number_input(f"{name} Inlet Pressure (bar)", key=name+"Pin")
        Tin = st.number_input(f"{name} Inlet Temp (°C)", key=name+"Tin")

    with c2:
        Pout = st.number_input(f"{name} Outlet Pressure (bar)", key=name+"Pout")
        Tout = st.number_input(f"{name} Outlet Temp (°C)", key=name+"Tout")

    with c3:
        MW = st.number_input(f"{name} MW", key=name+"MW", value=28.0)
        Cp = st.number_input(f"{name} Cp", key=name+"Cp", value=1.005)
        Cv = st.number_input(f"{name} Cv", key=name+"Cv", value=0.718)

    return Pin, Pout, Tin, Tout, MW, Cp, Cv

stage_data = []
for i in range(stages):
    stage_data.append(stage_input(f"Stage {i+1}"))

# ---------------- CALCULATION ----------------
def calc_stage(data, stage_no):

    Pin, Pout, Tin, Tout, MW, Cp, Cv = data

    if Pin <= 0 or Pout <= 0 or Pout <= Pin:
        return None

    if Cp <= Cv:
        return None

    Tin_K = Tin + 273.15
    Tout_K = Tout + 273.15

    if Tout_K <= Tin_K:
        return None

    # Properties
    K = Cp / Cv
    R = 8.314 / MW

    PR = Pout / Pin

    # Ideal temp
    T2s = Tin_K * (PR)**((K - 1)/K)

    dT_act = Tout_K - Tin_K
    dT_ideal = T2s - Tin_K

    if dT_act <= 0.001:
        return None

    eta = dT_ideal / dT_act
    eta = max(0.01, min(eta, 1))

    eta_percent = eta * 100

    # Polytropic index
    N = ((K - 1)/(K * eta)) + 1

    # Head
    Head = (N/(N-1)) * R * Tin_K * ((PR)**((N-1)/N) - 1)

    # Power
    Power = mass_flow * Head

    # Flow
    Pin_Pa = Pin * 1e5
    Q = (mass_flow * R * 1000 * Tin_K) / Pin_Pa

    # Diagnosis
    issues = []

    if eta_percent < 65:
        issues.append("Low efficiency → fouling/leakage")

    if eta_percent > 90:
        issues.append("Check sensors → too high efficiency")

    if PR > 4:
        issues.append("High PR → surge risk")

    if Tout_K > T2s + 40:
        issues.append("High outlet temp → cooling issue")

    return {
        "Stage": stage_no,
        "PR": PR,
        "Efficiency": eta_percent,
        "Power": Power,
        "Head": Head,
        "Flow": Q,
        "Tout": Tout_K,
        "T2s": T2s,
        "Issues": issues
    }

# ---------------- RESULTS ----------------
st.header("⚙️ Stage-wise Results")

results = []
total_power = 0

cols = st.columns(stages)

for i, data in enumerate(stage_data):
    res = calc_stage(data, i+1)

    with cols[i]:
        st.subheader(f"Stage {i+1}")

        if res:
            st.metric("Efficiency", f"{res['Efficiency']:.1f} %")
            st.metric("Power", f"{res['Power']:.1f} kW")
            st.metric("PR", f"{res['PR']:.2f}")
            st.metric("Flow", f"{res['Flow']:.2f} m³/s")

            if res["Issues"]:
                for issue in res["Issues"]:
                    st.warning(issue)
            else:
                st.success("Healthy")

            total_power += res["Power"]
            results.append(res)
        else:
            st.error("Invalid Data")

# ---------------- TOTAL ----------------
st.header("⚡ Total Performance")

st.success(f"Total Power: {total_power:.2f} kW")

if results:
    avg_eff = np.mean([r["Efficiency"] for r in results])
    st.metric("Overall Efficiency", f"{avg_eff:.1f} %")

# ---------------- INTERCOOLER ----------------
st.header("❄️ Intercooler Performance")

for i in range(len(results)-1):
    T_out = results[i]["Tout"]
    T_next_in = stage_data[i+1][2] + 273.15

    delta = T_out - T_next_in

    st.write(f"Stage {i+1} → Stage {i+2}")

    if delta < 10:
        st.warning("Poor cooling → intercooler issue")
    elif delta > 50:
        st.info("Excellent cooling")
    else:
        st.success("Normal cooling")

# ---------------- SURGE ----------------
st.header("⚠️ Surge Risk Indicator")

for r in results:
    if r["PR"] > 4 and r["Flow"] < 2:
        st.error(f"Stage {r['Stage']} → HIGH SURGE RISK")
    elif r["PR"] > 3:
        st.warning(f"Stage {r['Stage']} → Moderate risk")
    else:
        st.success(f"Stage {r['Stage']} → Safe")

# ---------------- TREND GRAPH ----------------
st.header("📈 Efficiency Trend (Simulation)")

if st.button("Generate Trend"):
    time = np.arange(0, 50)

    fig = plt.figure()

    for i in range(stages):
        eff = 75 + 5*np.sin(0.2*time + i)
        plt.plot(time, eff, label=f"Stage {i+1}")

    plt.xlabel("Time")
    plt.ylabel("Efficiency (%)")
    plt.legend()

    st.pyplot(fig)

# ---------------- FILE UPLOAD ----------------
st.header("📂 Upload Plant Data (CSV)")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write(df.head())

    if "Efficiency" in df.columns:
        fig = plt.figure()
        plt.plot(df["Efficiency"])
        plt.title("Uploaded Efficiency Trend")
        st.pyplot(fig)

# ---------------- FINAL DIAGNOSIS ----------------
st.header("🧠 Overall Diagnosis")

if total_power == 0:
    st.error("Check Inputs")

elif total_power > 800:
    st.warning("⚠️ Compressor overload")

else:
    st.success("✅ Compressor operating normally")

# ---------------- FOOTER ----------------
st.divider()
st.markdown("<p style='text-align: center; color: gray;'>Digital Twin by Sanket Naik</p>", unsafe_allow_html=True)
