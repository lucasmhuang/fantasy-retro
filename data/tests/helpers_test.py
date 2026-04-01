from datetime import datetime, timezone

from helpers import date_to_week, find_team_in_matchup, get_manager_name
from models import MatchupData, PlayerData, TeamRef


class TestDateToWeek:
    def test_week_1_start(self):
        dt = datetime(2025, 10, 21, 12, 0, tzinfo=timezone.utc)
        epoch_ms = int(dt.timestamp() * 1000)
        assert date_to_week(epoch_ms) == 1

    def test_week_1_end(self):
        dt = datetime(2025, 10, 26, 23, 0, tzinfo=timezone.utc)
        epoch_ms = int(dt.timestamp() * 1000)
        assert date_to_week(epoch_ms) == 1

    def test_week_18(self):
        dt = datetime(2026, 2, 25, 12, 0, tzinfo=timezone.utc)
        epoch_ms = int(dt.timestamp() * 1000)
        assert date_to_week(epoch_ms) == 18

    def test_week_21_playoff(self):
        dt = datetime(2026, 3, 18, 12, 0, tzinfo=timezone.utc)
        epoch_ms = int(dt.timestamp() * 1000)
        assert date_to_week(epoch_ms) == 21

    def test_none_input(self):
        assert date_to_week(None) is None

    def test_zero_input(self):
        assert date_to_week(0) is None

    def test_out_of_range(self):
        dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        epoch_ms = int(dt.timestamp() * 1000)
        assert date_to_week(epoch_ms) is None


class TestFindTeamInMatchup:
    def _make_box(self):
        return MatchupData(
            home_team=TeamRef(1, "Team A"),
            away_team=TeamRef(2, "Team B"),
            home_score=100.0,
            away_score=95.0,
            home_lineup=[PlayerData("P1", 50, {}, "PG")],
            away_lineup=[PlayerData("P2", 45, {}, "SG")],
        )

    def test_home_team(self):
        box = self._make_box()
        lineup, score, opp, opp_score = find_team_in_matchup(box, 1)
        assert len(lineup) == 1
        assert score == 100.0
        assert opp.team_id == 2
        assert opp_score == 95.0

    def test_away_team(self):
        box = self._make_box()
        lineup, score, opp, opp_score = find_team_in_matchup(box, 2)
        assert score == 95.0
        assert opp.team_id == 1

    def test_missing_team(self):
        box = self._make_box()
        lineup, score, opp, opp_score = find_team_in_matchup(box, 99)
        assert lineup is None


class TestGetManagerName:
    def test_normal_owner(self):
        team = type("T", (), {"owners": [{"firstName": "John", "lastName": "Doe"}]})()
        assert get_manager_name(team) == "John Doe"

    def test_no_owners(self):
        team = type("T", (), {"owners": []})()
        assert get_manager_name(team) == "Unknown"

    def test_missing_attr(self):
        team = type("T", (), {})()
        assert get_manager_name(team) == "Unknown"
