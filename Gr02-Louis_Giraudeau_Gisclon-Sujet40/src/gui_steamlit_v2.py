import sys
import subprocess
import importlib.util
from pathlib import Path
import tempfile
from typing import Optional
import json
from datetime import datetime, timedelta

def _ensure_requirements(packages, req_name="requirements.txt"):
    missing = [p for p in packages if importlib.util.find_spec(p) is None]
    if not missing:
        return
    p = Path(__file__).resolve().parent
    req_path = None
    for _ in range(6):
        candidate = p / req_name
        if candidate.exists():
            req_path = candidate
            break
        if p.parent == p:
            break
        p = p.parent
    if req_path is None:
        print("Missing packages:", missing)
        raise SystemExit(1)
    print("Missing packages detected:", missing)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])


_ensure_requirements(["streamlit", "pandas", "yfinance", "ortools", "numpy", "scipy"])

import streamlit as st
import pandas as pd

from data_utils import download_market_data, annualize_mean_return, load_sectors_csv, load_current_weights_csv
from optimizer import optimize_portfolio_cvar_milp, SolveConfig, SectorBounds


def save_uploaded_file(uploaded) -> Optional[str]:
    if uploaded is None:
        return None
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tf.write(uploaded.getvalue())
    tf.flush()
    tf.close()
    return tf.name


def build_config_from_inputs(values) -> SolveConfig:
    return SolveConfig(
        beta=float(values["beta"]),
        lambda_cvar=float(values["lambda_cvar"]),
        n_max_assets=int(values["n_max"]),
        min_weight_if_selected=float(values["w_min_if_selected"]),
        max_weight_per_asset=float(values["w_max"]),
        turnover_max=float(values["turnover_max"]),
        tc_rate=float(values["tc_rate"]),
        tc_fixed=float(values["tc_fixed"]),
        solver_preference=values["solver"],
        time_limit_sec=int(values["time_limit_sec"]),
    )


TICKER_PRESETS = {
    "Tech 10": "AAPL,MSFT,NVDA,GOOGL,META,TSLA,AMD,NFLX,CRM,ADBE",
    "Finance 10": "JPM,BAC,WFC,GS,MS,PNC,TD,BLK,BK,SCHW",
    "Healthcare 10": "JNJ,UNH,PFE,ABBV,TMO,MRNA,LLY,CVS,CI,HCA",
    "Energy 10": "XOM,CVX,COP,EOG,MPC,PSX,HES,VLO,SLB,WMB",
    "Dividend 10": "T,O,VICI,PEP,KO,JNJ,IBM,MMM,PG,GIS",
    "S&P 500 (30 leaders)": "AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,BRK.B,JNJ,JPM,V,WMT,PG,MA,COST,UNH,HD,MCD,CRM,PEP,KO,NFLX,BA,MMM,AXP,GS,IBM,CVX,XOM,LMT",
    "Global ETFs": "VTI,VXUS,BND,BNDX,GLD,DBC,REZ,VNQ,VPU",
}


