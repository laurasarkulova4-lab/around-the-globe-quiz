"""Pandas and NumPy summaries for completed quiz sessions."""
from __future__ import annotations

import numpy as np
import pandas as pd


def results_frame(results: list[dict]) -> pd.DataFrame:
    """Convert answer records into a tidy dataframe for analysis and export."""
    columns = ["question_number", "country", "category", "difficulty", "selected_answer",
               "correct_answer", "is_correct", "points_possible", "points_earned"]
    frame = pd.DataFrame(results)
    if frame.empty:
        return pd.DataFrame(columns=columns)
    return frame.reindex(columns=columns)


def performance_by_category(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize number of questions and accuracy by question category."""
    if frame.empty:
        return pd.DataFrame(columns=["category", "questions", "accuracy_percent"])
    summary = frame.groupby("category", as_index=False).agg(
        questions=("is_correct", "size"), accuracy_percent=("is_correct", "mean")
    )
    summary["accuracy_percent"] = (summary["accuracy_percent"] * 100).round(1)
    return summary.sort_values("accuracy_percent", ascending=False)


def difficulty_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize performance across Easy, Medium, and Hard questions."""
    if frame.empty:
        return pd.DataFrame(columns=["difficulty", "questions", "accuracy_percent"])
    order = ["Easy", "Medium", "Hard"]
    summary = frame.groupby("difficulty", as_index=False).agg(
        questions=("is_correct", "size"), accuracy_percent=("is_correct", "mean")
    )
    summary["accuracy_percent"] = (summary["accuracy_percent"] * 100).round(1)
    summary["difficulty"] = pd.Categorical(summary["difficulty"], categories=order, ordered=True)
    return summary.sort_values("difficulty")


def score_statistics(frame: pd.DataFrame) -> dict[str, float]:
    """Calculate descriptive statistics for earned points per question."""
    if frame.empty:
        return {"mean": 0.0, "std": 0.0, "median": 0.0}
    values = frame["points_earned"].to_numpy(dtype=float)
    return {
        "mean": round(float(np.mean(values)), 2),
        "std": round(float(np.std(values)), 2),
        "median": round(float(np.median(values)), 2),
    }
