from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def synthetic_4v4() -> pd.DataFrame:
    """Small deterministic fixture; every handle and result is synthetic."""
    strong = ["P01", "P02", "P03", "P04"]
    weak = ["P05", "P06", "P07", "P08"]
    civs_a = ["CivA", "CivB", "CivC", "CivD"]
    civs_b = ["CivE", "CivF", "CivG", "CivH"]
    rows = []
    for match_id in range(1, 25):
        strong_first = match_id % 2 == 0
        team1, team2 = (strong, weak) if strong_first else (weak, strong)
        team1_civs, team2_civs = (civs_a, civs_b) if strong_first else (civs_b, civs_a)
        row = {
            "match_id": match_id,
            "played_at": f"2026-01-{match_id:02d}T20:00:00Z",
            "duration_seconds": 2_400,
            "team1_won": int(strong_first),
        }
        for slot in range(4):
            row[f"team1_player{slot + 1}"] = team1[slot]
            row[f"team2_player{slot + 1}"] = team2[slot]
            row[f"team1_civ{slot + 1}"] = team1_civs[slot]
            row[f"team2_civ{slot + 1}"] = team2_civs[slot]
        rows.append(row)
    return pd.DataFrame(rows)
