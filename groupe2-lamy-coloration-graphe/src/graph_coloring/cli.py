from __future__ import annotations

import argparse
import networkx as nx


from .instances import (
    cycle_graph,
    erdos_renyi_graph,
    grid_graph,
    relabel_nodes_to_int,
    load_adjacency_list_file,
)
from .minimize import find_min_k_by_iteration
from .solver_cp_sat import solve_k_coloring_cp_sat
from .validate import is_valid_coloring


def build_instance(args: argparse.Namespace) -> nx.Graph:
    if args.instance == "cycle":
        g = cycle_graph(args.n)
        return relabel_nodes_to_int(g)

    elif args.instance == "grid":
        g = grid_graph(args.m, args.n)
        return relabel_nodes_to_int(g)

    elif args.instance == "er":
        g = erdos_renyi_graph(args.n, args.p, seed=args.seed)
        return relabel_nodes_to_int(g)

    elif args.instance == "file":
        if args.path is None:
            raise SystemExit("Error: --path is required when --instance file")
        g = load_adjacency_list_file(args.path)
        return g

    else:
        raise ValueError(f"Unknown instance: {args.instance}")



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="graph_coloring")

    # Instance selection
    parser.add_argument("--instance", choices=["cycle", "grid", "er", "file"], required=True)
    parser.add_argument("--n", type=int, default=10, help="n nodes (cycle/er) or grid n")
    parser.add_argument("--m", type=int, default=5, help="grid m")
    parser.add_argument("--p", type=float, default=0.2, help="Erdos-Renyi probability")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--path", type=str, default=None, help="path to adjacency-list .txt when --instance file")
    parser.add_argument("--plot", action="store_true", help="plot graph with coloring")


    # Solve options
    parser.add_argument("--k", type=int, default=None, help="number of colors (if not minimizing)")
    parser.add_argument("--minimize", action="store_true", help="find minimum number of colors by iterating K")
    parser.add_argument("--k-max", type=int, default=None, help="max K to try when minimizing (default: n)")
    parser.add_argument("--time-limit", type=float, default=10.0)

    args = parser.parse_args(argv)

    g = build_instance(args)

    # Solve
    if args.minimize:
        res = find_min_k_by_iteration(
            g,
            k_min=1,
            k_max=args.k_max,
            time_limit_s=args.time_limit,
        )
    else:
        if args.k is None:
            raise SystemExit("Error: provide --k or use --minimize")
        res = solve_k_coloring_cp_sat(g, k=args.k, time_limit_s=args.time_limit)

    # Print summary
    print(f"Instance: {args.instance} | nodes={g.number_of_nodes()} edges={g.number_of_edges()}")
    print(f"K = {res.k}")
    print(f"K-feasible: {res.feasible}")
    if res.wall_time is not None:
        print(f"Wall time: {res.wall_time:.3f}s")

    if res.feasible:
        used = len(set(res.coloring.values()))
        print(f"Colors used: {used}")
        ok = is_valid_coloring(g, res.coloring)
        print(f"Valid coloring: {ok}")
        items = sorted(res.coloring.items())[: min(20, len(res.coloring))]
        print("Coloring (first nodes):", items)

    if args.plot and res.feasible:
        from .viz import draw_coloring_main_plus_inset
        draw_coloring_main_plus_inset(g, res.coloring, title=f"{args.instance} | k={res.k}")




    return 0



if __name__ == "__main__":
    raise SystemExit(main())
