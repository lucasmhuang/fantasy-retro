"""
Fantasy Wrapped — ESPN Data Extraction Pipeline (H2H Points)

Pulls data from ESPN's Fantasy Basketball API and outputs one JSON file
per team plus a league_meta.json.

Two-phase fetch:
  Phase 1: matchup_total=True (21 calls) — weekly scores + starter weekly totals
  Phase 2: matchup_total=False per scoring period (~153 calls) — correct roster
           slots, bench player daily stats, eligible positions for optimal lineup

Usage:
    python extract.py              # Extract all teams
    python extract.py --team 1     # Extract just team ID 1 (for testing)
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from espn_api.basketball import League

load_dotenv()

LEAGUE_ID = int(os.getenv("ESPN_LEAGUE_ID", "0"))
YEAR = int(os.getenv("ESPN_YEAR", "2026"))
ESPN_S2 = os.getenv("ESPN_S2", "")
SWID = os.getenv("ESPN_SWID", "")
OUTPUT_DIR = Path(__file__).parent / "output"

MATCHUP_DATES = [
    (datetime(2025, 10, 21, tzinfo=timezone.utc), datetime(2025, 10, 26, tzinfo=timezone.utc)),
    (datetime(2025, 10, 27, tzinfo=timezone.utc), datetime(2025, 11, 2, tzinfo=timezone.utc)),
    (datetime(2025, 11, 3, tzinfo=timezone.utc), datetime(2025, 11, 9, tzinfo=timezone.utc)),
    (datetime(2025, 11, 10, tzinfo=timezone.utc), datetime(2025, 11, 16, tzinfo=timezone.utc)),
    (datetime(2025, 11, 17, tzinfo=timezone.utc), datetime(2025, 11, 23, tzinfo=timezone.utc)),
    (datetime(2025, 11, 24, tzinfo=timezone.utc), datetime(2025, 11, 30, tzinfo=timezone.utc)),
    (datetime(2025, 12, 1, tzinfo=timezone.utc), datetime(2025, 12, 7, tzinfo=timezone.utc)),
    (datetime(2025, 12, 8, tzinfo=timezone.utc), datetime(2025, 12, 14, tzinfo=timezone.utc)),
    (datetime(2025, 12, 15, tzinfo=timezone.utc), datetime(2025, 12, 21, tzinfo=timezone.utc)),
    (datetime(2025, 12, 22, tzinfo=timezone.utc), datetime(2025, 12, 28, tzinfo=timezone.utc)),
    (datetime(2025, 12, 29, tzinfo=timezone.utc), datetime(2026, 1, 4, tzinfo=timezone.utc)),
    (datetime(2026, 1, 5, tzinfo=timezone.utc), datetime(2026, 1, 11, tzinfo=timezone.utc)),
    (datetime(2026, 1, 12, tzinfo=timezone.utc), datetime(2026, 1, 18, tzinfo=timezone.utc)),
    (datetime(2026, 1, 19, tzinfo=timezone.utc), datetime(2026, 1, 25, tzinfo=timezone.utc)),
    (datetime(2026, 1, 26, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc)),
    (datetime(2026, 2, 2, tzinfo=timezone.utc), datetime(2026, 2, 8, tzinfo=timezone.utc)),
    (datetime(2026, 2, 9, tzinfo=timezone.utc), datetime(2026, 2, 22, tzinfo=timezone.utc)),
    (datetime(2026, 2, 23, tzinfo=timezone.utc), datetime(2026, 3, 1, tzinfo=timezone.utc)),
    (datetime(2026, 3, 2, tzinfo=timezone.utc), datetime(2026, 3, 8, tzinfo=timezone.utc)),
    (datetime(2026, 3, 9, tzinfo=timezone.utc), datetime(2026, 3, 15, tzinfo=timezone.utc)),
    (datetime(2026, 3, 16, tzinfo=timezone.utc), datetime(2026, 3, 22, tzinfo=timezone.utc)),
]

BENCH_SLOTS = frozenset({"BE", "Bench", "BN", "IR"})

ESPN_STAT_ID_MAP = {
    0: "PTS",
    1: "BLK",
    2: "STL",
    3: "AST",
    6: "REB",
    11: "TO",
    13: "FGM",
    14: "FGA",
    15: "FTM",
    16: "FTA",
    17: "3PM",
    19: "OREB",
    20: "DREB",
    28: "MPG",
    40: "MIN",
    42: "GS",
}

SLOT_ID_MAP = {
    0: "PG",
    1: "SG",
    2: "SF",
    3: "PF",
    4: "C",
    5: "G",
    6: "F",
    7: "SG/SF",
    8: "G/F",
    9: "PF/C",
    10: "F/C",
    11: "UT",
    12: "BE",
    13: "IR",
}

LINEUP_CONFIG = {"C": 1, "G": 3, "F": 3, "F/C": 1, "UT": 2}


# ---------------------------------------------------------------------------
# Compatibility wrappers (same interface as espn-api objects)
# ---------------------------------------------------------------------------


class TeamRef:
    def __init__(self, team_id, team_name):
        self.team_id = team_id
        self.team_name = team_name


class PlayerData:
    def __init__(self, name, points, points_breakdown, slot_position, position="", eligible_slot_ids=None):
        self.name = name
        self.points = points
        self.points_breakdown = points_breakdown
        self.slot_position = slot_position
        self.position = position
        self.eligibleSlots = eligible_slot_ids or []


class MatchupData:
    def __init__(self, home_team, away_team, home_score, away_score, home_lineup, away_lineup):
        self.home_team = home_team
        self.away_team = away_team
        self.home_score = home_score
        self.away_score = away_score
        self.home_lineup = home_lineup
        self.away_lineup = away_lineup


# ---------------------------------------------------------------------------
# Cache Serialization
# ---------------------------------------------------------------------------

CACHE_DIR = Path(__file__).parent / "cache"


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


def fetch_roster_totals(league):
    """Extract season totals capped to the league's final scoring period.

    Uses league.player_info() per player to get per-scoring-period breakdowns,
    then sums only periods <= finalScoringPeriod (excludes post-league games).
    Returns {player_name: {"total_points": float, "gp": int}}.
    """
    year = str(YEAR)
    final_sp = league.finalScoringPeriod
    players = {}
    for team in league.teams:
        for player in team.roster:
            players[player.name] = player.playerId
    for pick in league.draft:
        if pick.playerName not in players:
            pid = league.player_map.get(pick.playerName)
            if pid:
                players[pick.playerName] = pid

    totals = {}
    player_list = list(players.items())
    for i, (name, pid) in enumerate(player_list):
        if (i + 1) % 20 == 0 or i == 0:
            print(f"    {i + 1}/{len(player_list)}...", end="\r")
        try:
            info = _retry(lambda p=pid: league.player_info(playerId=p))
            pts = 0.0
            gp = 0
            for key, val in info.stats.items():
                if key.startswith(year):
                    continue
                try:
                    sp = int(key)
                except ValueError:
                    continue
                if sp <= final_sp:
                    sp_pts = val.get("applied_total", 0)
                    pts += sp_pts
                    if sp_pts > 0:
                        gp += 1
            totals[name] = {"total_points": round(pts, 1), "gp": gp}
        except Exception:
            totals[name] = {"total_points": 0, "gp": 0}
    print(f"    Done ({len(player_list)} players)" + " " * 20)
    return totals


def compute_last_week_by_team(box_cache, total_weeks, reg_weeks):
    """Return {team_id: last_week} based on first playoff loss.

    Non-playoff teams: last_week = reg_weeks (18).
    Playoff teams: last_week = week of first loss in weeks > reg_weeks.
    Champion (no playoff losses): last_week = their final matchup week.
    No consolation bracket — a playoff loss ends the season.
    """
    max_week = {}
    for week in range(1, total_weeks + 1):
        for box in box_cache.get(week, []):
            for t in [box.home_team, box.away_team]:
                if t and (t.team_id not in max_week or week > max_week[t.team_id]):
                    max_week[t.team_id] = week

    last = {}
    for tid, mw in max_week.items():
        if mw <= reg_weeks:
            last[tid] = reg_weeks
            continue
        last[tid] = mw
        for week in range(reg_weeks + 1, total_weeks + 1):
            for box in box_cache.get(week, []):
                lineup, my_score, _opp, opp_score = find_team_in_matchup(box, tid)
                if lineup is None:
                    continue
                if my_score < opp_score:
                    last[tid] = week
                    break
            if last[tid] != mw:
                break
    return last


def compute_final_placement(box_cache, last_week_map, league_teams, reg_weeks):
    """Return {team_id: placement} (1 = champion, 2 = runner-up, etc.).

    Traces the bracket to distinguish 3rd/4th and 5th/6th: the team that
    lost to the eventual champion ranks higher than the team that lost to
    the runner-up.  Consolation bracket matchups are ignored via last_week_map.
    """
    placement = {}
    champ_id = None
    runner_id = None

    finalists = {tid for tid, lw in last_week_map.items() if lw >= 21}
    for box in box_cache.get(21, []):
        h, a = box.home_team.team_id, box.away_team.team_id
        if h not in finalists or a not in finalists:
            continue
        if box.home_score > box.away_score:
            champ_id, runner_id = h, a
        else:
            champ_id, runner_id = a, h
    if champ_id:
        placement[champ_id] = 1
    if runner_id:
        placement[runner_id] = 2

    def _opponent_in_week(team_id, week):
        for box in box_cache.get(week, []):
            if box.home_team and box.home_team.team_id == team_id:
                return box.away_team.team_id
            if box.away_team and box.away_team.team_id == team_id:
                return box.home_team.team_id
        return None

    semis = [tid for tid, lw in last_week_map.items() if lw == 20]
    third_id = None
    for tid in semis:
        lost_to = _opponent_in_week(tid, 20)
        if lost_to == champ_id:
            third_id = tid
            placement[tid] = 3
        else:
            placement[tid] = 4

    quarters = [tid for tid, lw in last_week_map.items() if lw == 19]
    for tid in quarters:
        lost_to = _opponent_in_week(tid, 19)
        placement[tid] = 5 if lost_to in (third_id, champ_id) else 6

    non_playoff = sorted(
        [tid for tid, lw in last_week_map.items() if lw <= reg_weeks],
        key=lambda tid: next(t.standing for t in league_teams if t.team_id == tid),
    )
    for i, tid in enumerate(non_playoff):
        placement[tid] = 7 + i

    return placement


def _compute_pre_event_points(player_name, before_week, box_cache):
    """Sum a player's points across ALL teams' lineups for weeks 1..before_week-1."""
    pts = 0.0
    for week in range(1, before_week):
        for box in box_cache.get(week, []):
            for lineup in [box.home_lineup or [], box.away_lineup or []]:
                for player in lineup:
                    if player.name == player_name:
                        pts += player.points or 0
    return pts


def _compute_pre_event_games(player_name, before_week, nba_games_by_week):
    """Sum a player's NBA games for weeks 1..before_week-1."""
    pw = nba_games_by_week.get(player_name, {})
    return sum(pw.get(w, 0) for w in range(1, before_week))


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


