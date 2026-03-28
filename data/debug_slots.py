"""Debug: check what slot_position values the API actually returns."""

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

box = league.box_scores(1)[0]
print(f"Matchup: {box.home_team.team_name} vs {box.away_team.team_name}\n")

for player in box.home_lineup:
    print(
        f"  {player.name:<25} "
        f"slot_position={player.slot_position!r:<10} "
        f"lineupSlot={player.lineupSlot!r:<10} "
        f"position={player.position!r:<8} "
        f"eligibleSlots={player.eligibleSlots!r}"
    )

print("\n--- Slot position value counts (all 6 matchups) ---")
slots = Counter()
for box in league.box_scores(1):
    for player in box.home_lineup + box.away_lineup:
        slots[player.slot_position] += 1
for slot, count in slots.most_common():
    print(f"  {slot!r}: {count}")
