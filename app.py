import streamlit as st

st.title("🌀 Compressor Stage-wise Actual Performance (From Plant Data)")

# -------- INPUT --------
st.header("📥 Stage Data Input")

Cp = st.number_input("Cp (kJ/kg-K)", value=1.0)
Cv = st.number_input("Cv (kJ/kg-K)", value=0.718)
MW = st.number_input("Molecular Weight", value=28.0)
flow = st.number_input("Mass Flow (kg/hr)", value=10000.0)

# Stage Inputs
def stage_input(name):
    st.subheader(name)
    Pin = st.number_input(f"{name} Inlet Pressure (bar)", key=name+"Pin")
    Pout = st.number_input(f"{name} Outlet Pressure (bar)", key=name+"Pout")
    Tin = st.number_input(f"{name} Inlet Temp (°C)", key=name+"Tin")
    Tout = st.number_input(f"{name} Outlet Temp (°C)", key=name+"Tout")
    return Pin, Pout, Tin, Tout

A = stage_input("C201A")
B = stage_input("C201B")
C = stage_input("C201C")

# -------- CALC --------
K = Cp / Cv
R = 8.314 / MW
mass_flow = flow / 3600

def calc_stage(name, data):

    Pin, Pout, Tin, Tout = data

    Tin_K = Tin + 273.15
    Tout_K = Tout + 273.15

    PR = Pout / Pin

    # Isentropic temp
    T2s = Tin_K * (PR)**((K-1)/K)

    # Efficiency
    eta = (T2s - Tin_K) / (Tout_K - Tin_K)

    # Polytropic index
    N = ((K-1)/(K*eta)) + 1
    inv_N = 1/N

    # Head
    Head = (N/(N-1)) * R * Tin_K * ((PR)**((N-1)/N) - 1)

    # Power
    Power = mass_flow * Head

    # Volumetric flow
    Q = (mass_flow * R * Tin_K) / (Pin * MW)

    st.subheader(name)
    st.write(f"Pressure Ratio: {PR:.2f}")
    st.write(f"Temp Ratio: {(Tout_K/Tin_K):.2f}")
    st.write(f"Efficiency: {eta:.2f}")
    st.write(f"K Value: {K:.2f}")
    st.write(f"N Value: {N:.2f}")
    st.write(f"1/N: {inv_N:.3f}")
    st.write(f"Head: {Head:.2f} kJ/kg")
    st.write(f"Power: {Power:.2f} kW")
    st.write(f"Volumetric Flow: {Q:.2f} m3/s")

    return Power

# -------- RESULTS --------
Power_A = calc_stage("Product_C201A", A)
Power_B = calc_stage("Product_C201B", B)
Power_C = calc_stage("Product_C201C", C)

total_power = Power_A + Power_B + Power_C

st.header("⚡ Total Power")
st.write(f"Total Compressor Power: {total_power:.2f} kW")