class CachedTeam:
    def __init__(self, d):
        self.team_id = d["id"]
        self.team_name = d["name"]
        self.owners = d.get("owners", [])
        self.wins = d["wins"]
        self.losses = d["losses"]
        self.standing = d["standing"]
        self.points_for = d["pointsFor"]
        self.points_against = d["pointsAgainst"]
        self.schedule = [None] * d.get("schedule", 21)


class CachedDraftPick:
    def __init__(self, d, teams_by_id):
        self.round_num = d["round"]
        self.round_pick = d["pick"]
        self.playerName = d["playerName"]
        self.team = teams_by_id.get(d["teamId"], TeamRef(d["teamId"], d.get("teamName", "")))


class CachedLeague:
    def __init__(self, info):
        self.teams = [CachedTeam(t) for t in info["teams"]]
        teams_by_id = {t.team_id: t for t in self.teams}
        self.draft = [CachedDraftPick(p, teams_by_id) for p in info["draft"]]
        self.settings = type(
            "Settings",
            (),
            {
                "name": info["name"],
                "scoring_type": info["scoringType"],
                "reg_season_count": info["regSeasonWeeks"],
                "_raw_scoring_settings": {"scoringItems": info["scoringSettings"]},
            },
        )()


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
            "box_cache.json", "roster_by_week.json", "activity.json",
            "league_info.json", "roster_totals.json", "faab.json",
        ]
    )


# ---------------------------------------------------------------------------
# Connection & Data Fetching
# ---------------------------------------------------------------------------


def connect():
    if not LEAGUE_ID:
        print("ERROR: ESPN_LEAGUE_ID not set in .env")
        sys.exit(1)
    print(f"Connecting to league {LEAGUE_ID} ({YEAR - 1}-{str(YEAR)[2:]})...")
    league = League(
        league_id=LEAGUE_ID,
        year=YEAR,
        espn_s2=ESPN_S2 or None,
        swid=SWID or None,
    )
    print(f"  Connected: {league.settings.name} ({len(league.teams)} teams)")
    return league


def _retry(fn):
    for attempt in range(2):
        try:
            return fn()
        except Exception:
            if attempt == 0:
                time.sleep(1)
            else:
                raise


def fetch_box_scores(league, total_weeks):
    """Fetch enriched matchup data with correct roster slots and bench players.

    Phase 1: matchup_total=True — weekly scores + starter totals (RFMP)
    Phase 2: matchup_total=False per scoring period — correct slots, bench (RFCSP)
    Returns: {week: [MatchupData]} with full lineup including bench.
    """
    sp_ranges = {week: [int(sp) for sp in sps] for week, sps in league.matchup_ids.items()}

    # Phase 1: weekly totals
    print("  Phase 1: Weekly matchup scores...")
    weekly_box = {}
    for week in range(1, total_weeks + 1):
        print(f"    Week {week}/{total_weeks}", end="\r")
        try:
            weekly_box[week] = _retry(lambda w=week: league.box_scores(matchup_period=w))
        except Exception as e:
            print(f"\n    Warning: week {week} failed: {e}")
            weekly_box[week] = []
    print(f"    Done ({total_weeks} weeks)" + " " * 20)

    # Phase 2: daily roster data per scoring period
    total_sps = sum(len(sps) for week, sps in sp_ranges.items() if week <= total_weeks)
    print(f"  Phase 2: Roster data ({total_sps} scoring periods)...")

    # {week: {team_id: {player_name: {slot, position, eligible, daily_pts}}}}
    roster_by_week = defaultdict(lambda: defaultdict(dict))

    call_num = 0
    for week in range(1, total_weeks + 1):
        for sp in sp_ranges.get(week, []):
            call_num += 1
            if call_num % 20 == 0 or call_num == 1:
                print(f"    {call_num}/{total_sps}...", end="\r")
            try:
                daily = _retry(
                    lambda w=week, s=sp: league.box_scores(matchup_period=w, scoring_period=s, matchup_total=False)
                )
            except Exception:
                continue

            for box in daily:
                for team_obj, lineup in [(box.home_team, box.home_lineup), (box.away_team, box.away_lineup)]:
                    if not team_obj or not lineup:
                        continue
                    tid = team_obj.team_id
                    for player in lineup:
                        name = player.name
                        if name not in roster_by_week[week][tid]:
                            roster_by_week[week][tid][name] = {
                                "slot": player.slot_position,
                                "position": getattr(player, "position", ""),
                                "eligible": getattr(player, "eligibleSlots", []),
                                "daily_pts": [],
                            }
                        roster_by_week[week][tid][name]["daily_pts"].append(player.points or 0)
                        roster_by_week[week][tid][name]["slot"] = player.slot_position
    print(f"    Done ({call_num} calls)" + " " * 30)

    # Merge: RFMP weekly totals + RFCSP roster data
    cache = {}
    for week in range(1, total_weeks + 1):
        matchups = []
        for box in weekly_box.get(week, []):
            if not box.home_team or not box.away_team:
                continue
            matchups.append(
                MatchupData(
                    home_team=TeamRef(box.home_team.team_id, box.home_team.team_name),
                    away_team=TeamRef(box.away_team.team_id, box.away_team.team_name),
                    home_score=box.home_score,
                    away_score=box.away_score,
                    home_lineup=_merge_lineup(box.home_lineup, roster_by_week[week].get(box.home_team.team_id, {})),
                    away_lineup=_merge_lineup(box.away_lineup, roster_by_week[week].get(box.away_team.team_id, {})),
                )
            )
        cache[week] = matchups

    return cache, dict(roster_by_week)


def _merge_lineup(rfmp_players, roster_data):
    """Merge RFMP starters (weekly pts) with RFCSP roster (correct slots, bench).

    rfmp_players: library BoxPlayer list (10 starters, all slot=PG, weekly totals)
    roster_data: {name: {slot, position, eligible, daily_pts}} from RFCSP
    """
    starter_pts = {p.name: p.points for p in rfmp_players}
    starter_bkdn = {p.name: getattr(p, "points_breakdown", {}) for p in rfmp_players}

    lineup = []
    seen = set()

    for name, data in roster_data.items():
        seen.add(name)
        is_starter = name in starter_pts
        slot = data["slot"]
        if slot in BENCH_SLOTS:
            slot = "BE"

        lineup.append(
            PlayerData(
                name=name,
                points=starter_pts[name] if is_starter else round(sum(data["daily_pts"]), 1),
                points_breakdown=starter_bkdn.get(name, {}) if is_starter else {},
                slot_position=slot,
                position=data.get("position", ""),
                eligible_slot_ids=data.get("eligible", []),
            )
        )

    for p in rfmp_players:
        if p.name not in seen:
            lineup.append(
                PlayerData(
                    name=p.name,
                    points=p.points,
                    points_breakdown=getattr(p, "points_breakdown", {}),
                    slot_position="UT",
                    position=getattr(p, "position", ""),
                    eligible_slot_ids=getattr(p, "eligibleSlots", []),
                )
            )

    return lineup


