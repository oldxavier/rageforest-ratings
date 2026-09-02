"""A reusable ridge Bradley–Terry model for fixed-size team games.

The public package intentionally accepts handles rather than platform IDs. It contains no
crawler, identity registry, raw match history, or assumptions about a particular community.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.linear_model import LogisticRegression

ELO_SCALE = 400 / np.log(10)
BASELINE = 1500.0
TEAM_SIZE = 4
PLAYER_COLUMNS = [
    *(f"team1_player{i}" for i in range(1, TEAM_SIZE + 1)),
    *(f"team2_player{i}" for i in range(1, TEAM_SIZE + 1)),
]
CIV_COLUMNS = [
    *(f"team1_civ{i}" for i in range(1, TEAM_SIZE + 1)),
    *(f"team2_civ{i}" for i in range(1, TEAM_SIZE + 1)),
]


@dataclass(slots=True)
class FitResult:
    """A fitted model plus the exact vocabularies needed to score another match."""

    model: LogisticRegression
    player_to_index: dict[str, int]
    civ_to_index: dict[str, int]
    ratings: pd.DataFrame


def _validate(matches: pd.DataFrame) -> None:
    required = {"team1_won", *PLAYER_COLUMNS}
    missing = required - set(matches.columns)
    if missing:
        raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")
    if not matches["team1_won"].isin([0, 1, False, True]).all():
        raise ValueError("team1_won must contain only 0/1 values")
    if matches[PLAYER_COLUMNS].isna().any().any():
        raise ValueError("every match must contain exactly four named players per team")
    duplicate = matches[PLAYER_COLUMNS].nunique(axis=1) != 2 * TEAM_SIZE
    if duplicate.any():
        raise ValueError("a player cannot occupy two slots in one match")


def _design(
    matches: pd.DataFrame,
    *,
    player_to_index: dict[str, int] | None = None,
    civ_to_index: dict[str, int] | None = None,
) -> tuple[csr_matrix, np.ndarray, dict[str, int], dict[str, int], np.ndarray]:
    _validate(matches)
    frozen_players = player_to_index is not None
    frozen_civs = civ_to_index is not None
    players = {} if player_to_index is None else dict(player_to_index)
    civs = {} if civ_to_index is None else dict(civ_to_index)
    has_civs = set(CIV_COLUMNS).issubset(matches.columns)

    p_rows: list[int] = []
    p_cols: list[int] = []
    p_values: list[float] = []
    c_rows: list[int] = []
    c_cols: list[int] = []
    c_values: list[float] = []
    labels: list[int] = []
    source_rows: list[int] = []

    for row_number, (_, row) in enumerate(matches.iterrows()):
        player_indices: list[tuple[int, float]] = []
        civ_indices: list[tuple[int, float]] = []
        scoreable = True
        for slot, column in enumerate(PLAYER_COLUMNS):
            sign = 1.0 / TEAM_SIZE if slot < TEAM_SIZE else -1.0 / TEAM_SIZE
            handle = str(row[column]).strip()
            if frozen_players and handle not in players:
                scoreable = False
                break
            player_indices.append((players.setdefault(handle, len(players)), sign))
            if has_civs:
                civ = str(row[CIV_COLUMNS[slot]]).strip()
                if frozen_civs and civ not in civs:
                    scoreable = False
                    break
                civ_indices.append((civs.setdefault(civ, len(civs)), sign))
        if not scoreable:
            continue

        output_row = len(labels)
        for index, value in player_indices:
            p_rows.append(output_row)
            p_cols.append(index)
            p_values.append(value)
        for index, value in civ_indices:
            c_rows.append(output_row)
            c_cols.append(index)
            c_values.append(value)
        labels.append(int(bool(row["team1_won"])))
        source_rows.append(row_number)

    player_matrix = csr_matrix(
        (p_values, (p_rows, p_cols)), shape=(len(labels), len(players))
    )
    civ_matrix = csr_matrix((c_values, (c_rows, c_cols)), shape=(len(labels), len(civs)))
    return (
        hstack([player_matrix, civ_matrix], format="csr"),
        np.asarray(labels),
        players,
        civs,
        np.asarray(source_rows),
    )


def _sample_weights(matches: pd.DataFrame, source_rows: np.ndarray, half_life_days: int) -> np.ndarray:
    weights = np.ones(len(source_rows))
    if "played_at" in matches:
        played = pd.to_datetime(matches["played_at"], utc=True).iloc[source_rows]
        age_days = (played.max() - played).dt.total_seconds().to_numpy() / 86_400
        weights *= np.power(0.5, np.clip(age_days, 0, None) / half_life_days)
    if "duration_seconds" in matches:
        seconds = matches["duration_seconds"].iloc[source_rows].fillna(9999).to_numpy()
        weights *= np.where(seconds <= 300, 0.0, np.where(seconds <= 600, 0.2, 1.0))
    return weights


def fit_ratings(
    matches: pd.DataFrame,
    *,
    ridge_c: float = 3.0,
    half_life_days: int = 365,
    baseline: float = BASELINE,
    max_iter: int = 2_000,
) -> FitResult:
    """Fit player and optional civilization effects from an eight-player match table."""
    matrix, labels, players, civs, source_rows = _design(matches)
    if len(set(labels)) != 2:
        raise ValueError("training data must contain wins by both canonical team sides")
    weights = _sample_weights(matches, source_rows, half_life_days)
    usable = weights > 0
    if not usable.any():
        raise ValueError("duration rules excluded every training match")

    model = LogisticRegression(
        C=ridge_c,
        solver="lbfgs",
        fit_intercept=False,
        max_iter=max_iter,
    )
    model.fit(matrix[usable], labels[usable], sample_weight=weights[usable])

    player_count = len(players)
    coefficients = model.coef_[0, :player_count] * ELO_SCALE
    coefficients = coefficients - coefficients.mean() + baseline
    probabilities = model.predict_proba(matrix[usable])[:, 1]
    information = np.asarray(
        matrix[usable].power(2).T.dot(probabilities * (1 - probabilities))
    ).ravel()
    uncertainty = np.sqrt(1 / (information + 1 / ridge_c))[:player_count] * ELO_SCALE
    games = np.asarray((matrix[:, :player_count] != 0).sum(axis=0)).ravel()

    inverse = sorted(players, key=players.get)
    ratings = pd.DataFrame(
        {
            "handle": inverse,
            "rating": np.rint(coefficients).astype(int),
            "uncertainty": np.rint(uncertainty).astype(int),
            "games": games.astype(int),
        }
    ).sort_values(["rating", "games", "handle"], ascending=[False, False, True])
    ratings.insert(0, "rank", np.arange(1, len(ratings) + 1))
    return FitResult(model, players, civs, ratings.reset_index(drop=True))


def predict_team1(result: FitResult, matches: pd.DataFrame) -> np.ndarray:
    """Return team-one win probabilities for matches covered by the fitted vocabulary."""
    matrix, _, _, _, _ = _design(
        matches,
        player_to_index=result.player_to_index,
        civ_to_index=result.civ_to_index,
    )
    return result.model.predict_proba(matrix)[:, 1]
