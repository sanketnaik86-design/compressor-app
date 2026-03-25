import streamlit as st

st.title("🌀 Multi-Stage Compressor (Stage-wise Efficiency & Power)")

# ---------------- INPUT ----------------
st.header("📥 Input Data")

P1 = st.number_input("Inlet Pressure (bar)", value=1.0)
P_final = st.number_input("Final Pressure (bar)", value=9.0)
T1 = st.number_input("Inlet Temperature (°C)", value=30.0)
flow = st.number_input("Flowrate (kg/hr)", value=10000.0)

st.subheader("Design Parameters")
stages = st.selectbox("Number of Stages", [2, 3])

gamma = st.number_input("Gamma (Cp/Cv)", value=1.4)
Cp = st.number_input("Cp (kJ/kg-K)", value=1.0)

# Individual stage efficiency input
st.write("### Stage-wise Efficiency")
eff_stage = []
for i in range(stages):
    eff = st.number_input(f"Efficiency Stage {i+1}", value=0.75, key=i)
    eff_stage.append(eff)

intercool_temp = st.number_input("Intercooler Outlet Temp (°C)", value=40.0)

# ---------------- CALCULATION ----------------

Cp = Cp * 1000  # J/kg-K
T1_K = T1 + 273.15
mass_flow = flow / 3600  # kg/s

PR_total = P_final / P1
PR_stage = PR_total ** (1 / stages)

st.header("📊 Results")

total_power_actual = 0
total_power_ideal = 0

T_in = T1_K
P_in = P1

for i in range(stages):

    st.subheader(f"Stage {i+1}")

    # Pressure
    P_out = P_in * PR_stage

    # Ideal (isentropic) outlet temp
    T_out_ideal = T_in * (PR_stage)**((gamma-1)/gamma)

    # Actual outlet temp
    eta = eff_stage[i]
    T_out_actual = T_in + (T_out_ideal - T_in) / eta

    # Power
    Power_ideal = mass_flow * Cp * (T_out_ideal - T_in) / 1000
    Power_actual = mass_flow * Cp * (T_out_actual - T_in) / 1000

    total_power_actual += Power_actual
    total_power_ideal += Power_ideal

    # Display
    st.write(f"Outlet Pressure: {P_out:.2f} bar")
    st.write(f"Ideal Outlet Temp: {T_out_ideal - 273.15:.2f} °C")
    st.write(f"Actual Outlet Temp: {T_out_actual - 273.15:.2f} °C")

    st.write(f"Ideal Power: {Power_ideal:.2f} kW")
    st.write(f"Actual Power: {Power_actual:.2f} kW")

    st.write(f"Stage Efficiency: {eta:.2f}")

    # Intercooling
    if i < stages - 1:
        T_in = intercool_temp + 273.15
    else:
        T_in = T_out_actual

    P_in = P_out

# ---------------- TOTAL ----------------

st.header("⚡ Total Power")

st.write(f"Total Ideal Power: {total_power_ideal:.2f} kW")
st.write(f"Total Actual Power: {total_power_actual:.2f} kW")

overall_eff = total_power_ideal / total_power_actual

st.write(f"Overall Efficiency: {overall_eff:.2f}")

# ---------------- INTERPRETATION ----------------

st.header("🧠 Interpretation")

if total_power_actual > 500:
    st.warning("⚠️ High Power Consumption")

if (T_out_actual - 273.15) > 150:
    st.error("❌ High Discharge Temperature")

else:
    st.success("✅ Safe Operation")
