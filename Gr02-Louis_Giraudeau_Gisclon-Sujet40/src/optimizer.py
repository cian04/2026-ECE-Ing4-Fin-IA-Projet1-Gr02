from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ortools.linear_solver import pywraplp


@dataclass
class SectorBounds:
    # group -> (min_weight, max_weight)
    bounds: Dict[str, Tuple[float, float]]


@dataclass
class SolveConfig:
    beta: float = 0.95                 # CVaR confidence level
    lambda_cvar: float = 5.0           # risk aversion (bigger => safer)
    n_max_assets: int = 10             # cardinality
    min_weight_if_selected: float = 0.0
    max_weight_per_asset: float = 0.25
    turnover_max: float = 0.30         # sum(|w - w0|) <= turnover_max
    tc_rate: float = 0.001             # proportional transaction cost on turnover (e.g. 10 bps)
    tc_fixed: float = 0.0              # fixed cost per traded asset (in "weight units" proxy)
    enforce_full_investment: bool = True
    allow_short: bool = False
    time_limit_sec: int = 30
    solver_preference: str = "SCIP"    # "SCIP" or "CBC"


@dataclass
class SolveResult:
    weights: Dict[str, float]
    selected: Dict[str, int]
    cvar: float
    exp_return: float
    turnover: float
    objective: float
    status: str


def _pick_solver(pref: str) -> pywraplp.Solver:
    # Try preference, fallback
    pref = (pref or "").upper().strip()
    candidates = []
    if pref == "SCIP":
        candidates = ["SCIP", "CBC_MIXED_INTEGER_PROGRAMMING"]
    elif pref == "CBC":
        candidates = ["CBC_MIXED_INTEGER_PROGRAMMING", "SCIP"]
    else:
        candidates = ["SCIP", "CBC_MIXED_INTEGER_PROGRAMMING"]

    for name in candidates:
        s = pywraplp.Solver.CreateSolver(name)
        if s is not None:
            return s
    raise RuntimeError("Could not create an OR-Tools MILP solver (SCIP/CBC unavailable).")


