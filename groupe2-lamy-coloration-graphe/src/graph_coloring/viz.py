from typing import Any
import math
import networkx as nx
import matplotlib.pyplot as plt


def draw_coloring_main_plus_inset(
    g: nx.Graph,
    coloring: dict[Any, int],
    title: str = "",
    seed: int = 0,
) -> None:
    comps = [g.subgraph(c).copy() for c in nx.connected_components(g)]
    comps.sort(key=lambda sg: sg.number_of_nodes(), reverse=True)

    main = comps[0]
    rest = comps[1:]

    # Centrage du graphe principal
    k_main = 1.2 / math.sqrt(main.number_of_nodes())
    pos_main = nx.spring_layout(main, seed=seed, k=k_main, iterations=1200)

    xs = [p[0] for p in pos_main.values()]
    ys = [p[1] for p in pos_main.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    positions: dict[Any, tuple[float, float]] = dict(pos_main)

    inset_x0 = x_max + 0.45
    inset_y0 = y_max
    col_w = 0.35
    row_h = 0.25

    r = 0
    c = 0
    max_cols = 2

    for sg in rest:
        n = sg.number_of_nodes()
        if n == 1:
            node = next(iter(sg.nodes()))
            local_pos = {node: (0.0, 0.0)}
        else:
            k = 1.0 / math.sqrt(n)
            local_pos = nx.spring_layout(sg, seed=seed, k=k, iterations=600)

        # Normaliser local_pos dans une petite box
        lx = [p[0] for p in local_pos.values()]
        ly = [p[1] for p in local_pos.values()]
        lxmin, lxmax = min(lx), max(lx)
        lymin, lymax = min(ly), max(ly)

        scale_x = (lxmax - lxmin) if (lxmax - lxmin) != 0 else 1.0
        scale_y = (lymax - lymin) if (lymax - lymin) != 0 else 1.0

        # Position dans la grille d'inset
        base_x = inset_x0 + c * col_w
        base_y = inset_y0 - r * row_h

        for node, (x, y) in local_pos.items():
            nx_ = (x - lxmin) / scale_x
            ny_ = (y - lymin) / scale_y
            positions[node] = (base_x + 0.18 * nx_, base_y - 0.18 * ny_)

        c += 1
        if c >= max_cols:
            c = 0
            r += 1

    # Affichage graphe
    node_colors = [coloring.get(n, 0) for n in g.nodes()]

    plt.figure(figsize=(16, 9))
    nx.draw_networkx_edges(g, positions, alpha=0.35, width=1.2)
    nx.draw_networkx_nodes(g, positions, node_color=node_colors, node_size=850)

    nx.draw_networkx_labels(
        g,
        positions,
        font_size=9,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, boxstyle="round,pad=0.15"),
    )

    if title:
        plt.title(title)

    plt.axis("off")
    plt.tight_layout()
    plt.show()