import argparse
import json
import sys
import traceback
from collections import defaultdict

from cache import cache_exists, load_cache, save_cache
from constants import DRAFT_GRADE_SCORES, ESPN_STAT_ID_MAP, LINEUP_CONFIG, OUTPUT_DIR, YEAR
from draft import build_draft_analysis
from fetch import classify_activity, connect, fetch_activity, fetch_box_scores, fetch_faab, fetch_roster_totals
from grades import compute_league_grades
from helpers import get_manager_name
from lineup import extract_optimal_lineup
from ownership import build_ownership_timelines
from standings import (
    collect_weekly_team_scores,
    compute_final_placement,
    compute_last_week_by_team,
    compute_player_nba_games,
    compute_player_season_totals,
    compute_standings_by_week,
)
from team import extract_all_play, extract_team, extract_weekly_results
from trades import aggregate_league_trades, extract_trades
from waivers import aggregate_league_pickups, extract_waiver_pickups


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
    league,
    box_cache,
    roster_by_week,
    activity,
    reg_weeks,
    total_weeks,
    roster_totals=None,
    faab=None,
    team_id=None,
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

    timelines = build_ownership_timelines(activity)

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
        timelines=timelines,
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

    all_efficiencies = {}
    all_trade_nets = {}
    all_waiver_totals = {}
    all_luck_diffs = {}
    all_draft_scores = {}
    for t in league.teams:
        tid = t.team_id
        ol = extract_optimal_lineup(tid, box_cache, reg_weeks)
        all_efficiencies[tid] = ol.get("efficiency", 0.0)
        t_trades = extract_trades(
            tid,
            activity,
            box_cache,
            reg_weeks,
            repl_fpw,
            nba_games_by_week,
        )
        all_trade_nets[tid] = sum(tr.get("net", 0) for tr in t_trades)
        t_pickups = extract_waiver_pickups(tid, activity, box_cache, reg_weeks)
        all_waiver_totals[tid] = sum(p.get("ptsAfterAdd", 0) for p in t_pickups)
        ap = extract_all_play(tid, weekly_scores, reg_weeks)
        reg = [w for w in extract_weekly_results(tid, box_cache, standings, {}, reg_weeks) if w["week"] <= reg_weeks]
        win_pct = sum(1 for w in reg if w["result"] == "W") / len(reg) if reg else 0
        all_luck_diffs[tid] = win_pct - ap.get("winPct", 0.5)
        team_draft_grade = (draft_grades or {}).get(str(tid), {}).get("grade")
        if team_draft_grade:
            all_draft_scores[tid] = DRAFT_GRADE_SCORES.get(team_draft_grade, 50)
        else:
            early_wins = sum(1 for w in reg[:4] if w["result"] == "W")
            all_draft_scores[tid] = 50 + early_wins * 12.5

    league_grades = compute_league_grades(
        {
            "drafting": all_draft_scores,
            "trading": all_trade_nets,
            "waiverWire": all_waiver_totals,
            "luck": all_luck_diffs,
            "coaching": all_efficiencies,
        },
        final_placement_map,
    )

    for tid_str, tg in draft_grades.items():
        tid = int(tid_str)
        if tid in league_grades:
            tg["grade"] = league_grades[tid]["drafting"]

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
                pre_grades=league_grades.get(team.team_id, {}),
                final_placement=final_placement_map.get(team.team_id),
            )
            all_scoring_profiles.append(data.get("scoringProfile", {}))
            path = OUTPUT_DIR / f"team_{team.team_id}.json"
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  -> {path}")
        except Exception as e:
            print(f"  ERROR extracting {team.team_name}: {e}")
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
        "tradeGrades": {
            str(tid): {
                "team": next(t.team_name for t in league.teams if t.team_id == tid),
                "grade": league_grades.get(tid, {}).get("trading", "C"),
                "netPts": round(net, 1),
            }
            for tid, net in all_trade_nets.items()
        },
        "waiverGrades": {
            str(tid): {
                "team": next(t.team_name for t in league.teams if t.team_id == tid),
                "grade": league_grades.get(tid, {}).get("waiverWire", "C"),
                "totalPts": round(total, 1),
            }
            for tid, total in all_waiver_totals.items()
        },
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
