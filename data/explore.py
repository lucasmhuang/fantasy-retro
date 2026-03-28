"""Explore ESPN Fantasy Basketball API data structures.

Prints raw data from the espn-api library so we can see exact field names,
shapes, and available attributes before building the extraction pipeline.
"""

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

# ---------------------------------------------------------------------------
# 1. Basic league info
# ---------------------------------------------------------------------------
print("=" * 80)
print("LEAGUE INFO")
print("=" * 80)
print(f"Name:            {league.settings.name}")
print(f"Year:            {league.year}")
print(f"Num teams:       {len(league.teams)}")
print(f"Scoring type:    {league.settings.scoring_type}")
print(f"Reg season len:  {league.settings.reg_season_count}")
print(f"Playoff teams:   {league.settings.playoff_team_count}")
print()
print("Settings attributes:")
pprint(dir(league.settings))
print()

# ---------------------------------------------------------------------------
# 2. Teams
# ---------------------------------------------------------------------------
print("=" * 80)
print("TEAMS")
print("=" * 80)
for team in league.teams:
    print(
        f"  {team.team_id:>2}. {team.team_name:<30} "
        f"Owner: {team.owners}  "
        f"W-L: {team.wins}-{team.losses}  "
        f"Standing: {team.standing}"
    )
print()
print("First team attributes:")
pprint(dir(league.teams[0]))
print()

# ---------------------------------------------------------------------------
# 3. Scoring settings (custom point values per stat)
# ---------------------------------------------------------------------------
print("=" * 80)
print("SCORING SETTINGS")
print("=" * 80)
if hasattr(league.settings, "scoring_settings"):
    pprint(league.settings.scoring_settings)
else:
    print("No scoring_settings attribute found on league.settings")
    print("Checking for scoring-related attrs...")
    for attr in dir(league.settings):
        if "scor" in attr.lower():
            print(f"  {attr} = {getattr(league.settings, attr, 'N/A')}")
print()

# ---------------------------------------------------------------------------
# 4. Box scores for week 1 — full detail on one matchup
# ---------------------------------------------------------------------------
print("=" * 80)
print("BOX SCORES — WEEK 1")
print("=" * 80)
box_scores = league.box_scores(1)
print(f"Number of matchups: {len(box_scores)}")
print()

matchup = box_scores[0]
print(f"Home: {matchup.home_team.team_name}  Score: {matchup.home_score}")
print(f"Away: {matchup.away_team.team_name}  Score: {matchup.away_score}")
print()
print("Matchup attributes:")
pprint(dir(matchup))
print()

print("--- Home lineup (first 2 players) ---")
for player in matchup.home_lineup[:2]:
    print(f"  Name:           {player.name}")
    print(f"  Points:         {player.points}")
    print(f"  Slot position:  {player.slot_position}")
    print(f"  Position:       {player.position}")
    print(f"  Pro team:       {player.proTeam}")
    print()
    print("  points_breakdown:")
    pprint(player.points_breakdown, indent=4)
    print()
    print("  Player stats (raw):")
    if hasattr(player, "stats"):
        pprint(player.stats, indent=4)
    print()
    print("  All player attributes:")
    pprint(dir(player))
    print()
    print("  -" * 30)

# ---------------------------------------------------------------------------
# 5. Recent activity
# ---------------------------------------------------------------------------
print("=" * 80)
print("RECENT ACTIVITY (5 items)")
print("=" * 80)
activities = league.recent_activity(size=5)
for i, activity in enumerate(activities):
    print(f"\nActivity {i + 1}:")
    print(f"  Date:    {activity.date}")
    print(f"  Actions: {activity.actions}")
    for action in activity.actions:
        print(f"    Raw action ({len(action)} elements): {action}")
    if i == 0:
        print()
        print("  First activity attributes:")
        pprint(dir(activity))
print()

# ---------------------------------------------------------------------------
# 6. Team schedule (first 3 entries for first team)
# ---------------------------------------------------------------------------
print("=" * 80)
print("TEAM SCHEDULE (first team, first 3 matchups)")
print("=" * 80)
team = league.teams[0]
print(f"Team: {team.team_name}")
print(f"Schedule length: {len(team.schedule)}")
print()
for i, matchup in enumerate(team.schedule[:3]):
    print(f"  Matchup {i + 1}:")
    pprint(vars(matchup) if hasattr(matchup, "__dict__") else matchup, indent=4)
    print(f"  Attributes: {dir(matchup)}")
    print()

# ---------------------------------------------------------------------------
# 7. Draft (first 5 picks)
# ---------------------------------------------------------------------------
print("=" * 80)
print("DRAFT (first 5 picks)")
print("=" * 80)
draft = league.draft
for pick in draft[:5]:
    print(
        f"  Round {pick.round_num}, Pick {pick.round_pick}: "
        f"{pick.playerName:<25} -> {pick.team.team_name}"
    )
print()
print("First pick attributes:")
pprint(dir(draft[0]))
print()
print("First pick vars:")
pprint(vars(draft[0]) if hasattr(draft[0], "__dict__") else "no __dict__")
