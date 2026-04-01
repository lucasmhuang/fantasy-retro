import json

from constants import CACHE_DIR
from models import CachedLeague, MatchupData, PlayerData, TeamRef


def _serialize_player(p):
    return {
        "name": p.name,
        "points": p.points,
        "pointsBreakdown": p.points_breakdown or {},
        "slot": p.slot_position,
        "position": p.position,
        "eligibleSlots": p.eligibleSlots,
    }


def _deserialize_player(d):
    return PlayerData(
        name=d["name"],
        points=d["points"],
        points_breakdown=d.get("pointsBreakdown", {}),
        slot_position=d["slot"],
        position=d.get("position", ""),
        eligible_slot_ids=d.get("eligibleSlots", []),
    )


def _serialize_matchup(m):
    return {
        "homeTeam": {"id": m.home_team.team_id, "name": m.home_team.team_name},
        "awayTeam": {"id": m.away_team.team_id, "name": m.away_team.team_name},
        "homeScore": m.home_score,
        "awayScore": m.away_score,
        "homeLineup": [_serialize_player(p) for p in (m.home_lineup or [])],
        "awayLineup": [_serialize_player(p) for p in (m.away_lineup or [])],
    }


def _deserialize_matchup(d):
    return MatchupData(
        home_team=TeamRef(d["homeTeam"]["id"], d["homeTeam"]["name"]),
        away_team=TeamRef(d["awayTeam"]["id"], d["awayTeam"]["name"]),
        home_score=d["homeScore"],
        away_score=d["awayScore"],
        home_lineup=[_deserialize_player(p) for p in d.get("homeLineup", [])],
        away_lineup=[_deserialize_player(p) for p in d.get("awayLineup", [])],
    )


def save_cache(box_cache, roster_by_week, activity, league, roster_totals=None, faab=None):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    serialized_box = {str(week): [_serialize_matchup(m) for m in matchups] for week, matchups in box_cache.items()}
    with open(CACHE_DIR / "box_cache.json", "w") as f:
        json.dump(serialized_box, f)

    serialized_rbw = {
        str(week): {
            str(tid): {
                name: {
                    "slot": data["slot"],
                    "position": data.get("position", ""),
                    "eligible": data.get("eligible", []),
                    "daily_pts": data["daily_pts"],
                }
                for name, data in players.items()
            }
            for tid, players in teams.items()
        }
        for week, teams in roster_by_week.items()
    }
    with open(CACHE_DIR / "roster_by_week.json", "w") as f:
        json.dump(serialized_rbw, f)

    with open(CACHE_DIR / "activity.json", "w") as f:
        json.dump(activity, f)

    league_info = {
        "name": league.settings.name,
        "scoringType": league.settings.scoring_type,
        "regSeasonWeeks": league.settings.reg_season_count or 18,
        "totalWeeks": len(league.teams[0].schedule),
        "scoringSettings": league.settings._raw_scoring_settings.get("scoringItems", []),
        "teams": [
            {
                "id": t.team_id,
                "name": t.team_name,
                "owners": getattr(t, "owners", []),
                "wins": t.wins,
                "losses": t.losses,
                "standing": t.standing,
                "pointsFor": t.points_for,
                "pointsAgainst": t.points_against,
                "schedule": len(t.schedule),
            }
            for t in league.teams
        ],
        "draft": [
            {
                "round": p.round_num,
                "pick": p.round_pick,
                "playerName": p.playerName,
                "teamId": p.team.team_id,
                "teamName": p.team.team_name,
            }
            for p in league.draft
        ],
    }
    with open(CACHE_DIR / "league_info.json", "w") as f:
        json.dump(league_info, f)

    if roster_totals is not None:
        with open(CACHE_DIR / "roster_totals.json", "w") as f:
            json.dump(roster_totals, f)

    if faab is not None:
        serialized_faab = {f"{name}|{tid}|{week}": bid for (name, tid, week), bid in faab.items()}
        with open(CACHE_DIR / "faab.json", "w") as f:
            json.dump(serialized_faab, f)

    print(f"  Cache saved to {CACHE_DIR}/")


def load_cache():
    with open(CACHE_DIR / "box_cache.json") as f:
        raw_box = json.load(f)
    box_cache = {int(week): [_deserialize_matchup(m) for m in matchups] for week, matchups in raw_box.items()}

    with open(CACHE_DIR / "roster_by_week.json") as f:
        raw_rbw = json.load(f)
    roster_by_week = {
        int(week): {int(tid): players for tid, players in teams.items()} for week, teams in raw_rbw.items()
    }

    with open(CACHE_DIR / "activity.json") as f:
        raw_activity = json.load(f)
    activity = {
        "trades": raw_activity.get("trades", []),
        "adds": {int(k): v for k, v in raw_activity.get("adds", {}).items()},
        "drops": {int(k): v for k, v in raw_activity.get("drops", {}).items()},
    }

    with open(CACHE_DIR / "league_info.json") as f:
        league_info = json.load(f)

    with open(CACHE_DIR / "roster_totals.json") as f:
        roster_totals = json.load(f)

    with open(CACHE_DIR / "faab.json") as f:
        raw_faab = json.load(f)
    faab = {}
    for key, bid in raw_faab.items():
        parts = key.rsplit("|", 2)
        if len(parts) == 3:
            name, tid_str, week_str = parts
            week = int(week_str) if week_str != "None" else None
            faab[(name, int(tid_str), week)] = bid
        else:
            name, tid_str = key.rsplit("|", 1)
            faab[(name, int(tid_str), None)] = bid

    league = CachedLeague(league_info)
    total_weeks = league_info["totalWeeks"]
    print(f"  Loaded cache from {CACHE_DIR}/")
    return box_cache, roster_by_week, activity, league, total_weeks, roster_totals, faab


def cache_exists():
    return all(
        (CACHE_DIR / f).exists()
        for f in [
            "box_cache.json",
            "roster_by_week.json",
            "activity.json",
            "league_info.json",
            "roster_totals.json",
            "faab.json",
        ]
    )
