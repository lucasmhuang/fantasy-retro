from helpers import date_to_week


def extract_waiver_pickups(team_id, activity, box_cache, total_weeks, max_pickups=10, timelines=None):
    all_adds = activity["adds"]
    team_adds = sorted(all_adds.get(team_id, []), key=lambda a: a["date"] or 0)

    filtered_adds = []
    for add in team_adds:
        add_week = date_to_week(add["date"])
        if add_week and add_week >= total_weeks:
            continue
        name = add["player"]
        if timelines and name in timelines:
            if timelines[name].is_lm_roster_move(add["date"], team_id):
                continue
        elif _is_lm_roster_move(name, add["date"], team_id, activity):
            continue
        filtered_adds.append(add)

    pickups = []
    for i, add in enumerate(filtered_adds):
        name = add["player"]
        add_week = date_to_week(add["date"])
        next_other = _next_add_week(name, add["date"], all_adds, team_id)
        next_same = None
        for future in filtered_adds[i + 1 :]:
            if future["player"] == name:
                next_same = date_to_week(future["date"])
                break
        candidates = [w for w in (next_other, next_same) if w]
        end_week = (min(candidates) - 1) if candidates else total_weeks
        pts = 0.0
        weekly_points = []

        if add_week:
            for week in range(add_week, end_week + 1):
                week_pts = _player_week_pts(name, week, box_cache)
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
    timelines=None,
):
    all_pickups = []
    drafted = drafted_names or {}

    for team in teams:
        tid = team.team_id
        pickups = extract_waiver_pickups(tid, activity, box_cache, total_weeks, max_pickups=None, timelines=timelines)
        for p in pickups:
            name = p["player"]
            add_date = p["addDate"]
            if name in drafted.get(tid, set()):
                if timelines and name in timelines:
                    if timelines[name].is_simple_reclaim(tid, add_date):
                        continue
                elif _is_simple_reclaim(name, tid, add_date, activity):
                    continue

            cap = display_through_week or total_weeks
            pts = sum(wp["pts"] for wp in p["weeklyPoints"] if wp["week"] <= cap)
            active_weeks = [wp["week"] for wp in p["weeklyPoints"] if wp["pts"] > 0 and wp["week"] <= cap]
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


def _is_lm_roster_move(player_name, add_date, team_id, activity):
    if not add_date:
        return False
    one_day_ms = 24 * 60 * 60 * 1000
    for drop in activity["drops"].get(team_id, []):
        if drop["player"] == player_name and drop["date"]:
            if abs(add_date - drop["date"]) < one_day_ms:
                return True
    return False


def _player_week_pts(name, week, box_cache):
    for box in box_cache.get(week, []):
        for lineup in (box.home_lineup or [], box.away_lineup or []):
            for player in lineup:
                if player.name == name:
                    return player.points or 0
    return 0


def _next_add_week(player_name, after_date, all_adds, exclude_team_id):
    best = None
    for tid, adds in all_adds.items():
        if int(tid) == exclude_team_id:
            continue
        for add in adds:
            if add["player"] == player_name and add["date"] and add["date"] > after_date:
                if best is None or add["date"] < best:
                    best = add["date"]
    return date_to_week(best) if best else None


def _is_simple_reclaim(player_name, team_id, add_date, activity):
    for other_tid, adds in activity["adds"].items():
        if int(other_tid) == team_id:
            continue
        for a in adds:
            if a["player"] == player_name and a["date"] and a["date"] < add_date:
                return False
    return True
