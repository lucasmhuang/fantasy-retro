"""Debug: test mRoster API call for full roster including bench."""

import json
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

POSITION_MAP = {
    0: "PG", 1: "SG", 2: "SF", 3: "PF", 4: "C",
    5: "G", 6: "F", 7: "SG/SF", 8: "G/F", 9: "PF/C",
    10: "F/C", 11: "UT", 12: "BE", 13: "IR", 14: "", 15: "Rookie",
}

data = league.espn_request.league_get(params={
    "view": "mRoster",
    "scoringPeriodId": 1,
})

team_data = data["teams"][0]
team_name = next(
    t.team_name for t in league.teams if t.team_id == team_data["id"]
)
print(f"Team: {team_name} (ID: {team_data['id']})")

roster = team_data.get("roster", {})
entries = roster.get("entries", [])
print(f"Roster entries: {len(entries)}\n")

for entry in entries:
    slot_id = entry.get("lineupSlotId", -1)
    slot_name = POSITION_MAP.get(slot_id, f"?{slot_id}")
    player_info = entry.get("playerPoolEntry", {}).get("player", {})
    name = player_info.get("fullName", "???")

    stats = player_info.get("stats", [])
    week1_pts = 0
    for stat_set in stats:
        if stat_set.get("scoringPeriodId") == 1 and stat_set.get("statSourceId") == 0:
            week1_pts = round(stat_set.get("appliedTotal", 0), 1)
            break

    eligible = entry.get("playerPoolEntry", {}).get("player", {}).get("eligibleSlots", [])
    eligible_names = [POSITION_MAP.get(s, f"?{s}") for s in eligible]

    print(
        f"  slotId={slot_id:>2} ({slot_name:<5}) "
        f"{name:<25} pts={week1_pts:<8} "
        f"eligible={eligible_names}"
    )

print("\n--- Slot ID distribution ---")
from collections import Counter
slots = Counter(entry.get("lineupSlotId", -1) for entry in entries)
for slot_id, count in sorted(slots.items()):
    print(f"  {slot_id} ({POSITION_MAP.get(slot_id, '?')}): {count}")
