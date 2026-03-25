import streamlit as st

st.set_page_config(page_title="Compressor Performance", layout="wide")

st.title("🌀 Compressor Stage-wise Actual Performance")

# -------- INPUT --------
st.header("📥 Input Data")

col1, col2 = st.columns(2)

with col1:
    Cp = st.number_input("Cp (kJ/kg-K)", value=1.0, min_value=0.1)
    Cv = st.number_input("Cv (kJ/kg-K)", value=0.718, min_value=0.1)

with col2:
    MW = st.number_input("Molecular Weight (kg/kmol)", value=28.0, min_value=1.0)
    flow = st.number_input("Mass Flow (kg/hr)", value=10000.0, min_value=0.0)

# -------- CONSTANTS --------
K = Cp / Cv
R = 8.314 / MW
mass_flow = flow / 3600  # kg/s

# -------- STAGE INPUT --------
def stage_input(name):
    st.subheader(f"🔹 {name}")

    c1, c2 = st.columns(2)

    with c1:
        Pin = st.number_input(f"{name} Inlet Pressure (bar)", key=name+"Pin", min_value=0.01)
        Tin = st.number_input(f"{name} Inlet Temp (°C)", key=name+"Tin")

    with c2:
        Pout = st.number_input(f"{name} Outlet Pressure (bar)", key=name+"Pout", min_value=0.01)
        Tout = st.number_input(f"{name} Outlet Temp (°C)", key=name+"Tout")

    return Pin, Pout, Tin, Tout

Stage1 = stage_input("Stage 1")
Stage2 = stage_input("Stage 2")
Stage3 = stage_input("Stage 3")

# -------- CALC FUNCTION --------
def calc_stage(name, data):

    Pin, Pout, Tin, Tout = data

    st.markdown(f"### 📊 {name} Results")

    # ---- VALIDATION ----
    if Pin <= 0 or Pout <= 0:
        st.error("Invalid pressure")
        return 0, 0

    if Pout <= Pin:
        st.error("Pout must be > Pin")
        return 0, 0

    Tin_K = Tin + 273.15
    Tout_K = Tout + 273.15

    if Tout_K <= Tin_K:
        st.error("Tout must be > Tin")
        return 0, 0

    # ---- CALC ----
    PR = Pout / Pin

    T2s = Tin_K * (PR)**((K - 1) / K)

    delta_T_actual = Tout_K - Tin_K
    delta_T_ideal = T2s - Tin_K

    if delta_T_actual <= 0:
        return 0, 0

    # ---- EFFICIENCY ----
    eta = delta_T_ideal / delta_T_actual
    eta_percent = eta * 100

    # Clamp 0–100%
    eta_percent = max(0, min(eta_percent, 100))

    # ---- POLYTROPIC INDEX ----
    if eta > 0:
        N = ((K - 1) / (K * eta)) + 1
    else:
        N = 0

    # ---- HEAD ----
    Head = (N/(N-1)) * R * Tin_K * ((PR)**((N-1)/N) - 1) if N > 1 else 0

    # ---- POWER ----
    Power = mass_flow * Head

    # ---- FLOW ----
    Q = (mass_flow * R * Tin_K) / (Pin * 100)

    # ---- DISPLAY ----
    c1, c2, c3 = st.columns(3)

    c1.metric("Pressure Ratio", f"{PR:.2f}")
    c1.metric("Temp Ratio", f"{(Tout_K/Tin_K):.2f}")

    c2.metric("Efficiency", f"{eta_percent:.1f} %")
    c2.metric("Polytropic Index", f"{N:.2f}")

    c3.metric("Head", f"{Head:.2f} kJ/kg")
    c3.metric("Power", f"{Power:.2f} kW")

    st.write(f"Volumetric Flow: **{Q:.2f} m³/s**")

    # ---- DIAGNOSIS ----
    if eta_percent < 60:
        st.warning("⚠️ Low efficiency → fouling / leakage")

    if eta_percent > 90:
        st.info("ℹ️ Check sensors → efficiency too high")

    if Tout_K > T2s + 50:
        st.warning("🔥 High outlet temp")

    return Power, eta_percent

# -------- RESULTS --------
st.header("⚙️ Stage-wise Results")

P1, E1 = calc_stage("Stage 1", Stage1)
P2, E2 = calc_stage("Stage 2", Stage2)
P3, E3 = calc_stage("Stage 3", Stage3)

total_power = P1 + P2 + P3

# -------- TOTAL POWER --------
st.header("⚡ Total Power")

st.success(f"Total Compressor Power: {total_power:.2f} kW")

# -------- EFFICIENCY SUMMARY --------
st.header("📊 Stage-wise Efficiency Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Stage 1", f"{E1:.1f} %")
col2.metric("Stage 2", f"{E2:.1f} %")
col3.metric("Stage 3", f"{E3:.1f} %")

# -------- OVERALL --------
avg_eff = (E1 + E2 + E3) / 3 if (E1+E2+E3) > 0 else 0

st.metric("Overall Avg Efficiency", f"{avg_eff:.1f} %")

# -------- FINAL DIAGNOSIS --------
st.header("🧠 Overall Diagnosis")

if total_power == 0:
    st.error("❌ Check inputs")

elif total_power > 800:
    st.warning("⚠️ Compressor overload")

else:
    st.success("✅ Compressor normal")
