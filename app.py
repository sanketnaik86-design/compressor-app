import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Compressor Digital Twin", layout="wide")

st.title("🌀 Compressor Digital Twin Dashboard")

# ---------------- GLOBAL INPUT ----------------
st.header("📥 Global Input")

col1, col2 = st.columns(2)

with col1:
    flow = st.number_input("Mass Flow (kg/hr)", value=10000.0)

with col2:
    stages = st.selectbox("Number of Stages", [1, 2, 3], index=2)

mass_flow = flow / 3600

# ---------------- STAGE INPUT ----------------
def stage_input(name):
    st.subheader(f"🔹 {name}")

    c1, c2, c3 = st.columns(3)

    with c1:
        Pin = st.number_input(f"{name} Inlet Pressure (bar)", key=name+"Pin", min_value=0.0)
        Tin = st.number_input(f"{name} Inlet Temp (°C)", key=name+"Tin")

    with c2:
        Pout = st.number_input(f"{name} Outlet Pressure (bar)", key=name+"Pout", min_value=0.0)
        Tout = st.number_input(f"{name} Outlet Temp (°C)", key=name+"Tout")

    with c3:
        MW = st.number_input(f"{name} MW", key=name+"MW", value=28.0, min_value=1.0)
        Cp = st.number_input(f"{name} Cp", key=name+"Cp", value=1.005, min_value=0.1)
        Cv = st.number_input(f"{name} Cv", key=name+"Cv", value=0.718, min_value=0.1)

    return Pin, Pout, Tin, Tout, MW, Cp, Cv

stage_data = [stage_input(f"Stage {i+1}") for i in range(stages)]

# ---------------- CALCULATION ----------------
def calc_stage(data, stage_no):
    try:
        Pin, Pout, Tin, Tout, MW, Cp, Cv = data

        if Pin <= 0 or Pout <= Pin or Cp <= Cv:
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
        if eta_percent > 90:
            issues.append("Sensor issue")
        if PR > 4:
            issues.append("Surge risk")
        if Tout_K > T2s + 40:
            issues.append("Cooling issue")

        return {
            "Stage": stage_no,
            "PR": PR,
            "Efficiency": eta_percent,
            "Power": Power,
            "Flow": Q,
            "Tout": Tout_K,
            "Issues": issues
        }

    except:
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
st.header("❄️ Intercooler")

if len(results) > 1:
    for i in range(len(results)-1):
        delta = results[i]["Tout"] - (stage_data[i+1][2] + 273.15)

        if delta < 10:
            st.warning(f"Stage {i+1}-{i+2}: Poor cooling")
        else:
            st.success(f"Stage {i+1}-{i+2}: OK")

# ---------------- SURGE ----------------
st.header("⚠️ Surge")

for r in results:
    if r["PR"] > 4 and r["Flow"] < 2:
        st.error(f"Stage {r['Stage']} → HIGH RISK")
    elif r["PR"] > 3:
        st.warning(f"Stage {r['Stage']} → Moderate")
    else:
        st.success(f"Stage {r['Stage']} → Safe")

# ---------------- TREND ----------------
st.header("📈 Efficiency Trend")

if st.button("Generate Trend"):
    time = np.arange(0, 50)

    data = {}
    for i in range(stages):
        data[f"Stage {i+1}"] = 75 + 5*np.sin(0.2*time + i)

    df = pd.DataFrame(data)
    st.line_chart(df)

# ---------------- FILE ----------------
st.header("📂 Upload CSV")

file = st.file_uploader("Upload CSV")

if file:
    df = pd.read_csv(file)
    st.write(df.head())

    if "Efficiency" in df.columns:
        st.line_chart(df["Efficiency"])

# ---------------- FINAL ----------------
st.header("🧠 Diagnosis")

if total_power == 0:
    st.error("Check Inputs")
elif total_power > 800:
    st.warning("Overload")
else:
    st.success("Normal")

st.divider()
st.markdown("Digital Twin by Sanket Naik")
