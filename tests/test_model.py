from __future__ import annotations

import pandas as pd
import pytest

from rageforest_ratings import fit_ratings, predict_team1


def test_fit_recovers_the_stronger_synthetic_team(synthetic_4v4: pd.DataFrame) -> None:
    result = fit_ratings(synthetic_4v4)
    ratings = result.ratings.set_index("handle")

    assert ratings.loc[["P01", "P02", "P03", "P04"], "rating"].min() > ratings.loc[
        ["P05", "P06", "P07", "P08"], "rating"
    ].max()
    assert set(result.ratings.columns) == {"rank", "handle", "rating", "uncertainty", "games"}


def test_prediction_is_antisymmetric(synthetic_4v4: pd.DataFrame) -> None:
    result = fit_ratings(synthetic_4v4)
    first = synthetic_4v4.iloc[[0]].copy()
    swapped = first.copy()
    for slot in range(1, 5):
        swapped[f"team1_player{slot}"], swapped[f"team2_player{slot}"] = (
            first[f"team2_player{slot}"].to_numpy(),
            first[f"team1_player{slot}"].to_numpy(),
        )
        swapped[f"team1_civ{slot}"], swapped[f"team2_civ{slot}"] = (
            first[f"team2_civ{slot}"].to_numpy(),
            first[f"team1_civ{slot}"].to_numpy(),
        )

    p = predict_team1(result, first)[0]
    reverse = predict_team1(result, swapped)[0]
    assert p + reverse == pytest.approx(1.0)


def test_schema_rejects_duplicate_player(synthetic_4v4: pd.DataFrame) -> None:
    broken = synthetic_4v4.copy()
    broken.loc[0, "team2_player1"] = broken.loc[0, "team1_player1"]

    with pytest.raises(ValueError, match="cannot occupy two slots"):
        fit_ratings(broken)
