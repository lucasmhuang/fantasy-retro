from constants import RANK_GRADES


def _rank_with_clustering(values_by_id, threshold_pct=0.25, max_cluster=3):
    if not values_by_id:
        return {}
    vals = list(values_by_id.values())
    mean = sum(vals) / len(vals)
    std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 if len(vals) > 1 else 0
    threshold = threshold_pct * std

    sorted_teams = sorted(values_by_id.items(), key=lambda x: x[1], reverse=True)

    grades = {}
    grade_idx = 0
    cluster_anchor = sorted_teams[0][1]
    cluster_size = 1

    for i, (tid, value) in enumerate(sorted_teams):
        if i == 0:
            grades[tid] = RANK_GRADES[0]
            continue
        in_cluster = threshold > 0 and abs(value - cluster_anchor) <= threshold and cluster_size < max_cluster
        if in_cluster:
            grades[tid] = RANK_GRADES[grade_idx]
            cluster_size += 1
        else:
            grade_idx = min(grade_idx + 1, len(RANK_GRADES) - 1)
            grades[tid] = RANK_GRADES[grade_idx]
            cluster_anchor = value
            cluster_size = 1

    return grades


def compute_league_grades(all_values, final_placement_map):
    grade_categories = ["drafting", "trading", "waiverWire", "luck", "coaching"]
    tids = list(next(iter(all_values.values())).keys())

    all_grades = {tid: {} for tid in tids}
    all_ranks = {tid: {} for tid in tids}

    for cat in grade_categories:
        cat_grades = _rank_with_clustering(all_values[cat])
        sorted_tids = sorted(tids, key=lambda t: all_values[cat][t], reverse=True)
        for rank, tid in enumerate(sorted_tids):
            all_ranks[tid][cat] = rank + 1
        for tid in tids:
            all_grades[tid][cat] = cat_grades[tid]

    overall_cats = [c for c in grade_categories if c != "luck"]
    overall_scores = {}
    for tid in tids:
        cat_rank_sum = sum(all_ranks[tid][c] for c in overall_cats)
        placement = final_placement_map.get(tid, (len(tids) + 1) // 2)
        overall_scores[tid] = -(cat_rank_sum + placement) / (len(overall_cats) + 1)

    overall_grades = _rank_with_clustering(overall_scores)
    for tid in tids:
        all_grades[tid]["overall"] = overall_grades[tid]

    return all_grades
