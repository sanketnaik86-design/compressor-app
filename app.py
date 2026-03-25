import streamlit as st

# Title
st.title("🌀 Multi-Stage Compressor with Intercooling")

# ---------------- INPUT SECTION ----------------
st.header("📥 Input Data")

# Basic Inputs
P1 = st.number_input("Inlet Pressure (bar)", value=1.0, min_value=0.1)
P_final = st.number_input("Final Pressure (bar)", value=9.0, min_value=0.1)
T1 = st.number_input("Inlet Temperature (°C)", value=30.0)
flow = st.number_input("Flowrate (kg/hr)", value=10000.0, min_value=0.0)

st.subheader("Design Parameters")
stages = st.selectbox("Number of Stages", [2, 3])
eff = st.number_input("Efficiency (0-1)", value=0.75, min_value=0.1, max_value=1.0)
gamma = st.number_input("Gamma (Cp/Cv)", value=1.4, min_value=1.0)
Cp = st.number_input("Cp (kJ/kg-K)", value=1.0, min_value=0.1)
intercool_temp = st.number_input("Intercooler Outlet Temp (°C)", value=40.0)

# ---------------- CALCULATIONS ----------------

# Unit conversions
Cp = Cp * 1000            # kJ/kg-K → J/kg-K
T1_K = T1 + 273.15       # °C → K

# Pressure ratio
PR_total = P_final / P1
PR_stage = PR_total ** (1 / stages)

st.header("📊 Results")

total_power = 0
T_in_stage = T1_K
P_in_stage = P1

for i in range(1, stages + 1):

    # Stage pressure
    P_out_stage = P_in_stage * PR_stage

    # Temperature after compression (isentropic)
    T_out_stage = T_in_stage * (PR_stage) ** ((gamma - 1) / gamma)

    # Power calculation (kW)
    mass_flow = flow / 3600  # kg/hr → kg/s
    Power_stage = (mass_flow * Cp * (T_out_stage - T_in_stage)) / (eff * 1000)

    total_power += Power_stage

    # Display results
    st.subheader(f"Stage {i}")
    st.write(f"Outlet Pressure: {P_out_stage:.2f} bar")
    st.write(f"Outlet Temperature: {T_out_stage - 273.15:.2f} °C")
    st.write(f"Power Required: {Power_stage:.2f} kW")

    # Intercooling logic
    if i < stages:
        T_in_stage = intercool_temp + 273.15
    else:
        T_in_stage = T_out_stage

    P_in_stage = P_out_stage

# ---------------- TOTAL POWER ----------------
st.header("⚡ Total Power")
st.write(f"{total_power:.2f} kW")

# ---------------- INTERPRETATION ----------------
st.header("🧠 Interpretation")

if total_power > 500:
    st.warning("⚠️ High Power Consumption - Check staging or intercooling efficiency")

if (T_out_stage - 273.15) > 150:
    st.error("❌ High Discharge Temperature - Risk of compressor damage")
else:
    st.success("✅ Operating in safe temperature range")