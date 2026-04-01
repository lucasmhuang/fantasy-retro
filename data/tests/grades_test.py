from grades import _rank_with_clustering, compute_league_grades


class TestRankWithClustering:
    def test_basic_ranking(self):
        values = {1: 100, 2: 80, 3: 60}
        grades = _rank_with_clustering(values)
        assert grades[1] == "A+"
        assert grades[3] in ("A-", "B+", "B", "B-", "C+", "C", "C-")

    def test_empty_input(self):
        assert _rank_with_clustering({}) == {}

    def test_no_clustering_with_zero_std(self):
        values = {1: 100, 2: 100, 3: 100}
        grades = _rank_with_clustering(values)
        assert grades[1] == "A+"

    def test_clustering_within_threshold(self):
        values = {1: 100, 2: 99, 3: 50}
        grades = _rank_with_clustering(values)
        assert grades[1] == grades[2] == "A+"

    def test_twelve_teams(self):
        values = {i: 100 - i * 10 for i in range(1, 13)}
        grades = _rank_with_clustering(values)
        assert grades[1] == "A+"
        assert grades[12] == "F"


class TestComputeLeagueGrades:
    def test_returns_all_categories(self):
        tids = list(range(1, 13))
        all_values = {
            "drafting": {t: t * 10 for t in tids},
            "trading": {t: t * 5 for t in tids},
            "waiverWire": {t: t * 8 for t in tids},
            "luck": {t: 0.5 - t * 0.04 for t in tids},
            "coaching": {t: 0.9 - t * 0.05 for t in tids},
        }
        placement = {t: t for t in tids}
        grades = compute_league_grades(all_values, placement)

        assert set(grades.keys()) == set(tids)
        for tid in tids:
            assert "drafting" in grades[tid]
            assert "trading" in grades[tid]
            assert "waiverWire" in grades[tid]
            assert "luck" in grades[tid]
            assert "coaching" in grades[tid]
            assert "overall" in grades[tid]
