import argparse
import json
from pathlib import Path

from src.cpsat_solver import solve_with_cpsat
from src.export import print_schedule
from src.validate import validate_schedule, compute_metrics
from src.minizinc_refine import refine_with_minizinc
from src.travel_metrics import compute_travel_metrics


def load_instance(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def print_metrics(metrics: dict) -> None:
    print("\n--- METRICS ---")
    print("Total breaks:", metrics["total_breaks"])
    print("Breaks per team:", metrics["breaks_per_team"])
    print("Max away streak:", metrics["max_away_streak"])
    print("Home-Away balance:", metrics["balance"])


def print_travel(label: str, travel: dict) -> None:
    print(f"\n--- TRAVEL ({label}) ---")
    print("Total distance:", travel["total_distance"])
    print("Distance per team:", travel["distance_per_team"])
    print("Consecutive-away violations:", travel["consec_away_violations_count"])
    if travel["consec_away_violations_count"] > 0:
        print("Details:")
        for v in travel["consec_away_violations"][:10]:
            print(
                f"  Team {v['team']} away on days {v['day_prev']}->{v['day_cur']}: "
                f"{v['from']} -> {v['to']} = {v['distance']} (limit {v['threshold']})"
            )


def main():
    parser = argparse.ArgumentParser(description="Sports Tournament Scheduling (CP-SAT + MiniZinc refine)")
    parser.add_argument("--instance", default="data/example_6teams.json", help="Path to instance JSON")
    parser.add_argument("--time-limit", type=int, default=10, help="CP-SAT time limit (seconds)")
    parser.add_argument("--no-minizinc", action="store_true", help="Skip MiniZinc refinement step")
    args = parser.parse_args()

    inst = load_instance(args.instance)
    teams = inst["teams"]

    # 1) CP-SAT base schedule
    schedule_base = solve_with_cpsat(inst, time_limit_s=args.time_limit)

    print("\n========================")
    print("CP-SAT schedule (BASE)")
    print("========================")
    print_schedule(teams, schedule_base)

    validate_schedule(
        teams=teams,
        schedule=schedule_base,
        unavailable_home=inst.get("unavailable_home", {}),
    )
    print("\n✅ Validation OK (BASE)")
    metrics_base = compute_metrics(teams, schedule_base)
    print_metrics(metrics_base)

    # Travel metrics (if distances provided)
    if "distances" in inst:
        travel_base = compute_travel_metrics(
            teams=teams,
            schedule=schedule_base,
            distances=inst["distances"],
            max_consec_away_travel=int(inst.get("max_consec_away_travel", 10**9)),
        )
        print_travel("BASE", travel_base)

    if args.no_minizinc:
        print("\n(MiniZinc skipped)")
        return

    # 2) MiniZinc refine
    print("\n========================")
    print("MiniZinc refine")
    print("========================")

    try:
        refined = refine_with_minizinc(schedule_base, teams, inst)

        print("\n========================")
        print("Refined schedule (MiniZinc)")
        print("========================")
        print_schedule(teams, refined)

        validate_schedule(
            teams=teams,
            schedule=refined,
            unavailable_home=inst.get("unavailable_home", {}),
        )
        print("\n✅ Validation OK (REFINED)")
        metrics_refined = compute_metrics(teams, refined)
        print_metrics(metrics_refined)

        if "distances" in inst:
            travel_refined = compute_travel_metrics(
                teams=teams,
                schedule=refined,
                distances=inst["distances"],
                max_consec_away_travel=int(inst.get("max_consec_away_travel", 10**9)),
            )
            print_travel("REFINED", travel_refined)

            print("\n--- IMPROVEMENT ---")
            print("Breaks:", metrics_base["total_breaks"], "->", metrics_refined["total_breaks"])
            print("Total distance:", travel_base["total_distance"], "->", travel_refined["total_distance"])
        else:
            print("\n--- IMPROVEMENT ---")
            print("Breaks:", metrics_base["total_breaks"], "->", metrics_refined["total_breaks"])

    except Exception as e:
        print("\n❌ MiniZinc refinement failed:", str(e))


if __name__ == "__main__":
    main()
