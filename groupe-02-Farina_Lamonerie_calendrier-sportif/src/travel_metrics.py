from typing import Dict, List, Tuple, Any


Schedule = Dict[int, List[Tuple[str, str]]]  


def _get_dist(distances: Dict[str, Dict[str, int]], a: str, b: str) -> int:
    if a not in distances or b not in distances[a]:
        raise ValueError(f"Missing distance for '{a}' -> '{b}' in instance distances.")
    return int(distances[a][b])


def compute_travel_metrics(
    teams: List[str],
    schedule: Schedule,
    distances: Dict[str, Dict[str, int]],
    max_consec_away_travel: int,
) -> Dict[str, Any]:
    """
    Computes travel metrics from a schedule:
      - total_distance (sum over teams)
      - distance_per_team
      - consecutive_away_violations (count + details) based on max_consec_away_travel

    Model:
      - Each team "home city" is its team name
      - Day location for team t:
          if t is home => location = t
          else => location = opponent home (the home team name)
      - Travel per team:
          dist(home_city, location_day1) + sum dist(location_{d-1}, location_d)
    """
    D = len(schedule)
    if D == 0:
        return {
            "total_distance": 0,
            "distance_per_team": {t: 0 for t in teams},
            "consec_away_violations_count": 0,
            "consec_away_violations": [],
        }

    
    is_home = {t: [None] * D for t in teams}
    location = {t: [None] * D for t in teams}

    for d in range(D):
        day_matches = schedule[d]
        
        for t in teams:
            is_home[t][d] = 0  
            location[t][d] = None

        for (home, away) in day_matches:
            is_home[home][d] = 1
            location[home][d] = home

            is_home[away][d] = 0
            location[away][d] = home  

        
        for t in teams:
            if location[t][d] is None:
                raise ValueError(f"Team '{t}' has no match/location on day {d+1}.")

   
    distance_per_team = {}
    total_distance = 0

    for t in teams:
        
        dist_sum = _get_dist(distances, t, location[t][0])
       
        for d in range(1, D):
            dist_sum += _get_dist(distances, location[t][d - 1], location[t][d])
        distance_per_team[t] = dist_sum
        total_distance += dist_sum

    
    violations = []
    for t in teams:
        for d in range(1, D):
            if is_home[t][d - 1] == 0 and is_home[t][d] == 0:
                loc_prev = location[t][d - 1]
                loc_cur = location[t][d]
                leg = _get_dist(distances, loc_prev, loc_cur)
                if leg > max_consec_away_travel:
                    violations.append(
                        {
                            "team": t,
                            "day_prev": d,       
                            "day_cur": d + 1,   
                            "from": loc_prev,
                            "to": loc_cur,
                            "distance": leg,
                            "threshold": max_consec_away_travel,
                        }
                    )

    return {
        "total_distance": total_distance,
        "distance_per_team": distance_per_team,
        "consec_away_violations_count": len(violations),
        "consec_away_violations": violations,
    }
