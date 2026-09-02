# Public data boundary

The repository publishes enough to inspect the released rankings without exposing a replayable
record of where and with whom named people played.

## Included

- Ranks 1–500: handle, exact rank and rating, one-SD uncertainty, games, win rate, and coarse activity
- The remaining 265 handles in alphabetical order: shared position `501–765`, shared rating range
  `7xx–14xx`, plus uncertainty, games, win rate, and coarse activity
- Corpus date range, model/config hash, snapshot hash, row counts, and field definitions
- Generic model code and entirely synthetic tests

## Excluded

- Platform, Steam, profile, Discord, and match IDs
- Raw matches, team-mate/opponent histories, timestamps, and API payloads
- Aliases, account merges, identity evidence, and crowd membership
- Crawl targets, source-specific parsers, operational logs, diagnostics, and unpublished outputs

`scripts/export_public.py` is an allowlist exporter: it selects named columns rather than dropping
known-sensitive ones, asserts exact output sizes, and rejects identifier-like or diagnostic
fields. `.github/scripts/privacy_guard.py` independently scans the tracked repository.

The lower group is deliberately not sorted by rating and every member receives the same broad
position and rating ranges. This preserves the complete participant list without revealing an
approximate ordering or singling out the lowest-rated player.
