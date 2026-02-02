from collections import defaultdict


def validate_schedule(teams, schedule, unavailable_home=None):
    """
    Vérifie les contraintes de base:
    - 1 match par équipe et par journée
    - aucune rencontre dupliquée
    - respecte unavailable_home (jours 1..days)
    """
    unavailable_home = unavailable_home or {}

    team_set = set(teams)
    days = sorted(schedule.keys())

    
    for d in days:
        played = defaultdict(int)
        for h, a in schedule[d]:
            if h not in team_set or a not in team_set or h == a:
                raise ValueError(f"Jour {d+1}: match invalide ({h} vs {a})")

            played[h] += 1
            played[a] += 1

        for t in teams:
            if played[t] != 1:
                raise ValueError(f"Jour {d+1}: {t} joue {played[t]} match(s) (attendu 1)")

    
    seen_pairs = set()
    for d in days:
        for h, a in schedule[d]:
            pair = tuple(sorted([h, a]))
            if pair in seen_pairs:
                raise ValueError(f"Rencontre dupliquée détectée: {pair}")
            seen_pairs.add(pair)

    
    for team_name, bad_days in unavailable_home.items():
        if team_name not in team_set:
            continue
        for day_1based in bad_days:
            d = day_1based - 1
            if d in schedule:
                for h, _a in schedule[d]:
                    if h == team_name:
                        raise ValueError(
                            f"Indispo domicile violée: {team_name} est à domicile jour {day_1based}"
                        )

    return True


def compute_metrics(teams, schedule):
    """
    Calcule des métriques pour comparer des calendriers:
    - breaks (H-H ou A-A consécutifs)
    - max_away_streak
    - balance home-away (home_count - away_count)
    """
    days = sorted(schedule.keys())

    
    home = {t: {d: 0 for d in days} for t in teams}

    for d in days:
        for h, a in schedule[d]:
            home[h][d] = 1
            home[a][d] = 0

    
    breaks_per_team = {t: 0 for t in teams}
    for t in teams:
        for idx in range(1, len(days)):
            d_prev = days[idx - 1]
            d_cur = days[idx]
            if home[t][d_cur] == home[t][d_prev]:
                breaks_per_team[t] += 1

    total_breaks = sum(breaks_per_team.values())

    
    max_away_streak = {t: 0 for t in teams}
    for t in teams:
        cur = 0
        for d in days:
            if home[t][d] == 0: 
                cur += 1
                max_away_streak[t] = max(max_away_streak[t], cur)
            else:
                cur = 0

    
    balance = {}
    for t in teams:
        home_count = sum(home[t][d] for d in days)
        away_count = len(days) - home_count
        balance[t] = home_count - away_count

    return {
        "total_breaks": total_breaks,
        "breaks_per_team": breaks_per_team,
        "max_away_streak": max_away_streak,
        "balance": balance,
    }
