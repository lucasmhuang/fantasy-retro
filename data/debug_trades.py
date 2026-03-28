"""Debug: print raw trade activity to understand direction."""

import os
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

print("All trade activities (showing team / action / player):\n")
for activity in activities:
    trade_actions = [a for a in activity.actions if len(a) >= 3 and "TRADED" in str(a[1])]
    if not trade_actions:
        continue
    print(f"Activity date: {activity.date}")
    for action in trade_actions:
        print(f"  {action[0].team_name:<30} {action[1]:<15} {action[2]}")
    print()
