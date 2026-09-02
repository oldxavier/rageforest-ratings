"""Public, data-agnostic parts of the Rage Forest rating model."""

from .model import FitResult, fit_ratings, predict_team1

__all__ = ["FitResult", "fit_ratings", "predict_team1"]
