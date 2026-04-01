import time
from datetime import datetime, timedelta, timezone

from constants import MATCHUP_DATES


def _retry(fn):
    for attempt in range(2):
        try:
            return fn()
        except Exception:
            if attempt == 0:
                time.sleep(1)
            else:
                raise


def get_manager_name(team):
    owners = getattr(team, "owners", None) or []
    if isinstance(owners, list) and owners:
        owner = owners[0]
        first = owner.get("firstName", "").strip()
        last = owner.get("lastName", "").strip()
        name = f"{first} {last}".strip()
        if name:
            return name
    return "Unknown"


def date_to_week(epoch_ms):
    if not epoch_ms:
        return None
    try:
        dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
        for week_num, (start, end) in enumerate(MATCHUP_DATES, 1):
            if start <= dt <= end + timedelta(days=1):
                return week_num
        return None
    except (ValueError, OSError):
        return None


def find_team_in_matchup(box, team_id):
    if box.home_team and box.home_team.team_id == team_id:
        return box.home_lineup, box.home_score, box.away_team, box.away_score
    if box.away_team and box.away_team.team_id == team_id:
        return box.away_lineup, box.away_score, box.home_team, box.home_score
    return None, None, None, None
