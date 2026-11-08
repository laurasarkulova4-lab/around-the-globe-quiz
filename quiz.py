"""Question generation and difficulty-aware scoring logic."""
from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

DIFFICULTY_POINTS = {"Easy": 1, "Medium": 2, "Hard": 3}
QUESTION_TYPES = {
    "Capital cities": "capital",
    "Currencies": "currency",
    "Official languages": "languages",
    "Flags": "flag",
    "Regions": "region",
    "Population": "population",
    "GDP per capita": "gdp_per_capita",
}


@dataclass
class Question:
    """A four-option multiple-choice question with its scoring metadata."""
    prompt: str
    options: list[str]
    correct_answer: str
    difficulty: str
    category: str
    country: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        """Return the question as a serializable dictionary."""
        return asdict(self)


def _answer_value(row: pd.Series, category: str) -> str | None:
    """Convert a country row into a displayable answer for one category."""
    if category == "flag":
        # The flag is shown in the prompt; answer choices must be country names.
        return str(row.get("country"))
    value = row.get(category)
    if pd.isna(value) or value is None or str(value).strip() == "":
        return None
    if category == "population":
        return f"{int(round(float(value))):,}"
    if category == "gdp_per_capita":
        return f"${float(value):,.0f}"
    return str(value)


def _question_prompt(row: pd.Series, category: str) -> tuple[str, str]:
    """Create the question wording and a short factual explanation."""
    country = row["country"]
    prompts = {
        "capital": (f"What is the capital city of **{country}**?", f"The capital of {country} is {_answer_value(row, category)}."),
        "currency": (f"Which currency is used in **{country}**?", f"{country}'s listed currency is {_answer_value(row, category)}."),
        "languages": (f"Which official language(s) are listed for **{country}**?", f"The listed official language(s) of {country}: {_answer_value(row, category)}."),
        "flag": (f"Which country does this flag belong to? {row.get('flag', '🌍')}", f"This is the flag of {country}."),
        "region": (f"In which world region is **{country}** located?", f"{country} is in {row.get('region')}, specifically {row.get('subregion') or 'an unspecified subregion'}"),
        "population": (f"What is the latest available population estimate for **{country}**?", f"The latest available World Bank population value for {country} is {_answer_value(row, category)}."),
        "gdp_per_capita": (f"What is the latest available GDP per capita for **{country}**?", f"The latest available World Bank GDP per capita value for {country} is {_answer_value(row, category)}."),
    }
    return prompts[category]


def _similarity_scores(target: pd.Series, candidates: pd.DataFrame, category: str) -> pd.Series:
    """Score candidate answers by similarity; higher means a harder distractor."""
    scores = pd.Series(0.0, index=candidates.index)
    if category in {"capital", "currency", "languages", "region"}:
        if target.get("region"):
            scores += (candidates["region"] == target["region"]).astype(float) * 2.0
        if target.get("subregion"):
            scores += (candidates["subregion"] == target["subregion"]).astype(float) * 2.0
        if category == "languages" and target.get("languages"):
            target_words = set(str(target["languages"]).split(", "))
            scores += candidates["languages"].fillna("").apply(
                lambda text: bool(target_words.intersection(set(str(text).split(", "))))
            ).astype(float) * 3.0
        if category == "currency" and target.get("currency"):
            target_words = set(str(target["currency"]).split(", "))
            scores += candidates["currency"].fillna("").apply(
                lambda text: bool(target_words.intersection(set(str(text).split(", "))))
            ).astype(float) * 3.0
    elif category in {"population", "gdp_per_capita"}:
        target_value = pd.to_numeric(target.get(category), errors="coerce")
        values = pd.to_numeric(candidates[category], errors="coerce")
        if pd.notna(target_value) and target_value > 0:
            # Log distance treats a 10% difference similarly for small and large countries.
            distance = np.abs(np.log(values.clip(lower=1) / float(target_value)))
            scores = 1 / (1 + distance)
    elif category == "flag":
        scores += (candidates["region"] == target.get("region")).astype(float)
        scores += (candidates["subregion"] == target.get("subregion")).astype(float)
    return scores


def generate_question(countries: pd.DataFrame, difficulty: str = "Medium",
                      category: str | None = None, rng: random.Random | None = None) -> Question:
    """Generate one valid four-option geography question.

    Easy questions use random distractors. Medium questions prefer somewhat
    similar countries. Hard questions select the most similar available
    distractors (for population, the closest values on a logarithmic scale).
    """
    if difficulty not in DIFFICULTY_POINTS:
        raise ValueError(f"Unknown difficulty: {difficulty}")
    rng = rng or random.Random()
    if category is None:
        category = rng.choice(list(QUESTION_TYPES.values()))
    if category not in QUESTION_TYPES.values():
        raise ValueError(f"Unknown question category: {category}")

    usable = countries.dropna(subset=[category]).copy()
    usable = usable[usable[category].astype(str).str.strip().ne("")]
    if category == "population":
        usable = usable[pd.to_numeric(usable[category], errors="coerce") > 0]
    if len(usable) < 4:
        raise ValueError(f"Not enough countries with data for {category} questions.")

    # Avoid ambiguous duplicate answers: each answer must identify one country.
    usable["_answer"] = usable.apply(lambda row: _answer_value(row, category), axis=1)
    usable = usable.dropna(subset=["_answer"]).drop_duplicates("_answer")
    target_index = rng.choice(list(usable.index))
    target = usable.loc[target_index]
    pool = usable.drop(index=target_index)
    similarities = _similarity_scores(target, pool, category)

    if difficulty == "Easy":
        selected_indices = rng.sample(list(pool.index), 3)
    else:
        ordered = similarities.sort_values(ascending=False)
        if difficulty == "Medium":
            top_pool = list(ordered.head(min(15, len(ordered))).index)
            selected_indices = rng.sample(top_pool, min(3, len(top_pool)))
            if len(selected_indices) < 3:
                selected_indices += rng.sample([i for i in pool.index if i not in selected_indices], 3-len(selected_indices))
        else:
            selected_indices = list(ordered.head(3).index)

    correct = target["_answer"]
    options = [correct] + [pool.loc[index, "_answer"] for index in selected_indices]
    rng.shuffle(options)
    prompt, explanation = _question_prompt(target, category)
    return Question(prompt, options, correct, difficulty, category, target["country"], explanation)


def calculate_score(results: list[dict[str, Any]]) -> dict[str, float | int]:
    """Calculate a difficulty-weighted score as a percentage of available points."""
    if not results:
        return {"earned_points": 0, "maximum_points": 0, "score_percent": 0.0, "correct_answers": 0}
    weights = np.array([DIFFICULTY_POINTS[item["difficulty"]] for item in results], dtype=float)
    correct = np.array([bool(item["is_correct"]) for item in results], dtype=bool)
    earned = float(np.sum(weights * correct))
    maximum = float(np.sum(weights))
    return {
        "earned_points": int(earned),
        "maximum_points": int(maximum),
        "score_percent": round(100 * earned / maximum, 1) if maximum else 0.0,
        "correct_answers": int(correct.sum()),
    }
