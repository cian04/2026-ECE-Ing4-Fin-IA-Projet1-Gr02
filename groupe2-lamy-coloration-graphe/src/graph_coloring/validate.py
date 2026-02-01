from __future__ import annotations
import networkx as nx


def is_valid_coloring(g: nx.Graph, coloring: dict[int, int]) -> bool:
    for u, v in g.edges():
        if coloring.get(u) == coloring.get(v):
            return False
    return True
