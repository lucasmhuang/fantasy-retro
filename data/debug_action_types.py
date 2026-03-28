"""Debug: print all unique action types in activity log."""

import os
from collections import Counter
from dotenv import load_dotenv
from espn_api.basketball import League

load_dotenv()

league = League(
    league_id=int(os.environ["ESPN_LEAGUE_ID"]),
    year=int(os.environ["ESPN_YEAR"]),
    espn_s2=os.environ["ESPN_S2"],
    swid=os.environ["ESPN_SWID"],
)

activities = league.recent_activity(size=500)

types = Counter()
for activity in activities:
    for action in activity.actions:
        if len(action) >= 2:
            types[str(action[1])] += 1

print("Action type counts:")
for t, count in types.most_common():
    print(f"  {t:<30} {count}")

print(f"\nSample of each type:")
seen = set()
for activity in activities:
    for action in activity.actions:
        if len(action) >= 3:
            t = str(action[1])
            if t not in seen:
                seen.add(t)
                team = action[0]
                player = action[2]
                extra = action[3] if len(action) > 3 else ""
                print(f"  {t:<30} team={team.team_name:<25} player={player:<25} extra={extra!r}")
