def calc_stage(name, data):

    Pin, Pout, Tin, Tout, MW_stage = data

    st.markdown(f"### 📊 {name} Results")

    if Pin <= 0 or Pout <= 0:
        st.error("Invalid pressure")
        return 0, 0

    if Pout <= Pin:
        st.error("Outlet pressure must be greater than inlet")
        return 0, 0

    Tin_K = Tin + 273.15
    Tout_K = Tout + 273.15

    if Tout_K <= Tin_K:
        st.error("Outlet temp must be higher than inlet")
        return 0, 0

    # -------- NEW: Stage-wise R --------
    R_stage = 8.314 / MW_stage   # kJ/kg-K

    PR = Pout / Pin

    T2s = Tin_K * (PR)**((K - 1) / K)

    eta = (T2s - Tin_K) / (Tout_K - Tin_K)
    eta = max(0, min(eta, 1))

    eta_percent = eta * 100

    N = ((K - 1) / (K * eta)) + 1 if eta > 0 else 1.01

    # -------- UPDATED HEAD --------
    Head = (N/(N-1)) * R_stage * Tin_K * ((PR)**((N-1)/N) - 1)

    Power = mass_flow * Head

    # -------- UPDATED FLOW --------
    Pin_Pa = Pin * 1e5
    Q = (mass_flow * R_stage * 1000 * Tin_K) / Pin_Pa

    # -------- DISPLAY --------
    c1, c2, c3 = st.columns(3)

    c1.metric("Pressure Ratio", f"{PR:.2f}")
    c1.metric("Temp Ratio", f"{(Tout_K/Tin_K):.2f}")

    c2.metric("Efficiency", f"{eta_percent:.1f} %")
    c2.metric("Polytropic Index", f"{N:.2f}")

    c3.metric("Head", f"{Head:.2f} kJ/kg")
    c3.metric("Power", f"{Power:.2f} kW")

    st.write(f"Volumetric Flow: **{Q:.2f} m³/s**")

    # Diagnosis remains same
    if eta_percent < 65:
        st.warning("⚠️ Low efficiency → fouling / leakage")

    elif eta_percent > 90:
        st.info("ℹ️ Check sensors → efficiency too high")

    if Tout_K > T2s + 40:
        st.warning("🔥 High outlet temperature")

    return Power, eta_percent
