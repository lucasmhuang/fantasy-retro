from collections import defaultdict

from helpers import find_team_in_matchup


def compute_last_week_by_team(box_cache, total_weeks, reg_weeks):
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
    pts = 0.0
    for week in range(1, before_week):
        for box in box_cache.get(week, []):
            for lineup in [box.home_lineup or [], box.away_lineup or []]:
                for player in lineup:
                    if player.name == player_name:
                        pts += player.points or 0
    return pts


def _compute_pre_event_games(player_name, before_week, nba_games_by_week):
    pw = nba_games_by_week.get(player_name, {})
    return sum(pw.get(w, 0) for w in range(1, before_week))


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


def compute_player_nba_games(roster_by_week, total_weeks):
    result = defaultdict(lambda: defaultdict(int))
    for week in range(1, total_weeks + 1):
        week_data = roster_by_week.get(week, {})
        for _tid, players in week_data.items():
            for name, data in players.items():
                games = sum(1 for pts in data.get("daily_pts", []) if pts > 0)
                result[name][week] = max(result[name][week], games)
    return dict(result)
