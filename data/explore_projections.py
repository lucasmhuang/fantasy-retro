"""Test whether projected scores are available for past weeks."""

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

for week in [1, 10]:
    print("=" * 80)
    print(f"WEEK {week} — PROJECTED vs ACTUAL")
    print("=" * 80)
    box_scores = league.box_scores(week)
    matchup = box_scores[0]

    print(f"Home: {matchup.home_team.team_name}")
    print(f"  Actual score:    {matchup.home_score}")

    if hasattr(matchup, "home_projected"):
        print(f"  Projected score: {matchup.home_projected}")
    else:
        print("  No home_projected attr on matchup")

    print(f"Away: {matchup.away_team.team_name}")
    print(f"  Actual score:    {matchup.away_score}")

    if hasattr(matchup, "away_projected"):
        print(f"  Projected score: {matchup.away_projected}")
    else:
        print("  No away_projected attr on matchup")

    print()
    print("--- First 3 home players: projected fields ---")
    for player in matchup.home_lineup[:3]:
        print(f"  {player.name:<25} actual={player.points:<8}", end="")
        if hasattr(player, "projected_points"):
            print(f"  projected_points={player.projected_points}", end="")
        if hasattr(player, "projected_avg_points"):
            print(f"  projected_avg={player.projected_avg_points}", end="")
        if hasattr(player, "projected_total_points"):
            print(f"  projected_total={player.projected_total_points}", end="")

        proj_stats = {k: v for k, v in (player.stats or {}).items() if k != "0"}
        if proj_stats:
            print(f"\n    Non-actuals stat keys: {list(proj_stats.keys())}")
            for key, val in proj_stats.items():
                print(f"    stats['{key}']: applied_total={val.get('applied_total')}")
        else:
            print(f"\n    Only stats key '0' (actuals)")

        print()
    print()
