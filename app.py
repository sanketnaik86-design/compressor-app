import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Compressor Digital Twin", layout="wide")

st.title("🌀 Compressor Digital Twin Dashboard")

# ---------------- GLOBAL INPUT ----------------
st.header("📥 Global Input")

flow = st.number_input("Mass Flow (kg/hr)", value=10000.0)
stages = st.selectbox("Number of Stages", [1, 2, 3], index=2)

mass_flow = flow / 3600

# ---------------- GAS COMPOSITION ----------------
st.header("🧪 Gas Composition (Mole %)")

c1, c2, c3, c4, c5 = st.columns(5)

CH4 = c1.number_input("CH4 %", value=80.0)
C2H6 = c2.number_input("C2H6 %", value=5.0)
N2 = c3.number_input("N2 %", value=10.0)
H2 = c4.number_input("H2 %", value=3.0)
CO2 = c5.number_input("CO2 %", value=2.0)

total = CH4 + C2H6 + N2 + H2 + CO2

if total <= 0:
    st.error("❌ Composition cannot be zero")
    st.stop()

if abs(total - 100) > 0.5:
    st.warning("⚠️ Total composition should be ~100%")

# ---------------- GAS PROPERTY ----------------
def gas_properties(CH4, C2H6, N2, H2, CO2):

    MW_dict = {"CH4":16, "C2H6":30, "N2":28, "H2":2, "CO2":44}
    Cp_dict = {"CH4":2.2, "C2H6":1.7, "N2":1.04, "H2":14.3, "CO2":0.85}

    y = {
        "CH4": CH4/100,
        "C2H6": C2H6/100,
        "N2": N2/100,
        "H2": H2/100,
        "CO2": CO2/100
    }

    MW_mix = sum(y[i]*MW_dict[i] for i in y)
    Cp_mix = sum(y[i]*Cp_dict[i] for i in y)

    R = 8.314 / MW_mix
    Cv_mix = Cp_mix - R

    if Cv_mix <= 0:
        st.error("❌ Invalid gas properties (Cv ≤ 0)")
        st.stop()

    return MW_mix, Cp_mix, Cv_mix

MW_mix, Cp_mix, Cv_mix = gas_properties(CH4, C2H6, N2, H2, CO2)

st.success(f"MW: {MW_mix:.2f} | Cp: {Cp_mix:.2f} | Cv: {Cv_mix:.2f}")

# ---------------- STAGE INPUT ----------------
def stage_input(name):
    st.subheader(name)

    c1, c2 = st.columns(2)

    Pin = c1.number_input(f"{name} Pin (bar)", key=name+"Pin", min_value=0.0)
    Tin = c1.number_input(f"{name} Tin (°C)", key=name+"Tin")

    Pout = c2.number_input(f"{name} Pout (bar)", key=name+"Pout", min_value=0.0)
    Tout = c2.number_input(f"{name} Tout (°C)", key=name+"Tout")

    return Pin, Pout, Tin, Tout

stage_data = [stage_input(f"Stage {i+1}") for i in range(stages)]

# ---------------- CALC ----------------
def calc_stage(data, i):

    try:
        Pin, Pout, Tin, Tout = data

        if Pin <= 0 or Pout <= Pin:
            return None

        Tin_K = Tin + 273.15
        Tout_K = Tout + 273.15

        if Tout_K <= Tin_K:
            return None

        K = Cp_mix / Cv_mix
        R = 8.314 / MW_mix

        PR = Pout / Pin

        T2s = Tin_K * (PR)**((K - 1)/K)

        dT_act = Tout_K - Tin_K
        if dT_act <= 0.001:
            return None

        eta = (T2s - Tin_K) / dT_act
        eta = np.clip(eta, 0.01, 1)

        eta_percent = eta * 100

        N = ((K - 1)/(K * eta)) + 1

        if abs(N - 1) < 0.001:
            return None

        Head = (N/(N-1)) * R * Tin_K * ((PR)**((N-1)/N) - 1)
        Power = mass_flow * Head

        Pin_Pa = Pin * 1e5
        Q = (mass_flow * R * 1000 * Tin_K) / Pin_Pa

        issues = []
        if eta_percent < 65:
            issues.append("Low efficiency")
        if PR > 4:
            issues.append("Surge risk")
        if Tout_K > T2s + 40:
            issues.append("Cooling issue")

        return {
            "Stage": i,
            "Efficiency": eta_percent,
            "Power": Power,
            "PR": PR,
            "Flow": Q,
            "Tout": Tout_K,
            "Issues": issues
        }

    except Exception as e:
        st.error(f"Stage {i} Error: {e}")
        return None

# ---------------- RESULTS ----------------
st.header("⚙️ Stage-wise Results")

results = []
total_power = 0

cols = st.columns(int(stages))

for i, data in enumerate(stage_data):
    res = calc_stage(data, i+1)

    with cols[i]:
        st.subheader(f"Stage {i+1}")

        if res:
            st.metric("Efficiency", f"{res['Efficiency']:.1f} %")
            st.metric("Power", f"{res['Power']:.1f} kW")
            st.metric("PR", f"{res['PR']:.2f}")
            st.metric("Flow", f"{res['Flow']:.2f}")

            for issue in res["Issues"]:
                st.warning(issue)

            if not res["Issues"]:
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

# ---------------- FILE UPLOAD ----------------
st.header("📂 Upload Plant Data")

file = st.file_uploader("Upload CSV")

if file:
    try:
        df = pd.read_csv(file)
        st.dataframe(df.head())

        eff_cols = []

        for i in range(stages):
            s = i + 1

            if all(col in df.columns for col in [
                f"Stage{s}_Pin", f"Stage{s}_Pout",
                f"Stage{s}_Tin", f"Stage{s}_Tout"]):

                Pin = df[f"Stage{s}_Pin"]
                Pout = df[f"Stage{s}_Pout"]
                Tin = df[f"Stage{s}_Tin"] + 273.15
                Tout = df[f"Stage{s}_Tout"] + 273.15

                valid = (Tout - Tin) > 0

                PR = Pout / Pin
                K = Cp_mix / Cv_mix

                T2s = Tin * (PR)**((K - 1)/K)
                eta = np.where(valid, (T2s - Tin)/(Tout - Tin), np.nan)

                df[f"Stage{s}_Eff"] = eta * 100
                eff_cols.append(f"Stage{s}_Eff")

        if eff_cols:
            st.line_chart(df[eff_cols])
        else:
            st.warning("No valid columns found in file")

    except Exception as e:
        st.error(f"File Error: {e}")

# ---------------- FINAL ----------------
st.header("🧠 Diagnosis")

if total_power == 0:
    st.error("Check Inputs")
elif total_power > 800:
    st.warning("Compressor overload")
else:
    st.success("Compressor Normal")

st.divider()
st.markdown("Digital Twin by Sanket Naik 🚀")
