from dataclasses import dataclass
from typing import Any
import networkx as nx
from ortools.sat.python import cp_model


@dataclass
class SolveResult:
    feasible: bool
    coloring: dict[Any, int] 
    k: int
    wall_time: float | None = None


def solve_k_coloring_cp_sat(
    g: nx.Graph,
    k: int,
    time_limit_s: float = 10.0,
    symmetry_breaking: bool = True,
) -> SolveResult:
    

    # Relabel to 0..n-1 but keep mapping
    g_int = nx.convert_node_labels_to_integers(g, ordering="sorted", label_attribute="orig")
    nodes = list(g_int.nodes())

    model = cp_model.CpModel()
    color = {v: model.new_int_var(0, k - 1, f"c_{v}") for v in nodes}

    for u, v in g_int.edges():
        model.add(color[u] != color[v])

    if symmetry_breaking and nodes:
        model.add(color[nodes[0]] == 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = 8

    status = solver.solve(model)
    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    coloring: dict[Any, int] = {}
    if feasible:
        # Map back to original node labels
        for v in nodes:
            orig = g_int.nodes[v]["orig"]
            coloring[orig] = int(solver.value(color[v]))

    return SolveResult(
        feasible=feasible,
        coloring=coloring,
        k=k,
        wall_time=float(solver.wall_time),
    )
