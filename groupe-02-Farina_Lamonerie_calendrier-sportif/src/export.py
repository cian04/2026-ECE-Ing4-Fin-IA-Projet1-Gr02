def print_schedule(teams, schedule: dict) -> None:
    days = sorted(schedule.keys())
    for d in days:
        print(f"\nJournée {d+1}")
        for home, away in schedule[d]:
            print(f"  {home} vs {away}")
