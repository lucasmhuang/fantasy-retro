from trades import _deduplicate_trades


class TestDeduplicateTrades:
    def test_no_duplicates(self):
        trades = [
            {"partner": "Team B", "sent": ["P1"], "received": ["P2"]},
            {"partner": "Team C", "sent": ["P3"], "received": ["P4"]},
        ]
        result = _deduplicate_trades(trades)
        assert len(result) == 2

    def test_exact_duplicate(self):
        trades = [
            {"partner": "Team B", "sent": ["P1"], "received": ["P2"]},
            {"partner": "Team B", "sent": ["P1"], "received": ["P2"]},
        ]
        result = _deduplicate_trades(trades)
        assert len(result) == 1

    def test_mirror_cancellation(self):
        trades = [
            {"partner": "Team B", "sent": ["P1"], "received": ["P2"]},
            {"partner": "Team B", "sent": ["P2"], "received": ["P1"]},
        ]
        result = _deduplicate_trades(trades)
        assert len(result) == 0
