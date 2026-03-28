"""Debug: test combined mRoster + mMatchupScore for full roster with weekly pts."""

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
    10: "F/C", 11: "UT", 12: "BE", 13: "IR",
}

# Try 1: raw box_scores API call — check if bench players are in rosterForMatchupPeriod
print("=" * 70)
print("TEST 1: Raw box_scores response — does rosterForMatchupPeriod have bench?")
print("=" * 70)

import json as _json
params = {
    "view": ["mMatchupScore", "mScoreboard"],
    "scoringPeriodId": 7,
}
headers = {"x-fantasy-filter": _json.dumps({
    "schedule": {"filterMatchupPeriodIds": {"value": [1]}}
})}
raw = league.espn_request.league_get(params=params, headers=headers)

for matchup in raw.get("schedule", []):
    home = matchup.get("home", {})
    away = matchup.get("away", {})
    home_id = home.get("teamId")
    if home_id != 1:
        continue

    roster = home.get("rosterForMatchupPeriod", {})
    entries = roster.get("entries", [])
    print(f"Team 1 rosterForMatchupPeriod entries: {len(entries)}")
    for e in entries:
        slot_id = e.get("lineupSlotId", -1)
        slot = POSITION_MAP.get(slot_id, f"?{slot_id}")
        player = e.get("playerPoolEntry", {}).get("player", {})
        name = player.get("fullName", "???")
        stats = player.get("stats", [])
        applied = 0
        for s in stats:
            if s.get("statSourceId") == 0:
                applied = round(s.get("appliedTotal", 0), 1)
                break
        print(f"  slotId={slot_id:>2} ({slot:<5}) {name:<25} pts={applied}")
    break

# Try 2: mRoster view with matchup filter — correct slots + weekly pts?
print("\n" + "=" * 70)
print("TEST 2: mRoster with matchup filter")
print("=" * 70)

params2 = {
    "view": ["mRoster", "mMatchupScore"],
    "scoringPeriodId": 7,
}
headers2 = {"x-fantasy-filter": _json.dumps({
    "schedule": {"filterMatchupPeriodIds": {"value": [1]}}
})}
raw2 = league.espn_request.league_get(params=params2, headers=headers2)

team_data = None
for t in raw2.get("teams", []):
    if t["id"] == 1:
        team_data = t
        break

if team_data:
    roster = team_data.get("roster", {})
    entries = roster.get("entries", [])
    print(f"Team 1 roster entries: {len(entries)}")
    for e in entries:
        slot_id = e.get("lineupSlotId", -1)
        slot = POSITION_MAP.get(slot_id, f"?{slot_id}")
        player = e.get("playerPoolEntry", {}).get("player", {})
        name = player.get("fullName", "???")
        stats = player.get("stats", [])
        applied = 0
        for s in stats:
            if s.get("statSourceId") == 0:
                applied = round(s.get("appliedTotal", 0), 1)
                break
        print(f"  slotId={slot_id:>2} ({slot:<5}) {name:<25} pts={applied}")

    # Also check schedule data
    for matchup in raw2.get("schedule", []):
        home = matchup.get("home", {})
        if home.get("teamId") == 1:
            rfmp = home.get("rosterForMatchupPeriod", {})
            entries2 = rfmp.get("entries", [])
            print(f"\n  schedule.home.rosterForMatchupPeriod entries: {len(entries2)}")
            for e in entries2[:3]:
                slot_id = e.get("lineupSlotId", -1)
                slot = POSITION_MAP.get(slot_id, f"?{slot_id}")
                player = e.get("playerPoolEntry", {}).get("player", {})
                name = player.get("fullName", "???")
                print(f"    slotId={slot_id:>2} ({slot:<5}) {name}")
            break
