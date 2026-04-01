import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LEAGUE_ID = int(os.getenv("ESPN_LEAGUE_ID", "0"))
YEAR = int(os.getenv("ESPN_YEAR", "2026"))
ESPN_S2 = os.getenv("ESPN_S2", "")
SWID = os.getenv("ESPN_SWID", "")
OUTPUT_DIR = Path(__file__).parent.parent / "public" / "data"
CACHE_DIR = Path(__file__).parent / "cache"

MATCHUP_DATES = [
    (datetime(2025, 10, 21, tzinfo=timezone.utc), datetime(2025, 10, 26, tzinfo=timezone.utc)),
    (datetime(2025, 10, 27, tzinfo=timezone.utc), datetime(2025, 11, 2, tzinfo=timezone.utc)),
    (datetime(2025, 11, 3, tzinfo=timezone.utc), datetime(2025, 11, 9, tzinfo=timezone.utc)),
    (datetime(2025, 11, 10, tzinfo=timezone.utc), datetime(2025, 11, 16, tzinfo=timezone.utc)),
    (datetime(2025, 11, 17, tzinfo=timezone.utc), datetime(2025, 11, 23, tzinfo=timezone.utc)),
    (datetime(2025, 11, 24, tzinfo=timezone.utc), datetime(2025, 11, 30, tzinfo=timezone.utc)),
    (datetime(2025, 12, 1, tzinfo=timezone.utc), datetime(2025, 12, 7, tzinfo=timezone.utc)),
    (datetime(2025, 12, 8, tzinfo=timezone.utc), datetime(2025, 12, 14, tzinfo=timezone.utc)),
    (datetime(2025, 12, 15, tzinfo=timezone.utc), datetime(2025, 12, 21, tzinfo=timezone.utc)),
    (datetime(2025, 12, 22, tzinfo=timezone.utc), datetime(2025, 12, 28, tzinfo=timezone.utc)),
    (datetime(2025, 12, 29, tzinfo=timezone.utc), datetime(2026, 1, 4, tzinfo=timezone.utc)),
    (datetime(2026, 1, 5, tzinfo=timezone.utc), datetime(2026, 1, 11, tzinfo=timezone.utc)),
    (datetime(2026, 1, 12, tzinfo=timezone.utc), datetime(2026, 1, 18, tzinfo=timezone.utc)),
    (datetime(2026, 1, 19, tzinfo=timezone.utc), datetime(2026, 1, 25, tzinfo=timezone.utc)),
    (datetime(2026, 1, 26, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc)),
    (datetime(2026, 2, 2, tzinfo=timezone.utc), datetime(2026, 2, 8, tzinfo=timezone.utc)),
    (datetime(2026, 2, 9, tzinfo=timezone.utc), datetime(2026, 2, 22, tzinfo=timezone.utc)),
    (datetime(2026, 2, 23, tzinfo=timezone.utc), datetime(2026, 3, 1, tzinfo=timezone.utc)),
    (datetime(2026, 3, 2, tzinfo=timezone.utc), datetime(2026, 3, 8, tzinfo=timezone.utc)),
    (datetime(2026, 3, 9, tzinfo=timezone.utc), datetime(2026, 3, 15, tzinfo=timezone.utc)),
    (datetime(2026, 3, 16, tzinfo=timezone.utc), datetime(2026, 3, 22, tzinfo=timezone.utc)),
]

BENCH_SLOTS = frozenset({"BE", "Bench", "BN", "IR"})

ADJUSTED_WEEKS = frozenset(
    {
        (5, 2),
        (7, 2),
        (3, 3),
        (5, 3),
        (6, 3),
        (1, 4),
        (5, 4),
        (6, 4),
        (2, 5),
        (5, 5),
        (6, 5),
        (11, 5),
        (5, 6),
        (6, 6),
        (5, 7),
        (9, 7),
        (1, 8),
        (6, 8),
        (9, 8),
        (1, 9),
        (4, 9),
        (8, 9),
        (11, 9),
        (1, 10),
        (5, 10),
        (6, 10),
        (8, 10),
        (9, 10),
        (1, 11),
        (5, 11),
        (11, 11),
        (2, 12),
        (2, 13),
        (2, 14),
        (6, 14),
        (9, 14),
        (1, 15),
        (6, 15),
    }
)

ESPN_STAT_ID_MAP = {
    0: "PTS",
    1: "BLK",
    2: "STL",
    3: "AST",
    6: "REB",
    11: "TO",
    13: "FGM",
    14: "FGA",
    15: "FTM",
    16: "FTA",
    17: "3PM",
    19: "OREB",
    20: "DREB",
    28: "MPG",
    40: "MIN",
    42: "GS",
}

SLOT_ID_MAP = {
    0: "PG",
    1: "SG",
    2: "SF",
    3: "PF",
    4: "C",
    5: "G",
    6: "F",
    7: "SG/SF",
    8: "G/F",
    9: "PF/C",
    10: "F/C",
    11: "UT",
    12: "BE",
    13: "IR",
}

LINEUP_CONFIG = {"C": 1, "G": 3, "F": 3, "F/C": 1, "UT": 2}

RANK_GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]

DRAFT_GRADE_SCORES = {
    "A+": 97,
    "A": 92,
    "A-": 87,
    "B+": 82,
    "B": 77,
    "B-": 72,
    "C+": 67,
    "C": 62,
    "C-": 57,
    "D+": 52,
    "D": 47,
    "F": 30,
}