def fetch_activity(league):
    all_activity = []
    page_size = 25
    for page_num in range(80):
        offset = page_num * page_size
        try:
            page = league.recent_activity(size=page_size, offset=offset)
        except TypeError:
            try:
                return league.recent_activity(size=500)
            except Exception as e:
                print(f"  Warning: activity fetch failed: {e}")
                return all_activity
        except Exception as e:
            print(f"  Warning: activity fetch failed at offset {offset}: {e}")
            break
        if not page:
            break
        all_activity.extend(page)
        if len(page) < page_size:
            break
    return all_activity


def fetch_faab(league):
    """Fetch FAAB bid amounts from the transactions endpoint.

    Returns {(player_name, team_id, week): bid_amount} for all waiver/FA adds.
    Requires one API call per scoring period (~153 calls).
    """
    import json as _json

    final_sp = league.finalScoringPeriod
    all_txns = []
    for sp in range(1, final_sp + 1):
        if sp % 20 == 0 or sp == 1:
            print(f"    {sp}/{final_sp}...", end="\r")
        params = {"view": "mTransactions2", "scoringPeriodId": sp}
        filters = {"transactions": {"filterType": {"value": ["WAIVER", "FREEAGENT"]}}}
        headers = {"x-fantasy-filter": _json.dumps(filters)}
        try:
            data = _retry(
                lambda p=params, h=headers: league.espn_request.league_get(params=p, headers=h)
            )
            all_txns.extend(data.get("transactions", []))
        except Exception:
            continue
    print(f"    Done ({final_sp} scoring periods)" + " " * 20)

    faab = {}
    for txn in all_txns:
        bid = txn.get("bidAmount", 0)
        team_id = txn["teamId"]
        txn_date = txn.get("processDate") or txn.get("acceptedDate") or txn.get("date", 0)
        week = date_to_week(txn_date)
        for item in txn.get("items", []):
            if item["type"] == "ADD":
                pid = item["playerId"]
                name = league.player_map.get(pid, f"id:{pid}")
                faab[(name, team_id, week)] = bid
    return faab


