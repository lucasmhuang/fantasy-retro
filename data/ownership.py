from dataclasses import dataclass

from helpers import date_to_week


@dataclass(frozen=True, slots=True)
class OwnershipPeriod:
    team_id: int
    add_week: int | None
    add_date: int | None
    drop_week: int | None
    drop_date: int | None
    acquired_via: str
    departed_via: str | None


class OwnershipTimeline:
    def __init__(self, player_name: str, periods: list[OwnershipPeriod]):
        self.player_name = player_name
        self.periods = sorted(periods, key=lambda p: p.add_date or 0)

    def drop_week_for_team(self, team_id: int, after_date: int) -> int | None:
        for p in self.periods:
            if p.team_id != team_id or p.departed_via != "drop":
                continue
            if p.drop_date and p.drop_date > after_date:
                return p.drop_week
        return None

    def next_free_agency_after(self, after_date: int) -> int | None:
        for p in self.periods:
            if not p.drop_date or p.drop_date <= after_date or p.departed_via != "drop":
                continue
            next_add = next(
                (q.add_date for q in self.periods if q.add_date and q.add_date > p.drop_date),
                None,
            )
            if not next_add or (next_add - p.drop_date > 2 * 86_400_000):
                return p.drop_week
        return None

    def is_simple_reclaim(self, team_id: int, add_date: int) -> bool:
        return not any(
            p.team_id != team_id and p.add_date and p.add_date < add_date
            for p in self.periods
            if p.acquired_via == "add"
        )

    def is_lm_roster_move(self, add_date: int, team_id: int) -> bool:
        if not add_date:
            return False
        one_day_ms = 24 * 60 * 60 * 1000
        return any(
            p.team_id == team_id
            and p.departed_via == "drop"
            and p.drop_date
            and abs(add_date - p.drop_date) < one_day_ms
            for p in self.periods
        )


def build_ownership_timelines(activity: dict) -> dict[str, OwnershipTimeline]:
    events_by_player: dict[str, list[dict]] = {}

    for tid, adds in activity["adds"].items():
        tid = int(tid)
        for add in adds:
            name = add["player"]
            events_by_player.setdefault(name, []).append({"type": "add", "team_id": tid, "date": add["date"]})

    for tid, drops in activity["drops"].items():
        tid = int(tid)
        for drop in drops:
            name = drop["player"]
            events_by_player.setdefault(name, []).append({"type": "drop", "team_id": tid, "date": drop["date"]})

    timelines = {}
    for name, events in events_by_player.items():
        events.sort(key=lambda e: e["date"] or 0)
        periods = _build_periods(events)
        timelines[name] = OwnershipTimeline(name, periods)

    return timelines


def _build_periods(events: list[dict]) -> list[OwnershipPeriod]:
    periods: list[OwnershipPeriod] = []
    open_adds: dict[int, dict] = {}

    for event in events:
        tid = event["team_id"]
        if event["type"] == "add":
            open_adds[tid] = event
        elif event["type"] == "drop":
            add_event = open_adds.pop(tid, None)
            periods.append(
                OwnershipPeriod(
                    team_id=tid,
                    add_week=date_to_week(add_event["date"]) if add_event else None,
                    add_date=add_event["date"] if add_event else None,
                    drop_week=date_to_week(event["date"]),
                    drop_date=event["date"],
                    acquired_via="add" if add_event else "draft",
                    departed_via="drop",
                )
            )

    for tid, add_event in open_adds.items():
        periods.append(
            OwnershipPeriod(
                team_id=tid,
                add_week=date_to_week(add_event["date"]),
                add_date=add_event["date"],
                drop_week=None,
                drop_date=None,
                acquired_via="add",
                departed_via=None,
            )
        )

    return periods
