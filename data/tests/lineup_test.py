from lineup import compute_optimal_lineup
from models import MatchupData, PlayerData, TeamRef


class TestComputeOptimalLineup:
    def _make_box_cache(self, players):
        box = MatchupData(
            home_team=TeamRef(1, "Team A"),
            away_team=TeamRef(2, "Team B"),
            home_score=100.0,
            away_score=90.0,
            home_lineup=players,
            away_lineup=[],
        )
        return {1: [box]}

    def test_already_optimal(self):
        players = [
            PlayerData("P1", 50, {}, "G", eligible_slot_ids=["G", "UT"]),
            PlayerData("P2", 40, {}, "G", eligible_slot_ids=["G", "UT"]),
            PlayerData("P3", 30, {}, "G", eligible_slot_ids=["G", "UT"]),
            PlayerData("P4", 20, {}, "F", eligible_slot_ids=["F", "UT"]),
            PlayerData("P5", 15, {}, "F", eligible_slot_ids=["F", "UT"]),
            PlayerData("P6", 10, {}, "F", eligible_slot_ids=["F", "UT"]),
            PlayerData("P7", 8, {}, "C", eligible_slot_ids=["C", "F/C", "UT"]),
            PlayerData("P8", 5, {}, "F/C", eligible_slot_ids=["F/C", "UT"]),
            PlayerData("P9", 3, {}, "UT", eligible_slot_ids=["G", "F", "UT"]),
            PlayerData("P10", 2, {}, "UT", eligible_slot_ids=["G", "F", "UT"]),
            PlayerData("Bench1", 1, {}, "BE", eligible_slot_ids=["G", "UT"]),
        ]
        cache = self._make_box_cache(players)
        optimal, actual = compute_optimal_lineup(1, cache, 1)
        assert optimal >= actual

    def test_bench_better_than_starter(self):
        players = [
            PlayerData("Starter", 10, {}, "G", eligible_slot_ids=["G", "UT"]),
            PlayerData("Starter2", 10, {}, "G", eligible_slot_ids=["G", "UT"]),
            PlayerData("Starter3", 10, {}, "G", eligible_slot_ids=["G", "UT"]),
            PlayerData("Starter4", 10, {}, "F", eligible_slot_ids=["F", "UT"]),
            PlayerData("Starter5", 10, {}, "F", eligible_slot_ids=["F", "UT"]),
            PlayerData("Starter6", 10, {}, "F", eligible_slot_ids=["F", "UT"]),
            PlayerData("Starter7", 10, {}, "C", eligible_slot_ids=["C", "F/C", "UT"]),
            PlayerData("Starter8", 10, {}, "F/C", eligible_slot_ids=["F/C", "UT"]),
            PlayerData("Starter9", 10, {}, "UT", eligible_slot_ids=["G", "F", "UT"]),
            PlayerData("Starter10", 1, {}, "UT", eligible_slot_ids=["G", "F", "UT"]),
            PlayerData("BenchStar", 50, {}, "BE", eligible_slot_ids=["G", "UT"]),
        ]
        cache = self._make_box_cache(players)
        optimal, actual = compute_optimal_lineup(1, cache, 1)
        assert optimal > actual

    def test_empty_week(self):
        optimal, actual = compute_optimal_lineup(1, {}, 1)
        assert optimal == 0.0
        assert actual == 0.0
