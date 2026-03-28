"""Debug: test box_scores(matchup_total=False) for bench + correct slots."""

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

print("=== matchup_total=True (current behavior) ===")
box_true = league.box_scores(matchup_period=1, matchup_total=True)
m = box_true[0]
print(f"Matchup: {m.home_team.team_name} vs {m.away_team.team_name}")
print(f"Home lineup size: {len(m.home_lineup)}")
print(f"Home score: {m.home_score}")
for p in m.home_lineup:
    print(f"  {p.name:<25} slot={p.slot_position:<5} pts={p.points}")

print(f"\n=== matchup_total=False (daily, should include bench) ===")
box_false = league.box_scores(matchup_period=1, matchup_total=False)
m2 = box_false[0]
print(f"Matchup: {m2.home_team.team_name} vs {m2.away_team.team_name}")
print(f"Home lineup size: {len(m2.home_lineup)}")
print(f"Home score: {m2.home_score}")
for p in m2.home_lineup:
    print(f"  {p.name:<25} slot={p.slot_position:<5} pts={p.points}")

print(f"\n=== Checking different scoring periods for bench player pts ===")
for sp in [1, 2, 3]:
    box_sp = league.box_scores(matchup_period=1, scoring_period=sp, matchup_total=False)
    m3 = box_sp[0]
    bench = [p for p in m3.home_lineup if p.slot_position in ("BE", "IR")]
    starters = [p for p in m3.home_lineup if p.slot_position not in ("BE", "IR")]
    bench_str = ", ".join(f"{p.name}={p.points}" for p in bench)
    print(f"  SP {sp}: {len(m3.home_lineup)} players, "
          f"{len(starters)} starters, {len(bench)} bench")
    print(f"    Bench: {bench_str}")
    print(f"    Starter slots: {[p.slot_position for p in starters]}")