def main():
    st.set_page_config(page_title="Portfolio MILP — Optimizer", layout="wide")
    st.title("📊 Optimisation de Portefeuille (MILP + CVaR)")
    st.markdown("**Interface professionnelle** pour optimisation avec contraintes réelles — décisions basées sur données.")

    # Initialize session state
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "last_df" not in st.session_state:
        st.session_state.last_df = None

    with st.sidebar.form("params"):
        st.markdown("### 📋 Paramètres d'optimisation")

        # Ticker selection with presets
        st.markdown("**1️⃣ Univers d'actifs**")
        preset = st.selectbox(
            "Preset de tickers",
            options=["Custom"] + list(TICKER_PRESETS.keys()),
            index=2
        )
        if preset != "Custom":
            tickers = TICKER_PRESETS[preset]
            st.info(f"✅ Preset sélectionné: {preset}")
        else:
            tickers = st.text_input("Tickers (comma-separated)", value="AAPL,MSFT,AMZN,GOOGL,NVDA")

        # Dates (default: 2 years back to today)
        st.markdown("**2️⃣ Période historique**")
        default_end = datetime.now().date()
        default_start = (datetime.now() - timedelta(days=730)).date()
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start date", value=default_start)
        with col2:
            end = st.date_input("End date", value=default_end)

        # Basic params
        st.markdown("**3️⃣ Configuration CVaR & objectif**")
        col1, col2 = st.columns(2)
        with col1:
            beta = st.number_input("CVaR beta", value=0.95, min_value=0.5, max_value=0.999, step=0.01)
        with col2:
            lambda_cvar = st.number_input("Lambda (risk aversion)", value=5.0, step=0.1, help="Plus grand = plus prudent")

        # Selection & concentration
        st.markdown("**4️⃣ Sélection & concentration**")
        col1, col2 = st.columns(2)
        with col1:
            n_max = st.number_input("Max assets (cardinality)", value=10, min_value=1, help="Nombre d'actifs max")
        with col2:
            w_max = st.number_input("Max weight per asset", value=0.5, min_value=0.0, max_value=1.0, step=0.05, help="Limite par actif")

        # Turnover & costs
        st.markdown("**5️⃣ Rebalancing & coûts**")
        col1, col2 = st.columns(2)
        with col1:
            turnover_max = st.number_input("Max turnover (L1)", value=0.30, min_value=0.0, max_value=1.0, step=0.01)
        with col2:
            tc_rate = st.number_input("Transaction cost (%)", value=0.001, step=0.0001, format="%.4f")

        # Advanced
        with st.expander("⚙️ Options avancées"):
            col1, col2 = st.columns(2)
            with col1:
                w_min_if_selected = st.number_input("Min weight if selected", value=0.0, min_value=0.0, max_value=1.0, step=0.01)
            with col2:
                tc_fixed = st.number_input("Fixed trade cost", value=0.0, step=0.001)

            col1, col2 = st.columns(2)
            with col1:
                solver = st.selectbox("Solver", options=["CBC", "SCIP"], index=0)
            with col2:
                time_limit_sec = st.number_input("Solve time (sec)", value=30, min_value=1)

        # Optional files
        st.markdown("**6️⃣ Contraintes optionnelles**")
        sectors_csv = st.file_uploader("Sectors CSV (ticker,sector,region)", type=["csv"])
        current_weights_csv = st.file_uploader("Current weights CSV (ticker,weight)", type=["csv"])

        run = st.form_submit_button("▶️ Run optimization", use_container_width=True)

    # Action buttons (outside form)
    st.sidebar.markdown("---")
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("📥 CSV Template"):
            template = "ticker,sector,region\nAAPL,Tech,US\nMSFT,Tech,US\nJPM,Finance,US\n"
            st.download_button("sectors_template.csv", template, "sectors_template.csv", "text/csv")
    with col2:
        if st.button("🔄 Reset"):
            st.session_state.clear()
            st.rerun()
    with col3:
        if st.button("❓ Help"):
            st.info("Consultez la fiche technique pour comprendre chaque paramètre.")

    # Fiche technique
    with st.sidebar.expander("📖 Fiche technique"):
        st.markdown("""
        - **Tickers**: Univers d'actifs; change complètement les choix possibles.
        - **Start/End**: Fenêtre historique; plus longue → CVaR plus stable.
        - **CVaR beta**: Confiance (0.5→0.999); proche de 1 → accent sur pertes extrêmes.
        - **Lambda**: Aversion au risque; plus grand → portefeuille plus conservateur.
        - **Max assets**: Cardinalité; restreint diversification.
        - **Max weight**: Concentration max; trop serré → infaisable.
        - **Turnover**: Limite rebalancement; serré → limite changements.
        - **Transaction cost**: Pénalise trading; favorise stabilité.
        - **Solver/Time**: Choix algo + durée; affectent qualité solution.
        """)

    # Main content
    if not run:
        st.info("👈 Remplissez les paramètres à gauche et cliquez **Run optimization**.")
        return

    tickers_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(tickers_list) < 2:
        st.error("❌ Veuillez fournir au moins 2 tickers.")
        return

    sectors_path = save_uploaded_file(sectors_csv)
    weights_path = save_uploaded_file(current_weights_csv)

    values = {
        "beta": beta,
        "lambda_cvar": lambda_cvar,
        "n_max": n_max,
        "w_max": w_max,
        "w_min_if_selected": w_min_if_selected,
        "turnover_max": turnover_max,
        "tc_rate": tc_rate,
        "tc_fixed": tc_fixed,
        "solver": solver,
        "time_limit_sec": time_limit_sec,
    }

    cfg = build_config_from_inputs(values)

    with st.spinner("📥 Downloading market data..."):
        try:
            md = download_market_data(tickers=tickers_list, start=str(start), end=str(end))
        except Exception as e:
            st.error(f"❌ Failed to download: {e}\n\nVérifiez tickers, dates, connexion.")
            return
        scenarios = md.returns.copy()
        mu_annual = annualize_mean_return(md.mu, periods_per_year=252)

    sector_map = None
    region_map = None
    if sectors_path:
        try:
            sector_map, region_map = load_sectors_csv(sectors_path)
        except Exception as e:
            st.warning(f"⚠️ Sectors CSV: {e}")

    w0 = None
    if weights_path:
        try:
            w0 = load_current_weights_csv(weights_path)
        except Exception as e:
            st.warning(f"⚠️ Weights CSV: {e}")

    sector_bounds = None

    with st.spinner("⚙️ Solving MILP..."):
        try:
            res = optimize_portfolio_cvar_milp(
                tickers=tickers_list,
                scenario_returns=scenarios,
                mu=mu_annual,
                w0=w0,
                sector_map=sector_map,
                sector_bounds=sector_bounds,
                config=cfg,
            )
        except Exception as e:
            st.error(f"❌ Optimization error: {e}")
            return

    st.session_state.last_result = res
    st.session_state.last_df = None

    # Display results
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Status")
        if res.status == "OPTIMAL":
            st.success(f"✅ {res.status}")
        else:
            st.warning(f"⚠️ {res.status}")

    with col2:
        if not res.weights:
            st.error("❌ No solution found. Try relaxing constraints.")
            return

    df = pd.DataFrame({
        "ticker": tickers_list,
        "weight (%)": [res.weights.get(t, 0.0) * 100 for t in tickers_list],
        "selected": [res.selected.get(t, 0) for t in tickers_list],
    })
    df = df[df["weight (%)"] > 0.01].sort_values("weight (%)", ascending=False).reset_index(drop=True)
    st.session_state.last_df = df

    st.subheader("📈 Portfolio")
    st.dataframe(df, use_container_width=True)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Expected return (annual)", f"{res.exp_return:.2%}")
    with col2:
        st.metric("CVaR", f"{res.cvar:.4f}")
    with col3:
        st.metric("Turnover", f"{res.turnover:.4f}")
    with col4:
        st.metric("Objective", f"{res.objective:.4f}")

    # Export options
    st.markdown("---")
    st.subheader("💾 Export & Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Weights CSV", csv_data, "weights.csv", "text/csv")

    with col2:
        json_data = {
            "status": res.status,
            "portfolio": df.to_dict(orient="records"),
            "metrics": {
                "expected_return": float(res.exp_return),
                "cvar": float(res.cvar),
                "turnover": float(res.turnover),
                "objective": float(res.objective),
            },
            "parameters": values,
        }
        st.download_button("📋 Results JSON", json.dumps(json_data, indent=2), "results.json", "application/json")

    with col3:
        st.info("✅ Export successful. Use CSV for trading, JSON for archival.")


if __name__ == "__main__":
    main()
