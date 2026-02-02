from ortools.sat.python import cp_model


def solve_with_cpsat(inst: dict, time_limit_s: int = 10) -> dict:
    teams = inst["teams"]
    n = len(teams)
    days = inst["days"]

    if n % 2 != 0:
        raise ValueError("MVP: gère seulement un nombre pair d'équipes pour l'instant.")
    if days != n - 1:
        raise ValueError(f"MVP: pour n={n}, days devrait être {n-1} (aller simple).")

    
    unavailable_home = inst.get("unavailable_home", {})

    model = cp_model.CpModel()

   
    x = {}
    for d in range(days):
        for h in range(n):
            for a in range(n):
                if h == a:
                    continue
                x[(d, h, a)] = model.NewBoolVar(f"x_d{d}_h{h}_a{a}")

    
    for i in range(n):
        for j in range(i + 1, n):
            model.Add(
                sum(x[(d, i, j)] for d in range(days))
                + sum(x[(d, j, i)] for d in range(days))
                == 1
            )

    
    for d in range(days):
        for t in range(n):
            home_matches = sum(x[(d, t, o)] for o in range(n) if o != t)
            away_matches = sum(x[(d, o, t)] for o in range(n) if o != t)
            model.Add(home_matches + away_matches == 1)

    
    for team_name, bad_days in unavailable_home.items():
        if team_name not in teams:
            continue
        t = teams.index(team_name)
        for day_1based in bad_days:
            d = day_1based - 1
            if 0 <= d < days:
                model.Add(sum(x[(d, t, o)] for o in range(n) if o != t) == 0)

  
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("Aucune solution trouvée (contraintes trop fortes ?)")

    
    schedule = {d: [] for d in range(days)}
    for d in range(days):
        for h in range(n):
            for a in range(n):
                if h == a:
                    continue
                if solver.Value(x[(d, h, a)]) == 1:
                    schedule[d].append((teams[h], teams[a]))

    return schedule
