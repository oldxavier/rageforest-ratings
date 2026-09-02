"""Create the strict public boundary from the private frozen v17 table."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

MODEL_VERSION = "v17"
CONFIG_HASH = "d5e91c5131f8"
CORPUS_SNAPSHOT = "8cf276648edd"
CORPUS_FIRST = "2022-03-06"
CORPUS_LAST = "2026-08-30"
ELIGIBLE_MATCHES = 87_813
OBSERVED_PLAYERS = 9_699
RANKED_PLAYERS = 765
EXACT_RANKS = 500
PUBLIC_NAMED = RANKED_PLAYERS
TAIL_RATING_RANGE = "7xx–14xx"
INPUT_COLUMNS = {"rank", "player", "rating", "sd", "games", "win_rate", "days_idle", "config_hash"}
OUTPUT_COLUMNS = ["rank", "handle", "rating", "uncertainty", "games", "win_rate", "activity"]
FORBIDDEN_OUTPUT_TOKENS = {
    "id",
    "alias",
    "circle",
    "crowd",
    "teammate",
    "opponent",
    "match",
    "steam",
    "profile",
}


def activity_bucket(days_idle: int) -> str:
    if days_idle <= 14:
        return "last 2 weeks"
    if days_idle <= 30:
        return "15–30 days"
    if days_idle <= 60:
        return "31–60 days"
    return "61–100 days"


def export(source: Path, json_output: Path, csv_output: Path) -> None:
    frame = pd.read_csv(source)
    missing = INPUT_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"private table is missing columns: {', '.join(sorted(missing))}")
    if set(frame["config_hash"].astype(str)) != {CONFIG_HASH}:
        raise ValueError("private table config hash does not match the published model")

    # The frozen table uses rank 0, rather than null, for players who fail an eligibility gate.
    ranked = frame[frame["rank"] > 0].copy()
    ranked["rank"] = ranked["rank"].astype(int)
    ranked = ranked.sort_values("rank")
    if ranked["rank"].tolist() != list(range(1, RANKED_PLAYERS + 1)):
        raise ValueError(f"expected exactly ranks 1–{RANKED_PLAYERS}")

    exact = ranked.iloc[:EXACT_RANKS].copy()
    public_exact = pd.DataFrame(
        {
            "rank": exact["rank"].astype(int),
            "handle": exact["player"].astype(str),
            "rating": exact["rating"].round().astype(int),
            "uncertainty": exact["sd"].round().astype(int),
            "games": exact["games"].astype(int),
            "win_rate": exact["win_rate"].round(1),
            "activity": exact["days_idle"].astype(int).map(activity_bucket),
        }
    )
    tail = ranked.iloc[EXACT_RANKS:].sort_values("player", key=lambda s: s.str.casefold())
    if tail["rating"].min() < 700 or tail["rating"].max() >= 1_500:
        raise ValueError("the declared lower-ladder rating range no longer covers every player")
    public_tail = pd.DataFrame(
        {
            "rank": "501–765",
            "handle": tail["player"].astype(str),
            "rating": TAIL_RATING_RANGE,
            "uncertainty": tail["sd"].round().astype(int),
            "games": tail["games"].astype(int),
            "win_rate": tail["win_rate"].round(1),
            "activity": tail["days_idle"].astype(int).map(activity_bucket),
        }
    )
    public = pd.concat([public_exact, public_tail], ignore_index=True)
    if list(public.columns) != OUTPUT_COLUMNS or len(public) != PUBLIC_NAMED:
        raise AssertionError("public named export changed shape")
    lowered = {column.lower() for column in public.columns}
    if any(token in column for token in FORBIDDEN_OUTPUT_TOKENS for column in lowered):
        raise AssertionError("a sensitive-looking field crossed the public boundary")
    if public["handle"].str.contains(r"^\s*$", regex=True).any() or public["handle"].duplicated().any():
        raise ValueError("public handles must be unique and non-empty")

    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    payload = {
        "meta": {
            "model_version": MODEL_VERSION,
            "config_hash": CONFIG_HASH,
            "corpus_snapshot": CORPUS_SNAPSHOT,
            "corpus_first": CORPUS_FIRST,
            "corpus_last": CORPUS_LAST,
            "eligible_matches": ELIGIBLE_MATCHES,
            "observed_players": OBSERVED_PLAYERS,
            "ranked_players": RANKED_PLAYERS,
            "named_players": PUBLIC_NAMED,
            "exact_ranks": EXACT_RANKS,
            "source_table_sha256": source_sha256,
            "fields": {
                "rank": "Exact for 1–500; lower players share the 501–765 range.",
                "handle": "Display handle after private identity resolution.",
                "rating": "Exact for 1–500; the shared full lower-ladder range below rank 500.",
                "uncertainty": "One standard deviation, in rating points.",
                "games": "Eligible games represented in the fit.",
                "win_rate": "Raw win percentage in eligible games.",
                "activity": "Coarse days-since-last-game bucket; all ranked players are within 100 days.",
            },
        },
        "players": public.to_dict(orient="records"),
    }

    json_output.parent.mkdir(parents=True, exist_ok=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    public.to_csv(csv_output, index=False, lineterminator="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="private rageforest_rating_v17.csv")
    parser.add_argument("--json", type=Path, default=Path("site/data/ratings.json"))
    parser.add_argument("--csv", type=Path, default=Path("site/data/ratings_765.csv"))
    args = parser.parse_args()
    export(args.source, args.json, args.csv)


if __name__ == "__main__":
    main()
