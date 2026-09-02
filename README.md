# Rage Forest Ratings

An independent, outcome-only skill model for the Age of Empires II **Rage Forest** 4v4
community. The public site explains the method and publishes a searchable leaderboard:

**https://oldxavier.github.io/rageforest-ratings/**

## What is public

- A reusable ridge Bradley–Terry implementation for eight-player team games
- A synthetic 4v4 test fixture and documented input schema
- The named top 500 with exact rating, plus the remaining 265 alphabetically with only shared
  position/rating ranges
- One-SD uncertainty, games, win rate, own-team average, opponent-team average, and full-lobby
  average for all 765 players
- The methodology, corrections, and negative experiments in an approachable static article

## What is intentionally not public

Raw match histories, platform/profile IDs, identity and alias decisions, crawler lists, API
payloads, crowd membership, private diagnostics, and video-production files remain in a private
source repository. A fresh public history prevents deleted private data from surviving in Git.

The published leaderboard can be audited as an output boundary, but it cannot reconstruct the
private corpus or identity graph. See [docs/DATA_BOUNDARY.md](docs/DATA_BOUNDARY.md).

## Use the generic model

```python
import pandas as pd
from rageforest_ratings import fit_ratings

matches = pd.read_csv("your_matches.csv")
result = fit_ratings(matches)
print(result.ratings.head(20))
```

Each row is one 4v4 match. Teams must have four distinct handles and `team1_won` must be 0 or 1.
Civilisation columns are optional; timestamps and durations enable recency weighting and the
short-game rule. The complete contract is in [docs/INPUT_SCHEMA.md](docs/INPUT_SCHEMA.md).

```bash
uv sync
uv run ruff check .
uv run pytest -q
uv build
```

## Model and snapshot

The September 2026 release is model v17 (`config_hash d5e91c5131f8`) over corpus snapshot
`8cf276648edd`: 87,813 eligible matches from 2022-03-06 through 2026-08-30, 9,699 observed
handles, and 765 ranked players.

This package exposes the generic player/civilisation ridge model. The published v17 fit also
uses private identity resolution, community pooling, duration grading, evidence-age correction,
and a cross-community eligibility gate; those decisions are described on the site without
publishing the data needed to reverse the identity graph.

## License and attribution

Code is MIT licensed. Published ratings and prose are provided for community discussion; do not
present uncertainty-bearing estimates as facts about a person. Age of Empires II is a trademark
of Microsoft. This project is unofficial and is not endorsed by Microsoft or Forgotten Empires.
