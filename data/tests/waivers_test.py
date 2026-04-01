from unittest.mock import patch

from models import MatchupData, PlayerData
from waivers import _next_add_week, _player_week_pts, extract_waiver_pickups

WEEK_MS = 100_000_000


def _mock_date_to_week(epoch_ms):
    if not epoch_ms:
        return None
    return epoch_ms // WEEK_MS


def W(n):
    return n * WEEK_MS


def _player(name, pts):
    return PlayerData(name, pts, {}, "PG")


def _matchup(home_id, away_id, home_lineup, away_lineup):
    class Team:
        def __init__(self, tid):
            self.team_id = tid

    return MatchupData(Team(home_id), Team(away_id), 0, 0, home_lineup, away_lineup)


def _box_cache_from_weeks(week_data):
    cache = {}
    for week, matchups in week_data.items():
        cache[week] = [_matchup(m[0], m[1], m[2], m[3]) for m in matchups]
    return cache


@patch("waivers.date_to_week", side_effect=_mock_date_to_week)
class TestExtractWaiverPickups:
    def test_basic_pickup_full_ros(self, _mock):
        activity = {
            "adds": {1: [{"player": "Player X", "date": W(2)}]},
            "drops": {},
        }
        box_cache = _box_cache_from_weeks(
            {
                2: [(1, 2, [_player("Player X", 30)], [])],
                3: [(1, 2, [_player("Player X", 25)], [])],
            }
        )
        pickups = extract_waiver_pickups(1, activity, box_cache, total_weeks=3)
        assert len(pickups) == 1
        assert pickups[0]["player"] == "Player X"
        assert pickups[0]["ptsAfterAdd"] == 55.0

    def test_trade_through_credits_all_lineups(self, _mock):
        activity = {
            "adds": {1: [{"player": "Player X", "date": W(2)}]},
            "drops": {},
        }
        box_cache = _box_cache_from_weeks(
            {
                2: [(1, 2, [_player("Player X", 30)], [])],
                3: [(1, 2, [_player("Player X", 25)], [])],
                4: [(1, 2, [], [_player("Player X", 40)])],
                5: [(3, 4, [], []), (1, 2, [], []), (5, 6, [_player("Player X", 35)], [])],
            }
        )
        pickups = extract_waiver_pickups(1, activity, box_cache, total_weeks=5)
        assert len(pickups) == 1
        assert pickups[0]["ptsAfterAdd"] == 130.0

    def test_credit_ends_at_other_team_pickup(self, _mock):
        activity = {
            "adds": {
                1: [{"player": "Player X", "date": W(2)}],
                2: [{"player": "Player X", "date": W(5)}],
            },
            "drops": {},
        }
        box_cache = _box_cache_from_weeks(
            {
                2: [(1, 3, [_player("Player X", 30)], [])],
                3: [(1, 3, [_player("Player X", 25)], [])],
                4: [(1, 3, [_player("Player X", 20)], [])],
                5: [(2, 3, [_player("Player X", 50)], [])],
                6: [(2, 3, [_player("Player X", 45)], [])],
            }
        )
        pickups_team1 = extract_waiver_pickups(1, activity, box_cache, total_weeks=6)
        assert len(pickups_team1) == 1
        assert pickups_team1[0]["ptsAfterAdd"] == 75.0

        pickups_team2 = extract_waiver_pickups(2, activity, box_cache, total_weeks=6)
        assert len(pickups_team2) == 1
        assert pickups_team2[0]["ptsAfterAdd"] == 95.0

    def test_same_team_readd_no_double_count(self, _mock):
        activity = {
            "adds": {
                1: [
                    {"player": "Player X", "date": W(2)},
                    {"player": "Player X", "date": W(5)},
                ],
            },
            "drops": {1: [{"player": "Player X", "date": W(4)}]},
        }
        box_cache = _box_cache_from_weeks(
            {
                2: [(1, 2, [_player("Player X", 30)], [])],
                3: [(1, 2, [_player("Player X", 25)], [])],
                5: [(1, 2, [_player("Player X", 40)], [])],
                6: [(1, 2, [_player("Player X", 35)], [])],
            }
        )
        pickups = extract_waiver_pickups(1, activity, box_cache, total_weeks=6)
        assert len(pickups) == 2
        first = next(p for p in pickups if p["weekAdded"] == 2)
        second = next(p for p in pickups if p["weekAdded"] == 5)
        assert first["ptsAfterAdd"] == 55.0
        assert second["ptsAfterAdd"] == 75.0

    def test_lm_correction_not_counted(self, _mock):
        one_hour_ms = 3600_000
        activity = {
            "adds": {
                1: [
                    {"player": "Player X", "date": W(2)},
                    {"player": "Player X", "date": W(5) + one_hour_ms},
                ],
            },
            "drops": {1: [{"player": "Player X", "date": W(5)}]},
        }
        box_cache = _box_cache_from_weeks(
            {
                2: [(1, 2, [_player("Player X", 30)], [])],
                3: [(1, 2, [_player("Player X", 25)], [])],
                5: [(1, 2, [_player("Player X", 20)], [])],
                6: [(1, 2, [_player("Player X", 15)], [])],
            }
        )
        pickups = extract_waiver_pickups(1, activity, box_cache, total_weeks=6)
        assert len(pickups) == 1
        assert pickups[0]["weekAdded"] == 2
        assert pickups[0]["ptsAfterAdd"] == 90.0


@patch("waivers.date_to_week", side_effect=_mock_date_to_week)
class TestPlayerWeekPts:
    def test_finds_player_on_any_team(self, _mock):
        box_cache = _box_cache_from_weeks(
            {
                3: [(1, 2, [], [_player("Player X", 42)])],
            }
        )
        assert _player_week_pts("Player X", 3, box_cache) == 42

    def test_returns_zero_when_not_rostered(self, _mock):
        box_cache = _box_cache_from_weeks(
            {
                3: [(1, 2, [_player("Other", 10)], [])],
            }
        )
        assert _player_week_pts("Player X", 3, box_cache) == 0


@patch("waivers.date_to_week", side_effect=_mock_date_to_week)
class TestNextAddWeek:
    def test_finds_next_other_team_add(self, _mock):
        all_adds = {
            1: [{"player": "Player X", "date": W(2)}],
            2: [{"player": "Player X", "date": W(5)}],
        }
        assert _next_add_week("Player X", W(2), all_adds, exclude_team_id=1) == 5

    def test_ignores_same_team(self, _mock):
        all_adds = {
            1: [
                {"player": "Player X", "date": W(2)},
                {"player": "Player X", "date": W(5)},
            ],
        }
        assert _next_add_week("Player X", W(2), all_adds, exclude_team_id=1) is None

    def test_returns_none_when_no_future_add(self, _mock):
        all_adds = {1: [{"player": "Player X", "date": W(2)}]}
        assert _next_add_week("Player X", W(2), all_adds, exclude_team_id=1) is None
