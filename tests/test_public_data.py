from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "rank",
    "handle",
    "rating",
    "uncertainty",
    "games",
    "win_rate",
    "team_average_rating",
    "opponent_team_average_rating",
    "average_lobby_rating",
}
CIV_ALLOWED = {
    "rank",
    "civilization",
    "rating_effect",
    "all_games",
    "all_win_rate",
    "top100_games",
    "top100_win_rate",
}


def test_public_export_is_exact_and_consistent() -> None:
    payload = json.loads((ROOT / "site/data/ratings.json").read_text())
    players = payload["players"]
    meta = payload["meta"]

    assert len(players) == meta["named_players"] == 765
    assert meta["ranked_players"] == 765
    assert meta["last_refreshed"] == "Sunday, 30 August 2026"
    assert [player["rank"] for player in players[:500]] == list(range(1, 501))
    assert {player["rank"] for player in players[500:]} == {"501–765"}
    assert [player["handle"].casefold() for player in players[500:]] == sorted(
        player["handle"].casefold() for player in players[500:]
    )
    assert {player["rating"] for player in players[500:]} == {"7xx–14xx"}
    assert all(set(player) == ALLOWED for player in players)
    assert len({player["handle"] for player in players}) == 765

    with (ROOT / "site/data/ratings_765.csv").open(newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 765
    assert set(csv_rows[0]) == ALLOWED
    assert [row["handle"] for row in csv_rows] == [player["handle"] for player in players]


def test_public_export_contains_no_identity_or_match_fields() -> None:
    payload = json.loads((ROOT / "site/data/ratings.json").read_text())
    rendered = json.dumps(payload["players"]).lower()

    for forbidden in ("profile_id", "steam_id", "match_id", "alias", "circle", "crowd"):
        assert forbidden not in rendered


def test_civilization_export_is_complete_and_consistent() -> None:
    payload = json.loads((ROOT / "site/data/civilizations.json").read_text())
    civilizations = payload["civilizations"]

    assert len(civilizations) == 53
    assert [civilization["rank"] for civilization in civilizations] == list(range(1, 54))
    assert all(set(civilization) == CIV_ALLOWED for civilization in civilizations)
    assert len({civilization["civilization"] for civilization in civilizations}) == 53
    assert all(civilization["all_games"] >= civilization["top100_games"] > 0
               for civilization in civilizations)
    assert all(0 <= civilization["all_win_rate"] <= 100 for civilization in civilizations)
    assert all(0 <= civilization["top100_win_rate"] <= 100 for civilization in civilizations)

    with (ROOT / "site/data/civilizations.csv").open(newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 53
    assert set(csv_rows[0]) == CIV_ALLOWED
    assert [row["civilization"] for row in csv_rows] == [
        civilization["civilization"] for civilization in civilizations
    ]
