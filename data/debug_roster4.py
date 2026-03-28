"""Debug: check pointsByScoringPeriod and find bench player weekly pts."""

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

params = {
    "view": ["mMatchupScore", "mScoreboard"],
    "scoringPeriodId": 1,
}
headers = {"x-fantasy-filter": json.dumps({
    "schedule": {"filterMatchupPeriodIds": {"value": [1]}}
})}
raw = league.espn_request.league_get(params=params, headers=headers)

for matchup in raw.get("schedule", []):
    home = matchup.get("home", {})
    if home.get("teamId") != 1:
        continue

    print("pointsByScoringPeriod:")
    pbsp = home.get("pointsByScoringPeriod", {})
    for sp_id, pts in sorted(pbsp.items(), key=lambda x: int(x[0])):
        print(f"  SP {sp_id}: {pts}")
    print(f"  Total from PBSP: {sum(pbsp.values()):.1f}")
    print(f"  totalPoints: {home.get('totalPoints')}")

    # Check rosterForCurrentScoringPeriod stats more carefully
    print("\nBench player stats detail (rosterForCurrentScoringPeriod):")
    rfcsp = home.get("rosterForCurrentScoringPeriod", {})
    for e in rfcsp.get("entries", []):
        slot_id = e.get("lineupSlotId", -1)
        if slot_id != 12:
            continue
        player = e.get("playerPoolEntry", {}).get("player", {})
        name = player.get("fullName", "???")
        print(f"\n  {name} (bench):")
        for s in player.get("stats", []):
            print(f"    statSourceId={s.get('statSourceId')} "
                  f"splitTypeId={s.get('statSplitTypeId')} "
                  f"scoringPeriodId={s.get('scoringPeriodId')} "
                  f"appliedTotal={s.get('appliedTotal', 0):.1f} "
                  f"id={s.get('id')}")
    break

# Now test: can we get per-scoring-period roster? Check SP 2
print("\n" + "=" * 70)
print("Checking rosterForCurrentScoringPeriod with scoringPeriodId=2,3,4")
print("=" * 70)

for sp in [2, 3, 4]:
    params2 = {
        "view": ["mMatchupScore", "mScoreboard"],
        "scoringPeriodId": sp,
    }
    headers2 = {"x-fantasy-filter": json.dumps({
        "schedule": {"filterMatchupPeriodIds": {"value": [1]}}
    })}
    raw2 = league.espn_request.league_get(params=params2, headers=headers2)

    for matchup in raw2.get("schedule", []):
        home = matchup.get("home", {})
        if home.get("teamId") != 1:
            continue
        rfcsp = home.get("rosterForCurrentScoringPeriod", {})
        entries = rfcsp.get("entries", [])
        bench_pts = []
        for e in entries:
            if e.get("lineupSlotId") == 12:
                player = e.get("playerPoolEntry", {}).get("player", {})
                name = player.get("fullName", "???")
                stats = player.get("stats", [])
                applied = 0
                for s in stats:
                    if s.get("statSourceId") == 0:
                        applied = round(s.get("appliedTotal", 0), 1)
                        break
                bench_pts.append(f"{name}={applied}")
        print(f"  SP {sp}: {len(entries)} entries, bench: {bench_pts}")
        break