def classify_activity(activities):
    trades = []
    adds = defaultdict(list)
    drops = defaultdict(list)

    for activity in activities:
        trade_actions = []
        for action in activity.actions:
            if len(action) < 3:
                continue
            team_obj, action_type, player_name = action[0], action[1], action[2]

            if "TRADED" in action_type:
                trade_actions.append(
                    {
                        "team_id": team_obj.team_id,
                        "team_name": team_obj.team_name,
                        "player": player_name,
                    }
                )
            elif "ADDED" in action_type:
                adds[team_obj.team_id].append(
                    {
                        "player": player_name,
                        "date": activity.date,
                    }
                )
            elif "DROPPED" in action_type:
                drops[team_obj.team_id].append(
                    {
                        "player": player_name,
                        "date": activity.date,
                    }
                )

        if trade_actions:
            trades.append({"actions": trade_actions, "date": activity.date})

    return {"trades": trades, "adds": dict(adds), "drops": dict(drops)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Shared Computations
# ---------------------------------------------------------------------------


def compute_standings_by_week(box_cache, teams, reg_weeks):
    cumulative = {t.team_id: {"wins": 0, "losses": 0, "pts_for": 0.0} for t in teams}
    standings = {}

    for week in range(1, reg_weeks + 1):
        for box in box_cache.get(week, []):
            if not box.home_team or not box.away_team:
                continue
            h_id, a_id = box.home_team.team_id, box.away_team.team_id
            h_score, a_score = box.home_score or 0, box.away_score or 0

            cumulative[h_id]["pts_for"] += h_score
            cumulative[a_id]["pts_for"] += a_score

            if h_score > a_score:
                cumulative[h_id]["wins"] += 1
                cumulative[a_id]["losses"] += 1
            elif a_score > h_score:
                cumulative[a_id]["wins"] += 1
                cumulative[h_id]["losses"] += 1

        sorted_teams = sorted(
            cumulative.items(),
            key=lambda x: (
                x[1]["wins"] / max(1, x[1]["wins"] + x[1]["losses"]),
                x[1]["pts_for"],
            ),
            reverse=True,
        )
        standings[week] = {tid: rank + 1 for rank, (tid, _) in enumerate(sorted_teams)}

    return standings


def collect_weekly_team_scores(box_cache, total_weeks):
    scores = {}
    for week in range(1, total_weeks + 1):
        week_scores = {}
        for box in box_cache.get(week, []):
            if box.home_team:
                week_scores[box.home_team.team_id] = round(box.home_score or 0, 1)
            if box.away_team:
                week_scores[box.away_team.team_id] = round(box.away_score or 0, 1)
        scores[week] = week_scores
    return scores


def compute_player_season_totals(box_cache, total_weeks):
    totals = defaultdict(float)
    for week in range(1, total_weeks + 1):
        for box in box_cache.get(week, []):
            for lineup in [box.home_lineup or [], box.away_lineup or []]:
                for player in lineup:
                    totals[player.name] += player.points or 0
    return {name: round(pts, 1) for name, pts in totals.items()}


# ---------------------------------------------------------------------------
# Per-Team: Weekly Results
# ---------------------------------------------------------------------------


def build_events_by_week(team_id, activity):
    trade_events = defaultdict(list)
    pickup_events = defaultdict(list)

    for trade in activity["trades"]:
        sent, received, involved = [], [], False
        for action in trade["actions"]:
            if action["team_id"] == team_id:
                sent.append(action["player"])
                involved = True
            else:
                received.append(action["player"])
        if involved:
            week = date_to_week(trade["date"])
            if week:
                s = " + ".join(sent) if sent else "nothing"
                r = " + ".join(received) if received else "nothing"
                trade_events[week].append(f"Traded {s} for {r}")

    for add in activity["adds"].get(team_id, []):
        week = date_to_week(add["date"])
        if week:
            pickup_events[week].append(add["player"])

    result = {}
    all_weeks = set(trade_events.keys()) | set(pickup_events.keys())
    for week in all_weeks:
        trades = trade_events.get(week, [])
        pickups = pickup_events.get(week, [])
        if trades:
            result[week] = trades[0] if len(trades) == 1 else trades[0] + f" (+{len(trades) - 1} more)"
        elif pickups:
            result[week] = f"Picked up {', '.join(pickups)}"
    return result


def extract_weekly_results(team_id, box_cache, standings, events, total_weeks):
    results = []
    for week in range(1, total_weeks + 1):
        for box in box_cache.get(week, []):
            lineup, score, opp_team, opp_score = find_team_in_matchup(box, team_id)
            if lineup is None:
                continue

            score = round(score or 0, 1)
            opp_score = round(opp_score or 0, 1)

            if score > opp_score:
                result = "W"
            elif score < opp_score:
                result = "L"
            else:
                result = "T"

            entry = {
                "week": week,
                "result": result,
                "score": score,
                "oppScore": opp_score,
                "opponent": opp_team.team_name if opp_team else "BYE",
                "standing": standings.get(week, {}).get(team_id, 0),
            }
            if week in events:
                entry["event"] = events[week]
            results.append(entry)
            break

    return results


# ---------------------------------------------------------------------------
# Per-Team: Trades (fixed: skip phantom trades)
# ---------------------------------------------------------------------------


def extract_trades(
    team_id,
    activity,
    box_cache,
    total_weeks,
    replacement_ppg=0.0,
    nba_games=None,
    player_totals=None,
    nba_games_total=None,
):
    use_roster_totals = bool(player_totals)
    team_trades = []

    for trade in activity["trades"]:
        sent, received, partner = [], [], None
        for action in trade["actions"]:
            if action["team_id"] == team_id:
                sent.append(action["player"])
            else:
                received.append(action["player"])
                partner = action["team_name"]

        if not sent or not received:
            continue

        trade_week = date_to_week(trade["date"])
        sent_pts, received_pts = 0.0, 0.0
        weekly_breakdown = []
        player_pts = defaultdict(float)
        player_games = defaultdict(int)

        if trade_week:
            sent_set, recv_set = set(sent), set(received)
            all_players = sent_set | recv_set

            if use_roster_totals:
                for name in all_players:
                    pre = _compute_pre_event_points(name, trade_week, box_cache)
                    player_pts[name] = player_totals.get(name, 0) - pre
                sent_pts = sum(player_pts[n] for n in sent_set)
                received_pts = sum(player_pts[n] for n in recv_set)
            else:
                for week in range(trade_week, total_weeks + 1):
                    week_sent, week_recv = 0.0, 0.0
                    week_seen = set()
                    for box in box_cache.get(week, []):
                        for lineup in [box.home_lineup or [], box.away_lineup or []]:
                            for player in lineup:
                                if player.name in all_players:
                                    pts = player.points or 0
                                    player_pts[player.name] += pts
                                    if player.name not in week_seen:
                                        player_games[player.name] += 1
                                        week_seen.add(player.name)
                                if player.name in sent_set:
                                    week_sent += player.points or 0
                                if player.name in recv_set:
                                    week_recv += player.points or 0
                    sent_pts += week_sent
                    received_pts += week_recv
                    weekly_breakdown.append(
                        {
                            "week": week,
                            "sentPts": round(week_sent, 1),
                            "receivedPts": round(week_recv, 1),
                        }
                    )

        def _player_stats(names):
            stats = []
            for name in names:
                pts = player_pts.get(name, 0)
                if use_roster_totals and nba_games_total and trade_week:
                    pre_gp = _compute_pre_event_games(name, trade_week, nba_games)
                    g = nba_games_total.get(name, 0) - pre_gp
                elif nba_games and trade_week:
                    pw = nba_games.get(name, {})
                    g = sum(pw.get(w, 0) for w in range(trade_week, total_weeks + 1))
                else:
                    g = player_games.get(name, 0)
                stats.append(
                    {
                        "player": name,
                        "ptsROS": round(pts, 1),
                        "gamesROS": g,
                        "ppgROS": round(pts / g, 1) if g > 0 else 0,
                    }
                )
            return stats

        spot_diff = len(sent) - len(received)
        slot_adj = 0.0
        if spot_diff != 0 and trade_week and replacement_ppg > 0:
            weeks_remaining = total_weeks - trade_week + 1
            slot_adj = abs(spot_diff) * replacement_ppg * weeks_remaining
            if spot_diff > 0:
                received_pts += slot_adj
            else:
                sent_pts += slot_adj

        team_trades.append(
            {
                "week": trade_week,
                "partner": partner or "Unknown",
                "sent": sent,
                "received": received,
                "sentPtsROS": round(sent_pts, 1),
                "receivedPtsROS": round(received_pts, 1),
                "net": round(received_pts - sent_pts, 1),
                "slotAdjustment": round(slot_adj, 1),
                "sentStats": _player_stats(sent),
                "receivedStats": _player_stats(received),
                "weeklyBreakdown": weekly_breakdown,
            }
        )

    result = _deduplicate_trades(team_trades)
    result.sort(key=lambda t: t["week"] or 0)
    return result


def _deduplicate_trades(trades):
    """Remove LM reversal/re-application duplicates.

    If the same players appear between the same partner as both a trade and
    its mirror (or exact duplicate) within the same week, keep only the last
    occurrence — the final state after LM corrections.
    """

    def trade_key(t):
        return (t["partner"], frozenset(t["sent"]), frozenset(t["received"]))

    def mirror_key(t):
        return (t["partner"], frozenset(t["received"]), frozenset(t["sent"]))

    seen_keys = {}
    for i, t in enumerate(trades):
        k = trade_key(t)
        mk = mirror_key(t)
        if mk in seen_keys:
            prev_idx = seen_keys.pop(mk)
            trades[prev_idx] = None
            trades[i] = None
        elif k in seen_keys:
            prev_idx = seen_keys[k]
            seen_keys[k] = i
            trades[prev_idx] = None
        else:
            seen_keys[k] = i

    return [t for t in trades if t is not None]


# ---------------------------------------------------------------------------
# Per-Team: Waiver Pickups
# ---------------------------------------------------------------------------


def _is_lm_roster_move(player_name, add_date, team_id, activity):
    """Detect LM IR moves: same team dropped+added the same player within 24 hours."""
    if not add_date:
        return False
    one_day_ms = 24 * 60 * 60 * 1000
    for drop in activity["drops"].get(team_id, []):
        if drop["player"] == player_name and drop["date"]:
            if abs(add_date - drop["date"]) < one_day_ms:
                return True
    return False


def _find_team_drop_week(player_name, add_date, team_id, activity):
    """Find the week this team next dropped this player after add_date."""
    best = None
    for drop in activity["drops"].get(team_id, []):
        if drop["player"] == player_name and drop["date"] and drop["date"] > add_date:
            if best is None or drop["date"] < best:
                best = drop["date"]
    return date_to_week(best) if best else None


def extract_waiver_pickups(team_id, activity, box_cache, total_weeks, max_pickups=10):
    team_adds = sorted(activity["adds"].get(team_id, []), key=lambda a: a["date"] or 0)

    filtered_adds = []
    for add in team_adds:
        add_week = date_to_week(add["date"])
        if add_week and add_week >= total_weeks:
            continue
        if _is_lm_roster_move(add["player"], add["date"], team_id, activity):
            continue
        filtered_adds.append(add)

    pickups = []
    for add in filtered_adds:
        name = add["player"]
        add_week = date_to_week(add["date"])
        drop_week = _find_team_drop_week(name, add["date"], team_id, activity)
        end_week = drop_week if drop_week else total_weeks
        pts = 0.0
        weekly_points = []

        if add_week:
            for week in range(add_week, end_week + 1):
                week_pts = 0.0
                for box in box_cache.get(week, []):
                    lineup, _, _, _ = find_team_in_matchup(box, team_id)
                    if not lineup:
                        continue
                    for player in lineup:
                        if player.name == name:
                            week_pts += player.points or 0
                    break
                pts += week_pts
                weekly_points.append({"week": week, "pts": round(week_pts, 1)})

        if pts >= 10:
            pickups.append(
                {
                    "player": name,
                    "weekAdded": add_week,
                    "addDate": add["date"],
                    "ptsAfterAdd": round(pts, 1),
                    "weeklyPoints": weekly_points,
                }
            )

    pickups.sort(key=lambda x: x["ptsAfterAdd"], reverse=True)
    return pickups[:max_pickups] if max_pickups else pickups


# ---------------------------------------------------------------------------
# Per-Team: Scoring Profile
# ---------------------------------------------------------------------------


def extract_scoring_profile(team_id, box_cache, reg_weeks):
    totals = defaultdict(float)

    for week in range(1, reg_weeks + 1):
        for box in box_cache.get(week, []):
            lineup, _, _, _ = find_team_in_matchup(box, team_id)
            if not lineup:
                continue
            for player in lineup:
                if player.slot_position in BENCH_SLOTS:
                    continue
                for cat, pts in (player.points_breakdown or {}).items():
                    totals[cat] += pts
            break

    grand_total = sum(abs(v) for v in totals.values())
    return {
        cat: {
            "total": round(pts, 1),
            "pct": round(pts / grand_total, 3) if grand_total else 0,
        }
        for cat, pts in sorted(totals.items(), key=lambda x: abs(x[1]), reverse=True)
    }


# ---------------------------------------------------------------------------
# Per-Team: All-Play Record
# ---------------------------------------------------------------------------


def extract_all_play(team_id, weekly_team_scores, reg_weeks):
    wins, losses = 0, 0

    for week in range(1, reg_weeks + 1):
        scores = weekly_team_scores.get(week, {})
        my_score = scores.get(team_id)
        if my_score is None:
            continue
        for tid, score in scores.items():
            if tid == team_id:
                continue
            if my_score > score:
                wins += 1
            elif my_score < score:
                losses += 1

    total = wins + losses
    return {
        "wins": wins,
        "losses": losses,
        "winPct": round(wins / total, 3) if total else 0,
    }


# ---------------------------------------------------------------------------
# Per-Team: Roster Heatmap
# ---------------------------------------------------------------------------


def extract_roster_heatmap(team_id, box_cache, total_weeks):
    player_weeks = defaultdict(dict)

    for week in range(1, total_weeks + 1):
        for box in box_cache.get(week, []):
            lineup, _, _, _ = find_team_in_matchup(box, team_id)
            if not lineup:
                continue
            for player in lineup:
                slot = "BN" if player.slot_position in BENCH_SLOTS else player.slot_position
                player_weeks[player.name][week] = (slot, round(player.points or 0, 1))
            break

    rows = []
    for name, weeks_data in player_weeks.items():
        slot_counts = defaultdict(int)
        for slot, _ in weeks_data.values():
            slot_counts[slot] += 1

        non_bench = {s: c for s, c in slot_counts.items() if s != "BN"}
        primary_slot = max(non_bench, key=non_bench.get) if non_bench else "BN"

        weeks_array = [weeks_data.get(w, (None, 0))[1] for w in range(1, total_weeks + 1)]
        total_pts = sum(weeks_array)

        rows.append(
            {
                "slot": primary_slot,
                "player": name,
                "weeks": weeks_array,
                "_total": total_pts,
            }
        )

    starters = sorted(
        [r for r in rows if r["slot"] != "BN"],
        key=lambda x: x["_total"],
        reverse=True,
    )
    bench = sorted(
        [r for r in rows if r["slot"] == "BN"],
        key=lambda x: x["_total"],
        reverse=True,
    )

    return [{"slot": r["slot"], "player": r["player"], "weeks": r["weeks"]} for r in starters + bench]


# ---------------------------------------------------------------------------
# Per-Team: Points Left on Bench
# ---------------------------------------------------------------------------


def _week_has_adjustment(team_id, box_cache, week):
    """Detect if a week had manual point adjustments (starter sum != team score)."""
    for box in box_cache.get(week, []):
        lineup, team_score, _, _ = find_team_in_matchup(box, team_id)
        if lineup is None or team_score is None:
            continue
        starter_sum = sum(p.points or 0 for p in lineup if p.slot_position not in BENCH_SLOTS)
        return abs(starter_sum - team_score) > 1.0
    return False


def extract_bench_points(team_id, box_cache, weekly_results, reg_weeks):
    all_misplays = []

    loss_margins = {}
    for w in weekly_results:
        if w["result"] == "L" and w["week"] <= reg_weeks:
            loss_margins[w["week"]] = round(w["oppScore"] - w["score"], 1)

    for week in range(1, reg_weeks + 1):
        if _week_has_adjustment(team_id, box_cache, week):
            continue

        for box in box_cache.get(week, []):
            lineup, _, _, _ = find_team_in_matchup(box, team_id)
            if not lineup:
                continue

            starters = [
                (p.name, round(p.points or 0, 1))
                for p in lineup
                if p.slot_position not in BENCH_SLOTS and (p.points or 0) >= 10
            ]
            benched = [
                (p.name, round(p.points or 0, 1))
                for p in lineup
                if p.slot_position in BENCH_SLOTS and (p.points or 0) >= 10
            ]

            if starters and benched:
                worst_starter = min(starters, key=lambda x: x[1])
                best_bench = max(benched, key=lambda x: x[1])
                if best_bench[1] > worst_starter[1]:
                    diff = round(best_bench[1] - worst_starter[1], 1)
                    margin = loss_margins.get(week)
                    would_have_won = margin is not None and diff > margin
                    all_misplays.append(
                        {
                            "week": week,
                            "benchPlayer": best_bench[0],
                            "benchPts": best_bench[1],
                            "startPlayer": worst_starter[0],
                            "startPts": worst_starter[1],
                            "diff": diff,
                            "wouldHaveWon": would_have_won,
                            "lossMargin": margin,
                        }
                    )
            break

    flippers = sorted(
        [m for m in all_misplays if m["wouldHaveWon"]],
        key=lambda x: x["diff"],
        reverse=True,
    )
    non_flippers = sorted(
        [m for m in all_misplays if not m["wouldHaveWon"]],
        key=lambda x: x["diff"],
        reverse=True,
    )

    return (flippers + non_flippers)[:5]


# ---------------------------------------------------------------------------
# Per-Team: Head-to-Head
# ---------------------------------------------------------------------------


def extract_head_to_head(weekly_results, reg_weeks):
    h2h = defaultdict(
        lambda: {
            "wins": 0,
            "losses": 0,
            "margins": [],
            "playoffWins": 0,
            "playoffLosses": 0,
        }
    )

    for week in weekly_results:
        opp = week["opponent"]
        margin = week["score"] - week["oppScore"]
        is_playoff = week["week"] > reg_weeks
        if is_playoff:
            if week["result"] == "W":
                h2h[opp]["playoffWins"] += 1
            elif week["result"] == "L":
                h2h[opp]["playoffLosses"] += 1
        else:
            h2h[opp]["margins"].append(margin)
            if week["result"] == "W":
                h2h[opp]["wins"] += 1
            elif week["result"] == "L":
                h2h[opp]["losses"] += 1

    result = []
    for opp, data in h2h.items():
        games = len(data["margins"])
        result.append(
            {
                "opponent": opp,
                "wins": data["wins"],
                "losses": data["losses"],
                "avgMargin": round(sum(data["margins"]) / games) if games else 0,
                "playoffWins": data["playoffWins"],
                "playoffLosses": data["playoffLosses"],
            }
        )

    return sorted(result, key=lambda x: x["wins"] - x["losses"], reverse=True)


# ---------------------------------------------------------------------------
# Optimal Lineup
# ---------------------------------------------------------------------------


def compute_optimal_lineup(team_id, box_cache, week):
    """Compute the optimal lineup for a team in a given week.

    Uses branch-and-bound with most-constrained-first slot ordering.
    Returns (optimal_pts, actual_starter_pts).
    """
    for box in box_cache.get(week, []):
        lineup, _, _, _ = find_team_in_matchup(box, team_id)
        if not lineup:
            continue

        roster = []
        actual_pts = 0.0
        for player in lineup:
            eligible = getattr(player, "eligibleSlots", [])
            active_eligible = [s for s in eligible if s in LINEUP_CONFIG]
            roster.append(
                {
                    "name": player.name,
                    "points": player.points or 0,
                    "eligible": set(active_eligible),
                }
            )
            if player.slot_position not in BENCH_SLOTS:
                actual_pts += player.points or 0

        if not roster:
            return 0.0, 0.0

        slots = []
        for slot_id, count in sorted(
            LINEUP_CONFIG.items(),
            key=lambda x: sum(1 for p in roster if x[0] in p["eligible"]),
        ):
            slots.extend([slot_id] * count)

        eligible_per_slot = {}
        for i, slot_id in enumerate(slots):
            eligible_per_slot[i] = sorted(
                [j for j, p in enumerate(roster) if slot_id in p["eligible"]],
                key=lambda j: -roster[j]["points"],
            )

        best = [0.0]

        def bound(idx, used):
            remaining = len(slots) - idx
            avail = sorted(
                [roster[j]["points"] for j in range(len(roster)) if j not in used],
                reverse=True,
            )
            return sum(avail[:remaining])

        def backtrack(idx, used, pts):
            if idx == len(slots):
                if pts > best[0]:
                    best[0] = pts
                return

            if pts + bound(idx, used) <= best[0]:
                return

            for j in eligible_per_slot.get(idx, []):
                if j in used:
                    continue
                used.add(j)
                backtrack(idx + 1, used, pts + roster[j]["points"])
                used.remove(j)

        backtrack(0, set(), 0.0)
        return round(best[0], 1), round(actual_pts, 1)

    return 0.0, 0.0


def extract_optimal_lineup(team_id, box_cache, reg_weeks):
    weekly = []
    total_actual, total_optimal = 0.0, 0.0

    for week in range(1, reg_weeks + 1):
        if _week_has_adjustment(team_id, box_cache, week):
            continue
        optimal, actual = compute_optimal_lineup(team_id, box_cache, week)
        weekly.append(
            {
                "week": week,
                "actualPts": actual,
                "optimalPts": optimal,
                "diff": round(optimal - actual, 1),
            }
        )
        total_actual += actual
        total_optimal += optimal

    return {
        "weeklyComparison": weekly,
        "totalActual": round(total_actual, 1),
        "totalOptimal": round(total_optimal, 1),
        "efficiency": round(total_actual / total_optimal, 3) if total_optimal else 1.0,
    }


# ---------------------------------------------------------------------------
# Awards
# ---------------------------------------------------------------------------


def compute_awards(weekly_results, heatmap, weekly_team_scores, team_id, reg_weeks):
    reg = [w for w in weekly_results if w["week"] <= reg_weeks]
    losses = [w for w in reg if w["result"] == "L"]
    wins = [w for w in reg if w["result"] == "W"]

    awards = {}

    starter_rows = [r for r in heatmap if r["slot"] != "BN"]
    if starter_rows:
        mvp_row = max(starter_rows, key=lambda r: sum(r["weeks"]))
        awards["mvp"] = {
            "player": mvp_row["player"],
            "totalPts": round(sum(mvp_row["weeks"]), 1),
        }

    candidates = [r for r in heatmap if sum(1 for p in r["weeks"] if p > 0) >= 6]
    if candidates:

        def avg_pts(r):
            active = [p for p in r["weeks"] if p > 0]
            return sum(active) / len(active) if active else 0

        bw = min(candidates, key=avg_pts)
        active = [p for p in bw["weeks"] if p > 0]
        awards["benchWarmer"] = {
            "player": bw["player"],
            "weeks": len(active),
            "totalPts": round(sum(active), 1),
            "avgPts": round(sum(active) / len(active), 1),
        }

    if losses:
        hb = min(losses, key=lambda w: abs(w["score"] - w["oppScore"]))
        awards["heartbreakLoss"] = {
            "week": hb["week"],
            "opponent": hb["opponent"],
            "score": hb["score"],
            "oppScore": hb["oppScore"],
            "margin": round(abs(hb["score"] - hb["oppScore"]), 1),
        }

    if wins:
        sw = max(wins, key=lambda w: w["score"] - w["oppScore"])
        awards["statementWin"] = {
            "week": sw["week"],
            "opponent": sw["opponent"],
            "score": sw["score"],
            "oppScore": sw["oppScore"],
            "margin": round(sw["score"] - sw["oppScore"], 1),
        }

    if wins:
        best_lucky = None
        best_lucky_rank = 0
        for w in wins:
            week_scores = weekly_team_scores.get(w["week"], {})
            if not week_scores:
                continue
            rank = sum(1 for s in week_scores.values() if s > w["score"]) + 1
            if rank > best_lucky_rank:
                best_lucky_rank = rank
                best_lucky = w
        if best_lucky:
            awards["luckyWin"] = {
                "week": best_lucky["week"],
                "score": best_lucky["score"],
                "leagueRank": best_lucky_rank,
                "opponent": best_lucky["opponent"],
                "oppScore": best_lucky["oppScore"],
            }

    if losses:
        best_unlucky = None
        best_unlucky_rank = len(weekly_team_scores.get(1, {})) + 1
        for w in losses:
            week_scores = weekly_team_scores.get(w["week"], {})
            if not week_scores:
                continue
            rank = sum(1 for s in week_scores.values() if s > w["score"]) + 1
            if rank < best_unlucky_rank:
                best_unlucky_rank = rank
                best_unlucky = w
        if best_unlucky:
            awards["unluckyLoss"] = {
                "week": best_unlucky["week"],
                "score": best_unlucky["score"],
                "leagueRank": best_unlucky_rank,
                "opponent": best_unlucky["opponent"],
                "oppScore": best_unlucky["oppScore"],
            }

    return awards


# ---------------------------------------------------------------------------
# Grades
# ---------------------------------------------------------------------------


def compute_grades(weekly_results, trades, pickups, all_play, reg_weeks, draft_grade_override=None):
    def to_grade(score):
        thresholds = [
            (95, "A+"),
            (90, "A"),
            (85, "A-"),
            (80, "B+"),
            (75, "B"),
            (70, "B-"),
            (65, "C+"),
            (60, "C"),
            (55, "C-"),
            (50, "D+"),
            (45, "D"),
        ]
        for threshold, grade in thresholds:
            if score >= threshold:
                return grade
        return "F"

    reg = [w for w in weekly_results if w["week"] <= reg_weeks]
    total_games = len(reg)
    win_count = sum(1 for w in reg if w["result"] == "W")
    win_pct = win_count / total_games if total_games else 0

    if draft_grade_override:
        grade_to_score = {
            "A+": 97,
            "A": 92,
            "A-": 87,
            "B+": 82,
            "B": 77,
            "B-": 72,
            "C+": 67,
            "C": 62,
            "C-": 57,
            "D+": 52,
            "D": 47,
            "F": 30,
        }
        drafting = grade_to_score.get(draft_grade_override, 50)
    else:
        early_wins = sum(1 for w in reg[:4] if w["result"] == "W")
        drafting = 50 + early_wins * 12.5

    trade_net = sum(t.get("net", 0) for t in trades)
    trading = min(100, max(0, 60 + trade_net / 20))

    top_pickup = max((p.get("ptsAfterAdd", 0) for p in pickups), default=0)
    waiver = min(100, max(0, 40 + top_pickup / 10))

    ap_pct = all_play.get("winPct", 0.5)
    luck_diff = win_pct - ap_pct
    luck = min(100, max(0, 50 + luck_diff * 200))

    scores = [w["score"] for w in reg]
    if len(scores) > 1:
        mean = sum(scores) / len(scores)
        std = (sum((s - mean) ** 2 for s in scores) / len(scores)) ** 0.5
        consistency = min(100, max(0, 100 - std / 2))
    else:
        consistency = 50

    overall = drafting * 0.20 + trading * 0.20 + waiver * 0.20 + consistency * 0.20 + (win_pct * 100) * 0.20

    return {
        "drafting": to_grade(drafting),
        "trading": to_grade(trading),
        "waiverWire": to_grade(waiver),
        "luck": to_grade(luck),
        "consistency": to_grade(consistency),
        "overall": to_grade(overall),
    }


# ---------------------------------------------------------------------------
# Team Assembly
# ---------------------------------------------------------------------------


def extract_team(
    league,
    team,
    box_cache,
    activity,
    standings,
    weekly_team_scores,
    reg_weeks,
    total_weeks,
    draft_grades=None,
    replacement_ppg=0.0,
    nba_games=None,
    last_week=None,
):
    last_week = last_week or total_weeks
    tid = team.team_id
    print(f"\n{'=' * 60}")
    print(f"  {team.team_name} (ID: {tid}, last_week={last_week})")
    print(f"{'=' * 60}")

    print("  [ 1/11] Weekly results")
    events = build_events_by_week(tid, activity)
    weekly_results = extract_weekly_results(tid, box_cache, standings, events, last_week)

    print("  [ 2/11] Trades")
    trades = extract_trades(tid, activity, box_cache, last_week, replacement_ppg, nba_games)

    print("  [ 3/11] Waiver pickups")
    pickups = extract_waiver_pickups(tid, activity, box_cache, last_week)

    print("  [ 4/11] Scoring profile")
    scoring_profile = extract_scoring_profile(tid, box_cache, reg_weeks)

    print("  [ 5/11] All-play record")
    all_play = extract_all_play(tid, weekly_team_scores, reg_weeks)

    print("  [ 6/11] Roster heatmap")
    heatmap = extract_roster_heatmap(tid, box_cache, last_week)

    print("  [ 7/11] Points left on bench")
    bench_pts = extract_bench_points(tid, box_cache, weekly_results, last_week)

    print("  [ 8/11] Head-to-head")
    h2h = extract_head_to_head(weekly_results, reg_weeks)

    print("  [ 9/11] Optimal lineup")
    optimal = extract_optimal_lineup(tid, box_cache, last_week)

    print("  [10/11] Awards")
    awards = compute_awards(weekly_results, heatmap, weekly_team_scores, tid, reg_weeks)

    print("  [11/11] Grades")
    team_draft_grade = (draft_grades or {}).get(str(tid), {}).get("grade")
    grades = compute_grades(weekly_results, trades, pickups, all_play, reg_weeks, team_draft_grade)

    reg_results = [w for w in weekly_results if w["week"] <= reg_weeks]

    return {
        "team": {
            "name": team.team_name,
            "manager": get_manager_name(team),
            "record": f"{team.wins}-{team.losses}",
            "seed": team.standing,
            "pointsFor": round(sum(w["score"] for w in reg_results), 1),
            "pointsAgainst": round(sum(w["oppScore"] for w in reg_results), 1),
        },
        "league": {
            "name": league.settings.name,
            "season": f"{YEAR - 1}-{str(YEAR)[2:]}",
            "teams": len(league.teams),
        },
        "weeklyResults": weekly_results,
        "trades": trades,
        "waiverPickups": pickups,
        "scoringProfile": scoring_profile,
        "allPlayRecord": all_play,
        "rosterHeatmap": heatmap,
        "pointsLeftOnBench": bench_pts,
        "headToHead": h2h,
        "optimalLineup": optimal,
        "awards": awards,
        "grades": grades,
    }


# ---------------------------------------------------------------------------
# League-Wide: Trade Aggregation
# ---------------------------------------------------------------------------


def aggregate_league_trades(
    teams,
    activity,
    box_cache,
    total_weeks,
    replacement_ppg=0.0,
    nba_games=None,
    player_totals=None,
    nba_games_total=None,
):
    all_trades = []

    for team in teams:
        tid = team.team_id
        team_trades = extract_trades(
            tid,
            activity,
            box_cache,
            total_weeks,
            replacement_ppg,
            nba_games,
            player_totals=player_totals,
            nba_games_total=nba_games_total,
        )
        for trade in team_trades:
            all_trades.append({**trade, "_team_id": tid, "_team_name": team.team_name})

    seen = set()
    deduped = []
    for trade in all_trades:
        tid = trade["_team_id"]
        partner_name = trade["partner"]
        partner_id = next((t.team_id for t in teams if t.team_name == partner_name), 0)
        canonical = tuple(sorted([tid, partner_id]))
        all_players = frozenset(trade["sent"]) | frozenset(trade["received"])
        key = (trade["week"], canonical, all_players)
        if key in seen:
            continue
        seen.add(key)

        if tid < partner_id:
            team1_id, team1_name = tid, trade["_team_name"]
            team2_id, team2_name = partner_id, partner_name
            team1_sent, team2_sent = trade["sent"], trade["received"]
            team1_pts, team2_pts = trade["sentPtsROS"], trade["receivedPtsROS"]
            team1_stats = trade.get("sentStats", [])
            team2_stats = trade.get("receivedStats", [])
        else:
            team1_id, team1_name = partner_id, partner_name
            team2_id, team2_name = tid, trade["_team_name"]
            team1_sent, team2_sent = trade["received"], trade["sent"]
            team1_pts, team2_pts = trade["receivedPtsROS"], trade["sentPtsROS"]
            team1_stats = trade.get("receivedStats", [])
            team2_stats = trade.get("sentStats", [])

        net = team2_pts - team1_pts
        winner = team1_name if team2_pts > team1_pts else team2_name

        deduped.append(
            {
                "week": trade["week"],
                "team1": team1_name,
                "team1Id": team1_id,
                "team2": team2_name,
                "team2Id": team2_id,
                "team1Sent": team1_sent,
                "team2Sent": team2_sent,
                "team1Stats": team1_stats,
                "team2Stats": team2_stats,
                "team1PtsROS": round(team1_pts, 1),
                "team2PtsROS": round(team2_pts, 1),
                "net": round(abs(net), 1),
                "winner": winner,
                "slotAdjustment": round(trade.get("slotAdjustment", 0), 1),
            }
        )

    deduped.sort(key=lambda t: t["net"], reverse=True)
    return deduped


def _next_free_agency_week(player_name, after_date, activity):
    """Find the week when a player next hits free agency (dropped by any team).

    Returns the drop week, or None if the player stays rostered through season end.
    """
    all_drops = []
    for tid, drops in activity["drops"].items():
        for drop in drops:
            if drop["player"] == player_name and drop["date"] and drop["date"] > after_date:
                all_drops.append(drop["date"])
    if not all_drops:
        return None

    all_adds_after = []
    for tid, adds in activity["adds"].items():
        for add in adds:
            if add["player"] == player_name and add["date"] and add["date"] > after_date:
                all_adds_after.append(add["date"])

    for drop_date in sorted(all_drops):
        readded = any(a > drop_date for a in all_adds_after)
        if not readded:
            return date_to_week(drop_date)
        next_add = min(a for a in all_adds_after if a > drop_date)
        gap_ms = next_add - drop_date
        if gap_ms > 2 * 24 * 60 * 60 * 1000:
            return date_to_week(drop_date)
    return None


def _is_simple_reclaim(player_name, team_id, add_date, activity):
    """True if no other team picked up this player before add_date (a simple draft reclaim)."""
    for other_tid, adds in activity["adds"].items():
        if int(other_tid) == team_id:
            continue
        for a in adds:
            if a["player"] == player_name and a["date"] and a["date"] < add_date:
                return False
    return True


def aggregate_league_pickups(
    teams,
    activity,
    box_cache,
    total_weeks,
    nba_games=None,
    player_totals=None,
    nba_games_total=None,
    display_through_week=None,
    faab=None,
    drafted_names=None,
):
    all_pickups = []
    drafted = drafted_names or {}

    for team in teams:
        tid = team.team_id
        pickups = extract_waiver_pickups(tid, activity, box_cache, total_weeks, max_pickups=None)
        for p in pickups:
            name = p["player"]
            add_date = p["addDate"]
            if name in drafted.get(tid, set()) and _is_simple_reclaim(name, tid, add_date, activity):
                continue

            free_week = _next_free_agency_week(name, add_date or 0, activity)

            if free_week and p["weekAdded"]:
                active_weeks = [
                    wp["week"] for wp in p["weeklyPoints"]
                    if wp["pts"] > 0 and wp["week"] <= free_week
                ]
                pts = sum(wp["pts"] for wp in p["weeklyPoints"] if wp["week"] <= free_week)
                games = sum(nba_games.get(name, {}).get(w, 0) for w in active_weeks) if nba_games else 0
            elif player_totals and p["weekAdded"]:
                pre_pts = _compute_pre_event_points(name, p["weekAdded"], box_cache)
                pts = max(player_totals.get(name, 0) - pre_pts, p["ptsAfterAdd"])
                if nba_games_total and nba_games:
                    pre_gp = _compute_pre_event_games(name, p["weekAdded"], nba_games)
                    games = max(nba_games_total.get(name, 0) - pre_gp, 0)
                else:
                    active_weeks = [wp["week"] for wp in p["weeklyPoints"] if wp["pts"] > 0]
                    games = sum(nba_games.get(name, {}).get(w, 0) for w in active_weeks) if nba_games else 0
            else:
                pts = p["ptsAfterAdd"]
                active_weeks = [wp["week"] for wp in p["weeklyPoints"] if wp["pts"] > 0]
                games = sum(nba_games.get(name, {}).get(w, 0) for w in active_weeks) if nba_games else 0

            if pts < 10:
                continue

            ppg = round(pts / games, 1) if games > 0 else 0
            bid = faab.get((name, tid, p["weekAdded"]), 0) if faab else 0
            all_pickups.append(
                {
                    "player": name,
                    "team": team.team_name,
                    "teamId": tid,
                    "weekAdded": p["weekAdded"],
                    "ptsAfterAdd": round(pts, 1),
                    "gamesPlayed": games,
                    "ppg": ppg,
                    "faabBid": bid,
                }
            )

    if display_through_week is not None:
        all_pickups = [p for p in all_pickups if p["weekAdded"] and p["weekAdded"] <= display_through_week]

    all_pickups.sort(key=lambda p: p["ptsAfterAdd"], reverse=True)
    return all_pickups


# ---------------------------------------------------------------------------
# League-Wide: Draft Analysis with Replacement-Backfill Grading
# ---------------------------------------------------------------------------


def compute_player_nba_games(roster_by_week, total_weeks):
    """Count NBA games played per player per week from daily scoring data.

    Returns {player_name: {week: nba_games_count}}.
    A game is counted when a player has > 0 points in a scoring period.
    """
    result = defaultdict(lambda: defaultdict(int))
    for week in range(1, total_weeks + 1):
        week_data = roster_by_week.get(week, {})
        for _tid, players in week_data.items():
            for name, data in players.items():
                games = sum(1 for pts in data.get("daily_pts", []) if pts > 0)
                result[name][week] = max(result[name][week], games)
    return dict(result)


def build_draft_analysis(league, box_cache, player_totals, total_weeks, nba_games, nba_games_total=None):
    num_teams = len(league.teams)
    draft_picks = []

    for pick in league.draft:
        season_pts = player_totals.get(pick.playerName, 0)
        if nba_games_total and pick.playerName in nba_games_total:
            games = nba_games_total[pick.playerName]
        else:
            player_weeks = nba_games.get(pick.playerName, {})
            games = sum(player_weeks.values())
        ppg = round(season_pts / games, 1) if games > 0 else 0
        overall = (pick.round_num - 1) * num_teams + pick.round_pick

        draft_picks.append(
            {
                "round": pick.round_num,
                "pick": pick.round_pick,
                "overall": overall,
                "player": pick.playerName,
                "team": pick.team.team_name,
                "teamId": pick.team.team_id,
                "seasonPts": season_pts,
                "gamesPlayed": games,
                "ppg": ppg,
            }
        )

    def _active_weeks(player_name):
        pw = nba_games.get(player_name, {})
        observed_active = sum(1 for w in range(1, total_weeks + 1) if pw.get(w, 0) > 0)
        if not nba_games_total:
            return observed_active
        total_gp = nba_games_total.get(player_name, 0)
        observed_gp = sum(pw.values())
        missing_gp = total_gp - observed_gp
        if missing_gp <= 0 or observed_active == 0:
            return observed_active
        avg_gpw = observed_gp / observed_active
        return observed_active + round(missing_gp / avg_gpw) if avg_gpw > 0 else observed_active

    for pick in draft_picks:
        pick["_activeWeeks"] = _active_weeks(pick["player"])

    min_gp = 25
    starter_slots = num_teams * 10
    all_qualified = []
    for name, pts in player_totals.items():
        if pts <= 0:
            continue
        gp = nba_games_total.get(name, 0) if nba_games_total else 0
        if gp < min_gp:
            continue
        all_qualified.append({"name": name, "ppg": round(pts / gp, 1), "gp": gp})

    all_qualified.sort(key=lambda p: p["ppg"], reverse=True)
    replacement_idx = min(starter_slots - 1, len(all_qualified) - 1)
    replacement_ppg = all_qualified[replacement_idx]["ppg"] if replacement_idx >= 0 else 10.0

    total_games = sum(p["gp"] for p in all_qualified[:starter_slots])
    total_active_weeks = sum(_active_weeks(p["name"]) for p in all_qualified[:starter_slots])
    avg_gpw = total_games / total_active_weeks if total_active_weeks > 0 else 3.5
    replacement_fpw = round(replacement_ppg * avg_gpw, 1)

    for pick in draft_picks:
        missed_weeks = total_weeks - pick["_activeWeeks"]
        own_fpw = pick["seasonPts"] / pick["_activeWeeks"] if pick["_activeWeeks"] > 0 else 0
        backfill = min(replacement_fpw, own_fpw)
        pick["adjustedTotal"] = round(pick["seasonPts"] + missed_weeks * backfill, 1)
        del pick["_activeWeeks"]

    by_adjusted = sorted(draft_picks, key=lambda p: p["adjustedTotal"], reverse=True)
    for rank, pick in enumerate(by_adjusted, 1):
        pick["seasonRank"] = rank

    total_picks = len(draft_picks)
    for pick in draft_picks:
        vod = pick["overall"] - pick["seasonRank"]
        pick["valueOverDraft"] = vod
        pct = vod / max(1, total_picks) * 100
        pick["grade"] = _draft_grade(pct)
        pick["label"] = _draft_label(pct)

    team_grades = {}
    teams_picks = defaultdict(list)
    for pick in draft_picks:
        teams_picks[pick["teamId"]].append(pick)
    for tid, picks in teams_picks.items():
        avg_vod = sum(p["valueOverDraft"] for p in picks) / len(picks)
        pct = avg_vod / max(1, total_picks) * 100
        team_grades[str(tid)] = {
            "team": picks[0]["team"],
            "grade": _draft_grade(pct),
            "avgValueOverDraft": round(avg_vod, 1),
        }

    return draft_picks, {"replacementFPW": replacement_fpw, "totalGames": total_weeks}, team_grades


def _draft_grade(pct):
    thresholds = [
        (25, "A+"),
        (18, "A"),
        (12, "A-"),
        (7, "B+"),
        (3, "B"),
        (0, "B-"),
        (-5, "C+"),
        (-10, "C"),
        (-15, "C-"),
        (-22, "D+"),
        (-30, "D"),
    ]
    for threshold, grade in thresholds:
        if pct >= threshold:
            return grade
    return "F"


def _draft_label(pct):
    if pct >= 18:
        return "steal"
    if pct >= 5:
        return "value"
    if pct >= -5:
        return "fair"
    if pct >= -18:
        return "reach"
    return "bust"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def do_fetch(league, total_weeks):
    print("\n[Fetch 1/3] Box scores + roster data...")
    box_cache, roster_by_week = fetch_box_scores(league, total_weeks)

    print("\n[Fetch 2/3] Transactions...")
    raw_activity = fetch_activity(league)
    activity = classify_activity(raw_activity)
    n_trades = len(activity["trades"])
    n_adds = sum(len(v) for v in activity["adds"].values())
    n_drops = sum(len(v) for v in activity["drops"].values())
    print(f"  {len(raw_activity)} entries -> {n_trades} trades, {n_adds} adds, {n_drops} drops")

    print("\n[Fetch 3/4] Roster season totals...")
    roster_totals = fetch_roster_totals(league)
    print(f"  {len(roster_totals)} players")

    print("\n[Fetch 4/4] FAAB bids...")
    faab = fetch_faab(league)
    bids_with_amount = sum(1 for b in faab.values() if b > 0)
    print(f"  {len(faab)} transactions, {bids_with_amount} with nonzero bids")

    save_cache(box_cache, roster_by_week, activity, league, roster_totals, faab)
    return box_cache, roster_by_week, activity, roster_totals, faab


def do_extract(
    league, box_cache, roster_by_week, activity, reg_weeks, total_weeks,
    roster_totals=None, faab=None, team_id=None,
):
    print("\n[Extract 1/4] Standings & scores...")
    standings = compute_standings_by_week(box_cache, league.teams, reg_weeks)
    weekly_scores = collect_weekly_team_scores(box_cache, total_weeks)

    player_totals_box = compute_player_season_totals(box_cache, total_weeks)
    nba_games_by_week = compute_player_nba_games(roster_by_week, total_weeks)

    player_totals = {name: rt["total_points"] for name, rt in roster_totals.items()} if roster_totals else {}
    nba_games_total = {name: rt["gp"] for name, rt in roster_totals.items()} if roster_totals else {}
    for name, pts in player_totals_box.items():
        if name not in player_totals:
            player_totals[name] = pts
    for name, weeks in nba_games_by_week.items():
        if name not in nba_games_total:
            nba_games_total[name] = sum(weeks.values())
    if not player_totals:
        player_totals = player_totals_box

    last_week_map = compute_last_week_by_team(box_cache, total_weeks, reg_weeks)
    final_placement_map = compute_final_placement(box_cache, last_week_map, league.teams, reg_weeks)

    print("\n[Extract 2/4] Draft analysis & league trades...")
    draft_picks, draft_meta, draft_grades = build_draft_analysis(
        league,
        box_cache,
        player_totals,
        total_weeks,
        nba_games_by_week,
        nba_games_total,
    )
    repl_fpw = draft_meta["replacementFPW"]
    league_trades = aggregate_league_trades(
        league.teams,
        activity,
        box_cache,
        total_weeks,
        repl_fpw,
        nba_games_by_week,
        player_totals,
        nba_games_total,
    )
    drafted_by_team = defaultdict(set)
    for pick in league.draft:
        drafted_by_team[pick.team.team_id].add(pick.playerName)

    league_pickups = aggregate_league_pickups(
        league.teams,
        activity,
        box_cache,
        total_weeks,
        nba_games_by_week,
        player_totals=player_totals,
        nba_games_total=nba_games_total,
        display_through_week=reg_weeks,
        faab=faab,
        drafted_names=dict(drafted_by_team),
    )
    print(f"  {len(draft_picks)} picks, {len(league_trades)} trades, {len(league_pickups)} pickups")

    print("\n[Extract 3/4] Teams...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if team_id:
        teams = [t for t in league.teams if t.team_id == team_id]
        if not teams:
            print(f"\nERROR: No team with ID {team_id}. Available:")
            for t in league.teams:
                print(f"  {t.team_id}: {t.team_name}")
            sys.exit(1)
    else:
        teams = league.teams

    all_scoring_profiles = []
    for team in teams:
        last_week = last_week_map.get(team.team_id, reg_weeks)
        try:
            data = extract_team(
                league,
                team,
                box_cache,
                activity,
                standings,
                weekly_scores,
                reg_weeks,
                total_weeks,
                draft_grades,
                repl_fpw,
                nba_games_by_week,
                last_week=last_week,
            )
            all_scoring_profiles.append(data.get("scoringProfile", {}))
            path = OUTPUT_DIR / f"team_{team.team_id}.json"
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  -> {path}")
        except Exception as e:
            print(f"  ERROR extracting {team.team_name}: {e}")
            import traceback

            traceback.print_exc()

    print("\n[Extract 4/4] League metadata...")
    scoring_items = league.settings._raw_scoring_settings.get("scoringItems", [])
    scoring_weights = {}
    for item in scoring_items:
        stat_name = ESPN_STAT_ID_MAP.get(item["statId"], f"stat_{item['statId']}")
        scoring_weights[stat_name] = item["points"]

    league_avg_profile = {}
    if all_scoring_profiles:
        cats = list(all_scoring_profiles[0].keys())
        for cat in cats:
            vals = [p[cat]["pct"] for p in all_scoring_profiles if cat in p]
            league_avg_profile[cat] = round(sum(vals) / len(vals), 3) if vals else 0

    meta = {
        "name": league.settings.name,
        "season": f"{YEAR - 1}-{str(YEAR)[2:]}",
        "scoringType": league.settings.scoring_type,
        "regSeasonWeeks": reg_weeks,
        "totalWeeks": total_weeks,
        "scoringWeights": scoring_weights,
        "lineupConfig": LINEUP_CONFIG,
        "leagueAvgScoringProfile": league_avg_profile,
        "leagueTrades": league_trades,
        "leaguePickups": league_pickups,
        "draftAnalysis": draft_picks,
        "draftMeta": draft_meta,
        "draftGrades": draft_grades,
        "teams": [
            {
                "id": t.team_id,
                "name": t.team_name,
                "manager": get_manager_name(t),
                "record": f"{t.wins}-{t.losses}",
                "standing": t.standing,
                "finalPlacement": final_placement_map.get(t.team_id, t.standing),
                "pointsFor": round(t.points_for, 1),
                "pointsAgainst": round(t.points_against, 1),
            }
            for t in sorted(league.teams, key=lambda t: final_placement_map.get(t.team_id, t.standing))
        ],
    }
    meta_path = OUTPUT_DIR / "league_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nWrote {meta_path}")
    print(f"\nDone! {len(teams)} team file(s) + league_meta.json -> {OUTPUT_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="Fantasy Wrapped — extract league data")
    parser.add_argument("command", nargs="?", choices=["fetch", "extract"], default=None)
    parser.add_argument("--team", type=int, help="Extract only this team ID")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh API fetch")
    args = parser.parse_args()

    if args.command == "fetch" or (args.command is None and (args.no_cache or not cache_exists())):
        league = connect()
        total_weeks = len(league.teams[0].schedule)
        reg_weeks = league.settings.reg_season_count or 18
        print(f"  {reg_weeks} regular-season weeks, {total_weeks} total matchup periods")
        box_cache, roster_by_week, activity, roster_totals, faab = do_fetch(league, total_weeks)
        if args.command == "fetch":
            return
        do_extract(league, box_cache, roster_by_week, activity, reg_weeks, total_weeks, roster_totals, faab, args.team)
    elif args.command == "extract" or (args.command is None and cache_exists()):
        print("Loading from cache...")
        box_cache, roster_by_week, activity, league, total_weeks, roster_totals, faab = load_cache()
        reg_weeks = league.settings.reg_season_count or 18
        print(f"  {reg_weeks} regular-season weeks, {total_weeks} total matchup periods")
        do_extract(league, box_cache, roster_by_week, activity, reg_weeks, total_weeks, roster_totals, faab, args.team)


if __name__ == "__main__":
    main()
