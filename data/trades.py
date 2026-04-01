from collections import defaultdict

from helpers import date_to_week
from standings import _compute_pre_event_games, _compute_pre_event_points


def extract_trades(
    team_id,
    activity,
    box_cache,
    total_weeks,
    replacement_ppg=0.0,
    nba_games=None,
    player_totals=None,
    nba_games_total=None,
):
    use_roster_totals = bool(player_totals)
    team_trades = []

    for trade in activity["trades"]:
        sent, received, partner = [], [], None
        for action in trade["actions"]:
            if action["team_id"] == team_id:
                sent.append(action["player"])
            else:
                received.append(action["player"])
                partner = action["team_name"]

        if not sent or not received:
            continue

        trade_week = date_to_week(trade["date"])
        sent_pts, received_pts = 0.0, 0.0
        weekly_breakdown = []
        player_pts = defaultdict(float)
        player_games = defaultdict(int)

        if trade_week:
            sent_set, recv_set = set(sent), set(received)
            all_players = sent_set | recv_set

            if use_roster_totals:
                for name in all_players:
                    pre = _compute_pre_event_points(name, trade_week, box_cache)
                    player_pts[name] = player_totals.get(name, 0) - pre
                sent_pts = sum(player_pts[n] for n in sent_set)
                received_pts = sum(player_pts[n] for n in recv_set)
            else:
                for week in range(trade_week, total_weeks + 1):
                    week_sent, week_recv = 0.0, 0.0
                    week_seen = set()
                    for box in box_cache.get(week, []):
                        for lineup in [box.home_lineup or [], box.away_lineup or []]:
                            for player in lineup:
                                if player.name in all_players:
                                    pts = player.points or 0
                                    player_pts[player.name] += pts
                                    if player.name not in week_seen:
                                        player_games[player.name] += 1
                                        week_seen.add(player.name)
                                if player.name in sent_set:
                                    week_sent += player.points or 0
                                if player.name in recv_set:
                                    week_recv += player.points or 0
                    sent_pts += week_sent
                    received_pts += week_recv
                    weekly_breakdown.append(
                        {
                            "week": week,
                            "sentPts": round(week_sent, 1),
                            "receivedPts": round(week_recv, 1),
                        }
                    )

        def _player_stats(names):
            stats = []
            for name in names:
                pts = player_pts.get(name, 0)
                if use_roster_totals and nba_games_total and trade_week:
                    pre_gp = _compute_pre_event_games(name, trade_week, nba_games)
                    g = nba_games_total.get(name, 0) - pre_gp
                elif nba_games and trade_week:
                    pw = nba_games.get(name, {})
                    g = sum(pw.get(w, 0) for w in range(trade_week, total_weeks + 1))
                else:
                    g = player_games.get(name, 0)
                stats.append(
                    {
                        "player": name,
                        "ptsROS": round(pts, 1),
                        "gamesROS": g,
                        "ppgROS": round(pts / g, 1) if g > 0 else 0,
                    }
                )
            return stats

        spot_diff = len(sent) - len(received)
        slot_adj = 0.0
        if spot_diff != 0 and trade_week and replacement_ppg > 0:
            weeks_remaining = total_weeks - trade_week + 1
            slot_adj = abs(spot_diff) * replacement_ppg * weeks_remaining
            if spot_diff > 0:
                received_pts += slot_adj
            else:
                sent_pts += slot_adj

        team_trades.append(
            {
                "week": trade_week,
                "partner": partner or "Unknown",
                "sent": sent,
                "received": received,
                "sentPtsROS": round(sent_pts, 1),
                "receivedPtsROS": round(received_pts, 1),
                "net": round(received_pts - sent_pts, 1),
                "slotAdjustment": round(slot_adj, 1),
                "sentStats": _player_stats(sent),
                "receivedStats": _player_stats(received),
                "weeklyBreakdown": weekly_breakdown,
            }
        )

    result = _deduplicate_trades(team_trades)
    result.sort(key=lambda t: t["week"] or 0)
    return result


def _deduplicate_trades(trades):
    def trade_key(t):
        return (t["partner"], frozenset(t["sent"]), frozenset(t["received"]))

    def mirror_key(t):
        return (t["partner"], frozenset(t["received"]), frozenset(t["sent"]))

    seen_keys = {}
    for i, t in enumerate(trades):
        k = trade_key(t)
        mk = mirror_key(t)
        if mk in seen_keys:
            prev_idx = seen_keys.pop(mk)
            trades[prev_idx] = None
            trades[i] = None
        elif k in seen_keys:
            prev_idx = seen_keys[k]
            seen_keys[k] = i
            trades[prev_idx] = None
        else:
            seen_keys[k] = i

    return [t for t in trades if t is not None]


def aggregate_league_trades(
    teams,
    activity,
    box_cache,
    total_weeks,
    replacement_ppg=0.0,
    nba_games=None,
    player_totals=None,
    nba_games_total=None,
):
    all_trades = []

    for team in teams:
        tid = team.team_id
        team_trades = extract_trades(
            tid,
            activity,
            box_cache,
            total_weeks,
            replacement_ppg,
            nba_games,
            player_totals=player_totals,
            nba_games_total=nba_games_total,
        )
        for trade in team_trades:
            all_trades.append({**trade, "_team_id": tid, "_team_name": team.team_name})

    seen = set()
    deduped = []
    for trade in all_trades:
        tid = trade["_team_id"]
        partner_name = trade["partner"]
        partner_id = next((t.team_id for t in teams if t.team_name == partner_name), 0)
        canonical = tuple(sorted([tid, partner_id]))
        all_players = frozenset(trade["sent"]) | frozenset(trade["received"])
        key = (trade["week"], canonical, all_players)
        if key in seen:
            continue
        seen.add(key)

        if tid < partner_id:
            team1_id, team1_name = tid, trade["_team_name"]
            team2_id, team2_name = partner_id, partner_name
            team1_sent, team2_sent = trade["sent"], trade["received"]
            team1_pts, team2_pts = trade["sentPtsROS"], trade["receivedPtsROS"]
            team1_stats = trade.get("sentStats", [])
            team2_stats = trade.get("receivedStats", [])
        else:
            team1_id, team1_name = partner_id, partner_name
            team2_id, team2_name = tid, trade["_team_name"]
            team1_sent, team2_sent = trade["received"], trade["sent"]
            team1_pts, team2_pts = trade["receivedPtsROS"], trade["sentPtsROS"]
            team1_stats = trade.get("receivedStats", [])
            team2_stats = trade.get("sentStats", [])

        net = team2_pts - team1_pts
        winner = team1_name if team2_pts > team1_pts else team2_name

        deduped.append(
            {
                "week": trade["week"],
                "team1": team1_name,
                "team1Id": team1_id,
                "team2": team2_name,
                "team2Id": team2_id,
                "team1Sent": team1_sent,
                "team2Sent": team2_sent,
                "team1Stats": team1_stats,
                "team2Stats": team2_stats,
                "team1PtsROS": round(team1_pts, 1),
                "team2PtsROS": round(team2_pts, 1),
                "net": round(abs(net), 1),
                "winner": winner,
                "slotAdjustment": round(trade.get("slotAdjustment", 0), 1),
            }
        )

    deduped.sort(key=lambda t: t["net"], reverse=True)
    return deduped
