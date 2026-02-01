import networkx as nx
from graph_coloring.validate import is_valid_coloring

def test_is_valid_coloring_cycle():
    g = nx.cycle_graph(4)
    coloring = {0: 0, 1: 1, 2: 0, 3: 1}
    assert is_valid_coloring(g, coloring) is True

    bad = {0: 0, 1: 0, 2: 0, 3: 0}
    assert is_valid_coloring(g, bad) is False
