from constants import ADJUSTED_WEEKS, BENCH_SLOTS, LINEUP_CONFIG
from helpers import find_team_in_matchup


def _week_has_adjustment(team_id, week):
    return (team_id, week) in ADJUSTED_WEEKS


def extract_bench_points(team_id, box_cache, weekly_results, reg_weeks):
    all_misplays = []

    loss_margins = {}
    for w in weekly_results:
        if w["result"] == "L" and w["week"] <= reg_weeks:
            loss_margins[w["week"]] = round(w["oppScore"] - w["score"], 1)

    for week in range(1, reg_weeks + 1):
        if _week_has_adjustment(team_id, week):
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


def compute_optimal_lineup(team_id, box_cache, week):
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
        if _week_has_adjustment(team_id, week):
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
