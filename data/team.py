from collections import defaultdict

from constants import BENCH_SLOTS, YEAR
from helpers import date_to_week, find_team_in_matchup, get_manager_name
from lineup import extract_bench_points, extract_optimal_lineup
from trades import extract_trades
from waivers import extract_waiver_pickups


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
    pre_grades=None,
    final_placement=None,
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
    grades = pre_grades or {}

    reg_results = [w for w in weekly_results if w["week"] <= reg_weeks]

    return {
        "team": {
            "name": team.team_name,
            "manager": get_manager_name(team),
            "record": f"{team.wins}-{team.losses}",
            "seed": team.standing,
            "finalPlacement": final_placement,
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
