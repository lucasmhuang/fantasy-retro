from ownership import OwnershipPeriod, OwnershipTimeline, build_ownership_timelines


class TestOwnershipTimeline:
    def _make_timeline(self, periods):
        return OwnershipTimeline("Test Player", periods)

    def test_drop_week_for_team(self):
        tl = self._make_timeline(
            [
                OwnershipPeriod(
                    team_id=1,
                    add_week=5,
                    add_date=100,
                    drop_week=10,
                    drop_date=200,
                    acquired_via="add",
                    departed_via="drop",
                ),
            ]
        )
        assert tl.drop_week_for_team(1, 50) == 10
        assert tl.drop_week_for_team(1, 300) is None
        assert tl.drop_week_for_team(2, 50) is None

    def test_next_free_agency_after(self):
        tl = self._make_timeline(
            [
                OwnershipPeriod(
                    team_id=1,
                    add_week=1,
                    add_date=100,
                    drop_week=5,
                    drop_date=500_000,
                    acquired_via="add",
                    departed_via="drop",
                ),
            ]
        )
        assert tl.next_free_agency_after(0) == 5

    def test_next_free_agency_readded_quickly(self):
        drop_date = 1_000_000
        readd_date = drop_date + 1_000
        tl = self._make_timeline(
            [
                OwnershipPeriod(
                    team_id=1,
                    add_week=1,
                    add_date=100,
                    drop_week=5,
                    drop_date=drop_date,
                    acquired_via="add",
                    departed_via="drop",
                ),
                OwnershipPeriod(
                    team_id=2,
                    add_week=5,
                    add_date=readd_date,
                    drop_week=None,
                    drop_date=None,
                    acquired_via="add",
                    departed_via=None,
                ),
            ]
        )
        assert tl.next_free_agency_after(0) is None

    def test_next_free_agency_readded_with_gap(self):
        drop_date = 1_000_000
        readd_date = drop_date + 3 * 86_400_000
        tl = self._make_timeline(
            [
                OwnershipPeriod(
                    team_id=1,
                    add_week=1,
                    add_date=100,
                    drop_week=5,
                    drop_date=drop_date,
                    acquired_via="add",
                    departed_via="drop",
                ),
                OwnershipPeriod(
                    team_id=2,
                    add_week=6,
                    add_date=readd_date,
                    drop_week=None,
                    drop_date=None,
                    acquired_via="add",
                    departed_via=None,
                ),
            ]
        )
        assert tl.next_free_agency_after(0) == 5

    def test_is_simple_reclaim_true(self):
        tl = self._make_timeline(
            [
                OwnershipPeriod(
                    team_id=1,
                    add_week=1,
                    add_date=100,
                    drop_week=5,
                    drop_date=500,
                    acquired_via="add",
                    departed_via="drop",
                ),
                OwnershipPeriod(
                    team_id=1,
                    add_week=6,
                    add_date=600,
                    drop_week=None,
                    drop_date=None,
                    acquired_via="add",
                    departed_via=None,
                ),
            ]
        )
        assert tl.is_simple_reclaim(1, 600) is True

    def test_is_simple_reclaim_false(self):
        tl = self._make_timeline(
            [
                OwnershipPeriod(
                    team_id=1,
                    add_week=1,
                    add_date=100,
                    drop_week=5,
                    drop_date=500,
                    acquired_via="add",
                    departed_via="drop",
                ),
                OwnershipPeriod(
                    team_id=2,
                    add_week=5,
                    add_date=550,
                    drop_week=6,
                    drop_date=650,
                    acquired_via="add",
                    departed_via="drop",
                ),
                OwnershipPeriod(
                    team_id=1,
                    add_week=7,
                    add_date=700,
                    drop_week=None,
                    drop_date=None,
                    acquired_via="add",
                    departed_via=None,
                ),
            ]
        )
        assert tl.is_simple_reclaim(1, 700) is False

    def test_is_lm_roster_move(self):
        tl = self._make_timeline(
            [
                OwnershipPeriod(
                    team_id=1,
                    add_week=5,
                    add_date=100,
                    drop_week=5,
                    drop_date=100 + 3600_000,
                    acquired_via="add",
                    departed_via="drop",
                ),
            ]
        )
        assert tl.is_lm_roster_move(100 + 7200_000, 1) is True
        assert tl.is_lm_roster_move(100 + 7200_000, 2) is False


class TestBuildOwnershipTimelines:
    def test_basic_add_drop(self):
        activity = {
            "adds": {1: [{"player": "Player A", "date": 100}]},
            "drops": {1: [{"player": "Player A", "date": 500}]},
        }
        timelines = build_ownership_timelines(activity)
        assert "Player A" in timelines
        tl = timelines["Player A"]
        assert len(tl.periods) == 1
        assert tl.periods[0].team_id == 1
        assert tl.periods[0].departed_via == "drop"

    def test_still_rostered(self):
        activity = {
            "adds": {1: [{"player": "Player A", "date": 100}]},
            "drops": {},
        }
        timelines = build_ownership_timelines(activity)
        tl = timelines["Player A"]
        assert len(tl.periods) == 1
        assert tl.periods[0].departed_via is None

    def test_multiple_teams(self):
        activity = {
            "adds": {
                1: [{"player": "Player A", "date": 100}],
                2: [{"player": "Player A", "date": 600}],
            },
            "drops": {
                1: [{"player": "Player A", "date": 500}],
            },
        }
        timelines = build_ownership_timelines(activity)
        tl = timelines["Player A"]
        assert len(tl.periods) == 2
