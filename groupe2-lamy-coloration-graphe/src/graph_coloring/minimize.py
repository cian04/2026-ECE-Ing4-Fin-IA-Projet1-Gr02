from __future__ import annotations

import networkx as nx

from .solver_cp_sat import SolveResult, solve_k_coloring_cp_sat


def find_min_k_by_iteration(
    g: nx.Graph,
    k_min: int = 1,
    k_max: int | None = None,
    time_limit_s: float = 10.0,
) -> SolveResult:
    n = g.number_of_nodes()
    if k_max is None:
        k_max = n

    best: SolveResult | None = None
    for k in range(k_min, k_max + 1):
        res = solve_k_coloring_cp_sat(g, k=k, time_limit_s=time_limit_s)
        if res.feasible:
            best = res
            break

    if best is None:
        return SolveResult(feasible=False, coloring={}, k=k_max, wall_time=None)

    return best
