from collections import defaultdict


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
