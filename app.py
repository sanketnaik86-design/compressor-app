import streamlit as st

st.title("🌀 Compressor Stage-wise Actual Performance")

# -------- INPUT --------
st.header("📥 Stage Data Input")

Cp = st.number_input("Cp (kJ/kg-K)", value=1.0, min_value=0.1)
Cv = st.number_input("Cv (kJ/kg-K)", value=0.718, min_value=0.1)
MW = st.number_input("Molecular Weight", value=28.0, min_value=1.0)
flow = st.number_input("Mass Flow (kg/hr)", value=10000.0, min_value=0.0)

# Stage Inputs
def stage_input(name):
    st.subheader(name)
    Pin = st.number_input(f"{name} Inlet Pressure (bar)", key=name+"Pin", min_value=0.01)
    Pout = st.number_input(f"{name} Outlet Pressure (bar)", key=name+"Pout", min_value=0.01)
    Tin = st.number_input(f"{name} Inlet Temp (°C)", key=name+"Tin")
    Tout = st.number_input(f"{name} Outlet Temp (°C)", key=name+"Tout")
    return Pin, Pout, Tin, Tout

Stage1 = stage_input("Stage 1")
Stage2 = stage_input("Stage 2")
Stage3 = stage_input("Stage 3")

# -------- CALC --------
K = Cp / Cv
R = 8.314 / MW
mass_flow = flow / 3600  # kg/s

def calc_stage(name, data):

    Pin, Pout, Tin, Tout = data

    if Pin <= 0 or Pout <= 0:
        st.error(f"{name}: Invalid pressure input")
        return 0

    Tin_K = Tin + 273.15
    Tout_K = Tout + 273.15

    if Tout_K <= Tin_K:
        st.warning(f"{name}: Outlet temp should be greater than inlet temp")
        return 0

    PR = Pout / Pin

    # Isentropic temp
    T2s = Tin_K * (PR)**((K-1)/K)

    # Efficiency
    eta = (T2s - Tin_K) / (Tout_K - Tin_K)

    if eta <= 0 or eta > 1:
        st.warning(f"{name}: Efficiency out of realistic range")

    # Polytropic index
    N = ((K-1)/(K*eta)) + 1 if eta != 0 else 0
    inv_N = 1/N if N != 0 else 0

    # Head
    Head = (N/(N-1)) * R * Tin_K * ((PR)**((N-1)/N) - 1) if N > 1 else 0

    # Power (kW)
    Power = mass_flow * Head

    # Volumetric flow
    Q = (mass_flow * R * Tin_K) / (Pin * MW)

    # -------- DISPLAY --------
    st.subheader(name)
    st.write(f"Pressure Ratio: {PR:.2f}")
    st.write(f"Temperature Ratio: {(Tout_K/Tin_K):.2f}")
    st.write(f"Isentropic Efficiency: {eta:.2f}")
    st.write(f"K Value: {K:.2f}")
    st.write(f"N Value: {N:.2f}")
    st.write(f"1/N: {inv_N:.3f}")
    st.write(f"Head: {Head:.2f} kJ/kg")
    st.write(f"Power: {Power:.2f} kW")
    st.write(f"Volumetric Flow: {Q:.2f} m³/s")

    return Power

# -------- RESULTS --------
Power_1 = calc_stage("Stage 1", Stage1)
Power_2 = calc_stage("Stage 2", Stage2)
Power_3 = calc_stage("Stage 3", Stage3)

total_power = Power_1 + Power_2 + Power_3

st.header("⚡ Total Power")
st.write(f"Total Compressor Power: {total_power:.2f} kW")

# -------- INTERPRETATION --------
st.header("🧠 Interpretation")

if total_power > 500:
    st.warning("⚠️ High power consumption")

if total_power == 0:
    st.error("❌ Check input values")
