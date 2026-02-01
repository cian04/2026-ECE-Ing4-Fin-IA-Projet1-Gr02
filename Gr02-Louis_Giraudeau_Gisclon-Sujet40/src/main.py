from __future__ import annotations

import sys
import subprocess
import importlib.util
from pathlib import Path

def _ensure_requirements(packages, req_name="requirements.txt"):
    missing = [p for p in packages if importlib.util.find_spec(p) is None]
    if not missing:
        return
    # Search for requirements.txt upwards from this file
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
        print("requirements.txt not found; install missing packages manually.")
        raise SystemExit(1)
    print("Missing packages detected:", missing)
    print(f"Installing from {req_path} (this may take a while)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])


_ensure_requirements(["pandas", "yfinance", "ortools", "numpy", "scipy"])

import argparse
import pandas as pd

from data_utils import (
    download_market_data,
    load_sectors_csv,
    load_current_weights_csv,
    annualize_mean_return,
)
from optimizer import (
    optimize_portfolio_cvar_milp,
    SolveConfig,
    SectorBounds,
)


def parse_args():
    p = argparse.ArgumentParser(description="MILP Portfolio Optimization with CVaR + real constraints")
    p.add_argument("--tickers", type=str, default="AAPL,MSFT,AMZN", help='Comma list: "AAPL,MSFT,AMZN,..." (default preset)')
    p.add_argument("--start", type=str, default="2020-01-01")
    p.add_argument("--end", type=str, default=None)
    p.add_argument("--beta", type=float, default=0.95)
    p.add_argument("--lambda_cvar", type=float, default=5.0)
    p.add_argument("--n_max", type=int, default=10)
    p.add_argument("--w_max", type=float, default=1.0)
    p.add_argument("--w_min_if_selected", type=float, default=0.0)
    p.add_argument("--turnover_max", type=float, default=0.30)
    p.add_argument("--tc_rate", type=float, default=0.001)
    p.add_argument("--tc_fixed", type=float, default=0.0)
    p.add_argument("--solver", type=str, default="SCIP", choices=["SCIP", "CBC"])
    p.add_argument("--time_limit", type=int, default=30)

    p.add_argument("--sectors_csv", type=str, default=None, help="CSV: ticker,sector,region")
    p.add_argument("--current_weights_csv", type=str, default=None, help="CSV: ticker,weight")

    # Optional: simple sector bounds input example:
    # --sector_bound "Technology:0.05:0.40" --sector_bound "Financial:0.00:0.30"
    p.add_argument("--sector_bound", action="append", default=[], help='Format "Sector:min:max"')

    return p.parse_args()


def main():
    args = parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if len(tickers) < 2:
        raise ValueError("Provide at least 2 tickers")

    md = download_market_data(tickers=tickers, start=args.start, end=args.end)
    # Use daily scenarios for CVaR (could also sample/aggregate weekly)
    scenarios = md.returns.copy()

    # Expected return: annualize for easier interpretation (optional)
    mu_annual = annualize_mean_return(md.mu, periods_per_year=252)

    sector_map = None
    region_map = None
    if args.sectors_csv:
        sector_map, region_map = load_sectors_csv(args.sectors_csv)

    w0 = None
    if args.current_weights_csv:
        w0 = load_current_weights_csv(args.current_weights_csv)

    sector_bounds = None
    if args.sector_bound:
        bounds = {}
        for sb in args.sector_bound:
            # "Sector:min:max"
            parts = sb.split(":")
            if len(parts) != 3:
                raise ValueError(f"Bad --sector_bound '{sb}'. Expected 'Sector:min:max'")
            sec = parts[0].strip()
            mn = float(parts[1])
            mx = float(parts[2])
            bounds[sec] = (mn, mx)
        sector_bounds = SectorBounds(bounds=bounds)

    cfg = SolveConfig(
        beta=args.beta,
        lambda_cvar=args.lambda_cvar,
        n_max_assets=args.n_max,
        min_weight_if_selected=args.w_min_if_selected,
        max_weight_per_asset=args.w_max,
        turnover_max=args.turnover_max,
        tc_rate=args.tc_rate,
        tc_fixed=args.tc_fixed,
        solver_preference=args.solver,
        time_limit_sec=args.time_limit,
    )

    res = optimize_portfolio_cvar_milp(
        tickers=tickers,
        scenario_returns=scenarios,
        mu=mu_annual,
        w0=w0,
        sector_map=sector_map,
        sector_bounds=sector_bounds,
        config=cfg,
    )

    print("\n=== SOLVE STATUS ===")
    print(res.status)
    if not res.weights:
        print("No solution.")
        return

    df = pd.DataFrame(
        {
            "ticker": tickers,
            "weight": [res.weights[t] for t in tickers],
            "selected": [res.selected[t] for t in tickers],
        }
    )
    df = df[df["weight"] > 1e-6].sort_values("weight", ascending=False)

    print("\n=== PORTFOLIO ===")
    print(df.to_string(index=False))

    print("\n=== METRICS (based on model) ===")
    print(f"Expected return (annual, model mu): {res.exp_return:.6f}")
    print(f"CVaR@{args.beta:.2f}: {res.cvar:.6f}")
    print(f"Turnover (L1, weights): {res.turnover:.6f}")
    print(f"Objective value: {res.objective:.6f}")


if __name__ == "__main__":
    main()
