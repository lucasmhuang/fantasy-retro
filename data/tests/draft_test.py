from draft import _draft_grade, _draft_label


class TestDraftGrade:
    def test_a_plus(self):
        assert _draft_grade(25) == "A+"
        assert _draft_grade(30) == "A+"

    def test_a(self):
        assert _draft_grade(18) == "A"
        assert _draft_grade(24) == "A"

    def test_f(self):
        assert _draft_grade(-35) == "F"

    def test_boundary_b(self):
        assert _draft_grade(3) == "B"
        assert _draft_grade(2.9) == "B-"


class TestDraftLabel:
    def test_steal(self):
        assert _draft_label(18) == "steal"
        assert _draft_label(25) == "steal"

    def test_value(self):
        assert _draft_label(5) == "value"
        assert _draft_label(17) == "value"

    def test_fair(self):
        assert _draft_label(0) == "fair"
        assert _draft_label(-4) == "fair"

    def test_reach(self):
        assert _draft_label(-5.1) == "reach"
        assert _draft_label(-17) == "reach"

    def test_bust(self):
        assert _draft_label(-18.1) == "bust"
        assert _draft_label(-30) == "bust"