def optimize_portfolio_cvar_milp(
    tickers: List[str],
    scenario_returns: pd.DataFrame,     # rows=scenarios/time, cols=tickers
    mu: pd.Series,                      # expected return per ticker (same tickers)
    w0: Optional[Dict[str, float]] = None,
    sector_map: Optional[Dict[str, str]] = None,
    sector_bounds: Optional[SectorBounds] = None,
    config: Optional[SolveConfig] = None,
) -> SolveResult:
    """
    MILP:
    - w_i continuous weights
    - x_i binary selection
    - b_i, s_i >=0 rebalancing (w - w0 = b - s)
    - y_i binary "traded" for fixed cost
    CVaR with historical scenarios (loss = -portfolio_return).
    Objective: maximize E[R] - lambda * CVaR - tc_rate*turnover - tc_fixed*sum(y_i)
    """
    if config is None:
        config = SolveConfig()
    if scenario_returns.empty:
        raise ValueError("scenario_returns is empty")
    if set(scenario_returns.columns) != set(tickers):
        scenario_returns = scenario_returns[tickers]
    mu = mu[tickers]

    K = scenario_returns.shape[0]
    beta = float(config.beta)
    if not (0.0 < beta < 1.0):
        raise ValueError("beta must be in (0,1)")

    # Detect whether an initial weight vector was provided by the caller.
    w0_provided = w0 is not None and any(t in (w0 or {}) for t in tickers)
    w0 = w0 or {}
    w0_vec = np.array([float(w0.get(t, 0.0)) for t in tickers], dtype=float)

    solver = _pick_solver(config.solver_preference)
    solver.SetTimeLimit(int(config.time_limit_sec * 1000))

    # Variables
    w = {t: solver.NumVar(0.0, 1.0, f"w[{t}]") for t in tickers}
    if config.allow_short:
        # If you really want shorts: replace with [-1, 1] and adjust constraints accordingly.
        # For safety, keep default long-only.
        raise NotImplementedError("allow_short not implemented in this template (keep long-only).")

    x = {t: solver.IntVar(0.0, 1.0, f"x[{t}]") for t in tickers}

    b = {t: solver.NumVar(0.0, 1.0, f"buy[{t}]") for t in tickers}
    s = {t: solver.NumVar(0.0, 1.0, f"sell[{t}]") for t in tickers}

    y = {t: solver.IntVar(0.0, 1.0, f"traded[{t}]") for t in tickers}

    # CVaR variables
    z = solver.NumVar(-solver.infinity(), solver.infinity(), "VaR_z")
    xi = [solver.NumVar(0.0, solver.infinity(), f"xi[{k}]") for k in range(K)]

    # Constraints
    # Full investment
    if config.enforce_full_investment:
        solver.Add(sum(w[t] for t in tickers) == 1.0)
    else:
        solver.Add(sum(w[t] for t in tickers) <= 1.0)

    # Cardinality
    solver.Add(sum(x[t] for t in tickers) <= int(config.n_max_assets))

    # Link weights and selection
    for t in tickers:
        solver.Add(w[t] <= config.max_weight_per_asset * x[t])
        if config.min_weight_if_selected > 0:
            solver.Add(w[t] >= config.min_weight_if_selected * x[t])

    # Rebalancing definition: w - w0 = b - s
    for idx, t in enumerate(tickers):
        solver.Add(w[t] - float(w0_vec[idx]) == b[t] - s[t])

    # Turnover constraint: sum(b+s) <= turnover_max
    turnover_expr = sum(b[t] + s[t] for t in tickers)
    # If no initial weights `w0` were provided, skipping the turnover constraint
    # avoids inconsistency with full-investment (sum(w)==1) because b-s = w - w0.
    if w0_provided:
        solver.Add(turnover_expr <= float(config.turnover_max))

    # Fixed cost activation: b+s <= M*y
    M = 1.0  # because weights in [0,1]
    for t in tickers:
        solver.Add(b[t] + s[t] <= M * y[t])

    # Sector constraints (on weights)
    if sector_bounds is not None and sector_map is not None:
        # Build sector -> tickers list
        sector_to_tickers: Dict[str, List[str]] = {}
        for t in tickers:
            sec = sector_map.get(t, "UNKNOWN")
            sector_to_tickers.setdefault(sec, []).append(t)

        for sec, (mn, mx) in sector_bounds.bounds.items():
            members = sector_to_tickers.get(sec, [])
            if not members:
                continue
            solver.Add(sum(w[t] for t in members) >= float(mn))
            solver.Add(sum(w[t] for t in members) <= float(mx))

    # CVaR constraints:
    # loss_k = - sum_i w_i * r_{i,k}
    # xi_k >= loss_k - z, xi_k >=0
    R = scenario_returns.to_numpy(dtype=float)  # shape (K, n)
    for k in range(K):
        port_ret_k = sum(w[tickers[i]] * float(R[k, i]) for i in range(len(tickers)))
        loss_k = -port_ret_k
        solver.Add(xi[k] >= loss_k - z)

    # Define CVaR expression
    cvar_expr = z + (1.0 / ((1.0 - beta) * K)) * sum(xi[k] for k in range(K))

    # Objective components
    exp_return_expr = sum(w[t] * float(mu[t]) for t in tickers)

    tc_expr = float(config.tc_rate) * turnover_expr + float(config.tc_fixed) * sum(y[t] for t in tickers)

    # Maximize: E[R] - lambda * CVaR - TC
    solver.Maximize(exp_return_expr - float(config.lambda_cvar) * cvar_expr - tc_expr)

    status_code = solver.Solve()

    status_map = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
        pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
    }
    status = status_map.get(status_code, str(status_code))

    if status_code not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return SolveResult(
            weights={},
            selected={},
            cvar=float("nan"),
            exp_return=float("nan"),
            turnover=float("nan"),
            objective=float("nan"),
            status=status,
        )

    weights = {t: float(w[t].solution_value()) for t in tickers}
    selected = {t: int(round(x[t].solution_value())) for t in tickers}
    cvar_val = float(cvar_expr.solution_value())
    exp_ret_val = float(exp_return_expr.solution_value())
    turnover_val = float(turnover_expr.solution_value())
    obj_val = float(solver.Objective().Value())

    return SolveResult(
        weights=weights,
        selected=selected,
        cvar=cvar_val,
        exp_return=exp_ret_val,
        turnover=turnover_val,
        objective=obj_val,
        status=status,
    )
