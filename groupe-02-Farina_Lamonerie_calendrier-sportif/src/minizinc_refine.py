import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def _find_minizinc_exe() -> str:
    exe = shutil.which("minizinc")
    if exe:
        return exe

    fallback = r"C:\Users\leofa_ju19mmd\MiniZinc\minizinc.exe"
    if Path(fallback).exists():
        return fallback

    raise FileNotFoundError(
        "MiniZinc executable not found. "
        "Make sure `minizinc --version` works or update the fallback path in _find_minizinc_exe()."
    )


def _extract_json_object(stdout: str) -> dict:
    if not stdout:
        raise ValueError("MiniZinc returned empty stdout.")
    s = stdout.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            "Could not find a JSON object in MiniZinc output.\n"
            f"Raw stdout:\n{s}"
        )
    return json.loads(s[start : end + 1])


def _build_distance_matrix(teams: list[str], inst: dict) -> list[list[int]]:
    """
    Expect inst["distances"] as dict-of-dict:
    {
      "Paris": {"Lyon": 465, "Marseille": 775, ...},
      "Lyon":  {"Paris": 465, ...},
      ...
    }
    Distances can be asymmetric, but we recommend symmetric.
    Missing values -> error (better for correctness).
    """
    distances = inst.get("distances")
    if not isinstance(distances, dict):
        raise ValueError('Instance must include "distances" as dict-of-dict with city names.')

    n = len(teams)
    mat = [[0 for _ in range(n)] for _ in range(n)]

    for i, ci in enumerate(teams):
        if ci not in distances:
            raise ValueError(f'Missing distances row for "{ci}" in inst["distances"].')
        for j, cj in enumerate(teams):
            if i == j:
                mat[i][j] = 0
                continue
            row = distances.get(ci, {})
            if cj not in row:
                raise ValueError(f'Missing distance from "{ci}" to "{cj}" in inst["distances"].')
            mat[i][j] = int(row[cj])

    return mat


def refine_with_minizinc(schedule_base: dict, teams: list[str], inst: dict) -> dict:
    """
    Option A refinement (hard constraints + distance objective):
    - schedule_base: day -> list[(home, away)] from CP-SAT (unoriented pairs, but currently oriented)
    - MiniZinc can flip home/away (orientation) while respecting hard constraints:
        * max_away_streak <= inst["max_away_streak"]
        * max_home_streak <= inst["max_home_streak"]
        * balance abs(home-away) <= 1
        * unavailable_home respected (inst["unavailable_home"])
        * if 2 consecutive away: dist between away locations <= inst["max_consec_away_travel"]
    - Objective: minimize breaks first, then total_distance
    """
    D = len(schedule_base)
    if D == 0:
        return schedule_base

    M = len(schedule_base[0])
    T = len(teams)

    max_away = int(inst.get("max_away_streak", 2))
    max_home = int(inst.get("max_home_streak", 2))
    max_consec_away_travel = int(inst.get("max_consec_away_travel", 10**9))

    if max_away < 0 or max_home < 0:
        raise ValueError("max_away_streak and max_home_streak must be >= 0")

    team_to_id = {t: i + 1 for i, t in enumerate(teams)}

    
    flat_match = []
    for d in range(D):
        if len(schedule_base[d]) != M:
            raise ValueError("Inconsistent number of matches per day in schedule_base.")
        for (h, a) in schedule_base[d]:
            flat_match.append(team_to_id[h])
            flat_match.append(team_to_id[a])

    
    unavailable = [[0 for _ in range(D)] for _ in range(T)]
    unavailable_home = inst.get("unavailable_home", {})
    for team_name, bad_days in unavailable_home.items():
        if team_name not in team_to_id:
            continue
        t_idx = team_to_id[team_name] - 1
        for day_1based in bad_days:
            d_idx = int(day_1based) - 1
            if 0 <= d_idx < D:
                unavailable[t_idx][d_idx] = 1

    flat_unavail = []
    for t in range(T):
        for d in range(D):
            flat_unavail.append(unavailable[t][d])

    
    dist_mat = _build_distance_matrix(teams, inst)
    flat_dist = []
    max_dist = 0
    for i in range(T):
        for j in range(T):
            v = int(dist_mat[i][j])
            max_dist = max(max_dist, v)
            flat_dist.append(v)

    
    big = int(inst.get("big_weight", max_dist * T * (D + 1) + 1))

    dzn_lines = [
        f"D={D};",
        f"T={T};",
        f"M={M};",
        f"MAX_AWAY={max_away};",
        f"MAX_HOME={max_home};",
        f"MAX_CONSEC_AWAY_TRAVEL={max_consec_away_travel};",
        f"BIG={big};",
        f"match = array3d(1..D, 1..M, 1..2, [{', '.join(map(str, flat_match))}]);",
        f"unavailable_home = array2d(1..T, 1..D, [{', '.join(map(str, flat_unavail))}]);",
        f"dist = array2d(1..T, 1..T, [{', '.join(map(str, flat_dist))}]);",
    ]
    dzn_data = "\n".join(dzn_lines)

    model_path = Path("mzn/refine.mzn")
    if not model_path.exists():
        raise FileNotFoundError(f"MiniZinc model not found: {model_path}")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".dzn", delete=False, encoding="utf-8") as f:
        f.write(dzn_data)
        dzn_path = f.name

    minizinc_exe = _find_minizinc_exe()
    result = subprocess.run(
        [minizinc_exe, str(model_path), dzn_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "MiniZinc failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    data = _extract_json_object(result.stdout)

    orient = data.get("orient")
    if orient is None:
        raise RuntimeError(f"MiniZinc JSON missing 'orient'. Parsed: {data}")

    refined = {d: [] for d in range(D)}
    for d in range(D):
        if len(orient[d]) != M:
            raise RuntimeError(f"MiniZinc output orient[{d}] length != M")
        for m in range(M):
            t1 = schedule_base[d][m][0]
            t2 = schedule_base[d][m][1]
            if orient[d][m] == 0:
                refined[d].append((t1, t2))
            else:
                refined[d].append((t2, t1))


    return refined
