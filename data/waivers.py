from helpers import date_to_week, find_team_in_matchup


def extract_waiver_pickups(team_id, activity, box_cache, total_weeks, max_pickups=10, timelines=None):
    team_adds = sorted(activity["adds"].get(team_id, []), key=lambda a: a["date"] or 0)

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
    for add in filtered_adds:
        name = add["player"]
        add_week = date_to_week(add["date"])
        if timelines and name in timelines:
            drop_week = timelines[name].drop_week_for_team(team_id, add["date"])
        else:
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

            if timelines and name in timelines:
                free_week = timelines[name].next_free_agency_after(add_date or 0)
            else:
                free_week = _next_free_agency_week(name, add_date or 0, activity)

            cap = display_through_week or total_weeks

            if free_week and p["weekAdded"]:
                effective_cap = min(free_week, cap)
                active_weeks = [wp["week"] for wp in p["weeklyPoints"] if wp["pts"] > 0 and wp["week"] <= effective_cap]
                pts = sum(wp["pts"] for wp in p["weeklyPoints"] if wp["week"] <= effective_cap)
                games = sum(nba_games.get(name, {}).get(w, 0) for w in active_weeks) if nba_games else 0
            elif player_totals and p["weekAdded"]:
                pts = sum(wp["pts"] for wp in p["weeklyPoints"] if wp["week"] <= cap)
                active_weeks = [wp["week"] for wp in p["weeklyPoints"] if wp["pts"] > 0 and wp["week"] <= cap]
                games = sum(nba_games.get(name, {}).get(w, 0) for w in active_weeks) if nba_games else 0
            else:
                active_weeks = [wp["week"] for wp in p["weeklyPoints"] if wp["pts"] > 0 and wp["week"] <= cap]
                pts = sum(wp["pts"] for wp in p["weeklyPoints"] if wp["week"] <= cap)
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


def _find_team_drop_week(player_name, add_date, team_id, activity):
    best = None
    for drop in activity["drops"].get(team_id, []):
        if drop["player"] == player_name and drop["date"] and drop["date"] > add_date:
            if best is None or drop["date"] < best:
                best = drop["date"]
    return date_to_week(best) if best else None


def _next_free_agency_week(player_name, after_date, activity):
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
    for other_tid, adds in activity["adds"].items():
        if int(other_tid) == team_id:
            continue
        for a in adds:
            if a["player"] == player_name and a["date"] and a["date"] < add_date:
                return False
    return True
