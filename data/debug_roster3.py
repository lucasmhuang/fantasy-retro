"""Debug: find per-week bench player points."""

import json
import os
from pprint import pprint
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

# Check matchup period -> scoring period mapping
print("matchup_periods mapping (first 3):")
mp = league.settings.matchup_periods
for k in sorted(mp.keys())[:3]:
    print(f"  Matchup {k}: scoring periods {mp[k]}")

mp1 = mp.get(1, mp.get("1", [1]))
first_sp = mp1[0]
last_sp = mp1[-1]
print(f"\nMatchup 1 spans scoring periods {first_sp} to {last_sp}")

# Test: rosterForCurrentScoringPeriod — does it include bench?
print("\n" + "=" * 70)
print(f"TEST: rosterForCurrentScoringPeriod (scoringPeriodId={last_sp})")
print("=" * 70)

params = {
    "view": ["mMatchupScore", "mScoreboard"],
    "scoringPeriodId": last_sp,
}
headers = {"x-fantasy-filter": json.dumps({
    "schedule": {"filterMatchupPeriodIds": {"value": [1]}}
})}
raw = league.espn_request.league_get(params=params, headers=headers)

for matchup in raw.get("schedule", []):
    home = matchup.get("home", {})
    if home.get("teamId") != 1:
        continue

    for key in sorted(home.keys()):
        if "roster" in key.lower():
            entries = home.get(key, {}).get("entries", [])
            print(f"\n  {key}: {len(entries)} entries")
            for e in entries[:15]:
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
                print(f"    slotId={slot_id:>2} ({slot:<5}) {name:<25} pts={applied}")

    # Print all keys at the home level
    print(f"\n  All home keys: {list(home.keys())}")
    break
