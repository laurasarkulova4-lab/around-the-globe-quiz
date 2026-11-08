"""Unit tests for question generation and difficulty-weighted scoring."""
import pandas as pd

from globe_quiz.quiz import calculate_score, generate_question



def sample_countries():
    return pd.DataFrame([
        {"country": "Italy", "capital": "Rome", "currency": "Euro", "languages": "Italian", "region": "Europe", "subregion": "Southern Europe", "flag": "🇮🇹", "population": 59000000},
        {"country": "France", "capital": "Paris", "currency": "Euro", "languages": "French", "region": "Europe", "subregion": "Western Europe", "flag": "🇫🇷", "population": 68000000},
        {"country": "Spain", "capital": "Madrid", "currency": "Euro", "languages": "Spanish", "region": "Europe", "subregion": "Southern Europe", "flag": "🇪🇸", "population": 48000000},
        {"country": "Germany", "capital": "Berlin", "currency": "Euro", "languages": "German", "region": "Europe", "subregion": "Western Europe", "flag": "🇩🇪", "population": 84000000},
        {"country": "Japan", "capital": "Tokyo", "currency": "Japanese yen", "languages": "Japanese", "region": "Asia", "subregion": "Eastern Asia", "flag": "🇯🇵", "population": 124000000},
        {"country": "Canada", "capital": "Ottawa", "currency": "Canadian dollar", "languages": "English, French", "region": "Americas", "subregion": "North America", "flag": "🇨🇦", "population": 40000000},
    ])


def test_question_has_four_unique_options():
    question = generate_question(sample_countries(), "Medium", "capital")
    assert len(question.options) == 4
    assert len(set(question.options)) == 4
    assert question.correct_answer in question.options


def test_weighted_score_rewards_harder_questions():
    results = [
        {"difficulty": "Easy", "is_correct": True},
        {"difficulty": "Hard", "is_correct": False},
    ]
    score = calculate_score(results)
    assert score["earned_points"] == 1
    assert score["maximum_points"] == 4
    assert score["score_percent"] == 25.0


def test_flag_question_uses_country_names_as_answers():
    question = generate_question(sample_countries(), "Easy", "flag")
    assert len(question.options) == 4
    assert question.correct_answer == question.country
    assert question.correct_answer in question.options
    assert any(flag in question.prompt for flag in ["🇮🇹", "🇫🇷", "🇪🇸", "🇩🇪", "🇯🇵", "🇨🇦"])
