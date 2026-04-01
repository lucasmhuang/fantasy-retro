from models import MatchupData, PlayerData, TeamRef
from standings import (
    _compute_pre_event_games,
    _compute_pre_event_points,
    collect_weekly_team_scores,
    compute_player_season_totals,
    compute_standings_by_week,
)


def _make_box(h_id, a_id, h_score, a_score):
    return MatchupData(
        home_team=TeamRef(h_id, f"Team {h_id}"),
        away_team=TeamRef(a_id, f"Team {a_id}"),
        home_score=h_score,
        away_score=a_score,
        home_lineup=[PlayerData("H_Player", h_score, {}, "PG")],
        away_lineup=[PlayerData("A_Player", a_score, {}, "PG")],
    )


class TestComputeStandingsByWeek:
    def test_two_teams_two_weeks(self):
        teams = [TeamRef(1, "A"), TeamRef(2, "B")]
        box_cache = {
            1: [_make_box(1, 2, 100, 90)],
            2: [_make_box(1, 2, 80, 95)],
        }
        standings = compute_standings_by_week(box_cache, teams, 2)
        assert standings[1][1] == 1
        assert standings[1][2] == 2
        assert standings[2][1] in (1, 2)


class TestCollectWeeklyTeamScores:
    def test_basic(self):
        box_cache = {1: [_make_box(1, 2, 100, 90)]}
        scores = collect_weekly_team_scores(box_cache, 1)
        assert scores[1][1] == 100.0
        assert scores[1][2] == 90.0


class TestComputePlayerSeasonTotals:
    def test_sums_across_weeks(self):
        p = PlayerData("Player1", 50, {}, "PG")
        box_cache = {
            1: [MatchupData(TeamRef(1, "A"), TeamRef(2, "B"), 100, 90, [p], [])],
            2: [MatchupData(TeamRef(1, "A"), TeamRef(2, "B"), 100, 90, [PlayerData("Player1", 30, {}, "PG")], [])],
        }
        totals = compute_player_season_totals(box_cache, 2)
        assert totals["Player1"] == 80.0


class TestComputePreEventPoints:
    def test_sums_before_week(self):
        p1 = PlayerData("Player1", 50, {}, "PG")
        p2 = PlayerData("Player1", 30, {}, "PG")
        box_cache = {
            1: [MatchupData(TeamRef(1, "A"), TeamRef(2, "B"), 100, 90, [p1], [])],
            2: [MatchupData(TeamRef(1, "A"), TeamRef(2, "B"), 100, 90, [p2], [])],
            3: [MatchupData(TeamRef(1, "A"), TeamRef(2, "B"), 100, 90, [PlayerData("Player1", 20, {}, "PG")], [])],
        }
        assert _compute_pre_event_points("Player1", 3, box_cache) == 80.0
        assert _compute_pre_event_points("Player1", 1, box_cache) == 0.0


class TestComputePreEventGames:
    def test_sums_before_week(self):
        games = {"Player1": {1: 3, 2: 4, 3: 2}}
        assert _compute_pre_event_games("Player1", 3, games) == 7
        assert _compute_pre_event_games("Player1", 1, games) == 0
        assert _compute_pre_event_games("Unknown", 3, games) == 0
