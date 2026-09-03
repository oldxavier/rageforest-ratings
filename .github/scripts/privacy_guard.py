"""Fail CI if private-source artefacts or sensitive schemas become tracked."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_NAMES = {
    "corpus",
    "identities.toml",
    "players.toml",
    "match_players.csv",
    "matches.csv",
}
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".wav", ".mp3"}
SENSITIVE_SCHEMA = re.compile(
    r'(?i)(?:profile|steam|discord|match|player)[_-]?id["\']?\s*[:,=]'
)
LOCAL_PATH = re.compile(r"/Users/[^/\s]+/")
PUBLIC_PLAYER_KEYS = {
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
PUBLIC_CIV_KEYS = {
    "rank",
    "civilization",
    "rating_effect",
    "all_games",
    "all_win_rate",
    "top100_games",
    "top100_win_rate",
}


def tracked_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    return [ROOT / item.decode() for item in output.split(b"\0") if item]


def main() -> None:
    errors = []
    for path in tracked_files():
        relative = path.relative_to(ROOT)
        if not path.exists():
            continue
        if relative == Path(".github/scripts/privacy_guard.py"):
            continue
        lowered_parts = {part.lower() for part in relative.parts}
        if lowered_parts & FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden tracked path: {relative}")
            continue
        if path.suffix.lower() not in {".py", ".md", ".toml", ".json", ".csv", ".html", ".js", ".css", ".yml"}:
            continue
        text = path.read_text(errors="replace")
        if LOCAL_PATH.search(text):
            errors.append(f"local home path in {relative}")
        if path.suffix.lower() in {".csv", ".json"} and SENSITIVE_SCHEMA.search(text):
            errors.append(f"sensitive ID-like schema in {relative}")

    ratings_path = ROOT / "site/data/ratings.json"
    payload = json.loads(ratings_path.read_text())
    if len(payload.get("players", [])) != 765:
        errors.append("site/data/ratings.json must contain exactly 765 named players")
    for index, player in enumerate(payload.get("players", []), 1):
        if set(player) != PUBLIC_PLAYER_KEYS:
            errors.append(f"unexpected player fields at public row {index}: {sorted(player)}")
            break

    civ_path = ROOT / "site/data/civilizations.json"
    civ_payload = json.loads(civ_path.read_text())
    if len(civ_payload.get("civilizations", [])) != 53:
        errors.append("site/data/civilizations.json must contain exactly 53 civilizations")
    for index, civilization in enumerate(civ_payload.get("civilizations", []), 1):
        if set(civilization) != PUBLIC_CIV_KEYS:
            errors.append(
                f"unexpected civilization fields at public row {index}: "
                f"{sorted(civilization)}"
            )
            break

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"privacy guard passed across {len(tracked_files())} tracked files")


if __name__ == "__main__":
    main()
