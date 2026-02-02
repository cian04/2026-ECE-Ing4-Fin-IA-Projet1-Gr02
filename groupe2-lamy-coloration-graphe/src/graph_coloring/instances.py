from __future__ import annotations
import random
import networkx as nx
from pathlib import Path



def cycle_graph(n: int) -> nx.Graph:
    return nx.cycle_graph(n)


def grid_graph(m: int, n: int) -> nx.Graph:
    return nx.grid_2d_graph(m, n)


def erdos_renyi_graph(n: int, p: float, seed: int | None = None) -> nx.Graph:
    return nx.erdos_renyi_graph(n=n, p=p, seed=seed)


def relabel_nodes_to_int(g: nx.Graph) -> nx.Graph:
    return nx.convert_node_labels_to_integers(g, ordering="sorted")


def load_adjacency_list_file(path: str | Path) -> nx.Graph:
   
    path = Path(path)
    raw = path.read_text(encoding="utf-8")

    g = nx.Graph()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        u = int(parts[0])
        g.add_node(u)
        for v_str in parts[1:]:
            v = int(v_str)
            if v != u:
                g.add_edge(u, v)
    return g

