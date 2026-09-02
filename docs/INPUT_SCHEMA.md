# Input schema

The public model consumes one row per completed 4v4 match. It deliberately has no platform IDs
or crawler-specific fields.

## Required fields

- `team1_player1` … `team1_player4`: four distinct, stable handles
- `team2_player1` … `team2_player4`: four more distinct, stable handles
- `team1_won`: `1` when team one won, otherwise `0`

The team labels must be assigned independently of the result. Sorting the two rosters by their
handles is a deterministic option. Never put the winner in team one by construction.

## Optional fields

- `team1_civ1` … `team1_civ4`, `team2_civ1` … `team2_civ4`: civilization labels. Either provide
  all eight columns or none.
- `played_at`: an ISO-8601 timestamp. When present, evidence receives a one-year half-life by
  default.
- `duration_seconds`: game-clock duration. Matches at or below five minutes receive zero weight;
  five-to-ten-minute games receive weight 0.2.
- `match_id`: useful for provenance and deterministic ordering, but not read by `fit_ratings`.

## Identity requirement

A handle is the model's unit of identity. If one person has two accounts, or two people share a
display name, resolve that before fitting. The public package does not guess identities. This is
also why the project's real identity registry stays private.
