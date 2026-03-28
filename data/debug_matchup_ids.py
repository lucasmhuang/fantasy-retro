import os
from dotenv import load_dotenv
from espn_api.basketball import League
load_dotenv()
league = League(league_id=int(os.environ["ESPN_LEAGUE_ID"]), year=int(os.environ["ESPN_YEAR"]), espn_s2=os.environ["ESPN_S2"], swid=os.environ["ESPN_SWID"])
print("matchup_ids:", dict(sorted(league.matchup_ids.items())))
print("current_week:", league.current_week)
