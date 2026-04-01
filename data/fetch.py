import json as _json
import sys
from collections import defaultdict

from constants import BENCH_SLOTS, ESPN_S2, LEAGUE_ID, SWID, YEAR
from helpers import _retry, date_to_week
from models import MatchupData, PlayerData, TeamRef


def connect():
    from espn_api.basketball import League

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


def fetch_roster_totals(league):
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


def fetch_box_scores(league, total_weeks):
    sp_ranges = {week: [int(sp) for sp in sps] for week, sps in league.matchup_ids.items()}

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

    total_sps = sum(len(sps) for week, sps in sp_ranges.items() if week <= total_weeks)
    print(f"  Phase 2: Roster data ({total_sps} scoring periods)...")

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
    final_sp = league.finalScoringPeriod
    all_txns = []
    for sp in range(1, final_sp + 1):
        if sp % 20 == 0 or sp == 1:
            print(f"    {sp}/{final_sp}...", end="\r")
        params = {"view": "mTransactions2", "scoringPeriodId": sp}
        filters = {"transactions": {"filterType": {"value": ["WAIVER", "FREEAGENT"]}}}
        headers = {"x-fantasy-filter": _json.dumps(filters)}
        try:
            data = _retry(lambda p=params, h=headers: league.espn_request.league_get(params=p, headers=h))
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
