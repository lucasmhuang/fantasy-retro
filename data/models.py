class TeamRef:
    def __init__(self, team_id, team_name):
        self.team_id = team_id
        self.team_name = team_name


class PlayerData:
    def __init__(self, name, points, points_breakdown, slot_position, position="", eligible_slot_ids=None):
        self.name = name
        self.points = points
        self.points_breakdown = points_breakdown
        self.slot_position = slot_position
        self.position = position
        self.eligibleSlots = eligible_slot_ids or []


class MatchupData:
    def __init__(self, home_team, away_team, home_score, away_score, home_lineup, away_lineup):
        self.home_team = home_team
        self.away_team = away_team
        self.home_score = home_score
        self.away_score = away_score
        self.home_lineup = home_lineup
        self.away_lineup = away_lineup


class CachedTeam:
    def __init__(self, d):
        self.team_id = d["id"]
        self.team_name = d["name"]
        self.owners = d.get("owners", [])
        self.wins = d["wins"]
        self.losses = d["losses"]
        self.standing = d["standing"]
        self.points_for = d["pointsFor"]
        self.points_against = d["pointsAgainst"]
        self.schedule = [None] * d.get("schedule", 21)


class CachedDraftPick:
    def __init__(self, d, teams_by_id):
        self.round_num = d["round"]
        self.round_pick = d["pick"]
        self.playerName = d["playerName"]
        self.team = teams_by_id.get(d["teamId"], TeamRef(d["teamId"], d.get("teamName", "")))


class CachedLeague:
    def __init__(self, info):
        self.teams = [CachedTeam(t) for t in info["teams"]]
        teams_by_id = {t.team_id: t for t in self.teams}
        self.draft = [CachedDraftPick(p, teams_by_id) for p in info["draft"]]
        self.settings = type(
            "Settings",
            (),
            {
                "name": info["name"],
                "scoring_type": info["scoringType"],
                "reg_season_count": info["regSeasonWeeks"],
                "_raw_scoring_settings": {"scoringItems": info["scoringSettings"]},
            },
        )()
