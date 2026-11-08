"""Streamlit interface for Around the Globe Quiz."""
from __future__ import annotations

import random

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from globe_quiz.analysis import difficulty_summary, performance_by_category, results_frame, score_statistics
from globe_quiz.data import load_country_data
from globe_quiz.quiz import DIFFICULTY_POINTS, QUESTION_TYPES, calculate_score, generate_question

st.set_page_config(page_title="Around the Globe Quiz", page_icon="🌍", layout="wide")
st.title("🌍 Around the Globe Quiz")
st.caption("Explore the world, one question at a time.")

@st.cache_data(show_spinner="Loading country data...")
def get_data() -> pd.DataFrame:
    """Load country data once and cache it for the current app session."""
    return load_country_data()

try:
    countries = get_data()
except Exception as error:  # Keep the interface informative if the network is unavailable.
    st.error("Country data could not be loaded. Check your internet connection and try again.")
    st.caption(f"Technical detail: {error}")
    st.stop()

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "results" not in st.session_state:
    st.session_state.results = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = None

with st.sidebar:
    st.header("Quiz settings")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Mixed"], index=1)
    available_categories = [
        label for label, field in QUESTION_TYPES.items()
        if countries[field].notna().sum() >= 4
    ]
    categories = st.multiselect("Question topics", available_categories, default=available_categories)
    unavailable_categories = sorted(set(QUESTION_TYPES) - set(available_categories))
    if unavailable_categories:
        st.caption("Unavailable with the current data: " + ", ".join(unavailable_categories))
    number_questions = st.slider("Questions per round", min_value=5, max_value=20, value=10)
    st.markdown("---")
    st.markdown("**Scoring**")
    st.write("Easy: 1 point · Medium: 2 points · Hard: 3 points")
    st.caption("Mixed mode assigns a difficulty separately to each question.")
    st.caption("The final percentage is earned points divided by all points available.")
    if st.button("Start a new quiz", type="primary", use_container_width=True):
        if not categories:
            st.warning("Choose at least one topic.")
        else:
            category_values = [QUESTION_TYPES[label] for label in categories]
            generated = []
            for _ in range(number_questions):
                category = random.choice(category_values)
                question_difficulty = random.choice(list(DIFFICULTY_POINTS)) if difficulty == "Mixed" else difficulty
                generated.append(generate_question(countries, difficulty=question_difficulty, category=category))
            st.session_state.quiz_questions = [q.to_dict() for q in generated]
            st.session_state.current_index = 0
            st.session_state.results = []
            st.session_state.submitted = False
            st.session_state.last_feedback = None
            st.rerun()

st.markdown("### How it works")
st.write("Choose your difficulty and topics in the sidebar, then start a round. Each question has exactly four options and one correct answer. Your final score rewards harder questions with more points.")

questions = st.session_state.quiz_questions
if not questions:
    col1, col2, col3 = st.columns(3)
    col1.metric("Countries", f"{len(countries):,}")
    col2.metric("Question topics", len(QUESTION_TYPES))
    col3.metric("Answer choices", "4 per question")
    st.info("Select your settings on the left and click **Start a new quiz**.")
else:
    total = len(questions)
    index = st.session_state.current_index
    if index < total:
        feedback = st.session_state.last_feedback
        if feedback is not None:
            if feedback["correct"]:
                st.success("Correct! " + feedback["explanation"])
            else:
                st.error("Not quite. " + feedback["explanation"])
            if st.button("Continue to next question", type="primary"):
                st.session_state.last_feedback = None
                st.rerun()
        else:
            question = questions[index]
            st.progress(index / total, text=f"Question {index + 1} of {total}")
            st.markdown(f"**Difficulty:** {question['difficulty']} · **Value:** {DIFFICULTY_POINTS[question['difficulty']]} point(s)")
            st.markdown(f"## {question['prompt']}")
            choice = st.radio("Select one answer:", question["options"], index=None, key=f"answer_{index}")
            if st.button("Submit answer", type="primary", disabled=choice is None):
                correct = choice == question["correct_answer"]
                points_possible = DIFFICULTY_POINTS[question["difficulty"]]
                st.session_state.results.append({
                    "question_number": index + 1,
                    "country": question["country"],
                    "category": question["category"],
                    "difficulty": question["difficulty"],
                    "selected_answer": choice,
                    "correct_answer": question["correct_answer"],
                    "is_correct": correct,
                    "points_possible": points_possible,
                    "points_earned": points_possible if correct else 0,
                    "explanation": question["explanation"],
                })
                st.session_state.last_feedback = {"correct": correct, "explanation": question["explanation"]}
                st.session_state.current_index += 1
                st.rerun()
    else:
        st.session_state.submitted = True
        feedback = st.session_state.last_feedback
        if feedback is not None:
            if feedback["correct"]:
                st.success("Correct! " + feedback["explanation"])
            else:
                st.error("Not quite. " + feedback["explanation"])

if st.session_state.submitted:
    st.markdown("---")
    st.header("Your results")
    frame = results_frame(st.session_state.results)
    score = calculate_score(st.session_state.results)
    a, b, c = st.columns(3)
    a.metric("Weighted score", f"{score['score_percent']}%")
    b.metric("Correct answers", f"{score['correct_answers']} / {len(frame)}")
    c.metric("Points earned", f"{score['earned_points']} / {score['maximum_points']}")

    st.subheader("Performance analysis")
    category_data = performance_by_category(frame)
    difficulty_data = difficulty_summary(frame)
    left, right = st.columns(2)
    with left:
        st.write("Accuracy by topic")
        if not category_data.empty:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.barh(category_data["category"], category_data["accuracy_percent"])
            ax.set_xlabel("Accuracy (%)")
            ax.set_xlim(0, 100)
            ax.set_title("Accuracy by question topic")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
    with right:
        st.write("Accuracy by difficulty")
        if not difficulty_data.empty:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(difficulty_data["difficulty"].astype(str), difficulty_data["accuracy_percent"])
            ax.set_ylabel("Accuracy (%)")
            ax.set_ylim(0, 100)
            ax.set_title("Accuracy by difficulty")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    stats = score_statistics(frame)
    st.caption(f"Mean points per question: {stats['mean']} · Standard deviation: {stats['std']} · Median: {stats['median']}")
    st.subheader("Answer review")
    review = frame[["question_number", "country", "category", "difficulty", "selected_answer", "correct_answer", "is_correct"]]
    st.dataframe(review, use_container_width=True, hide_index=True)
    st.download_button("Download results as CSV", frame.to_csv(index=False).encode("utf-8"),
                       file_name="around_the_globe_results.csv", mime="text/csv")
    if st.button("Play another round", type="primary"):
        st.session_state.quiz_questions = []
        st.session_state.current_index = 0
        st.session_state.results = []
        st.session_state.submitted = False
        st.session_state.last_feedback = None
        st.rerun()

with st.expander("About the data"):
    st.write("Country facts are loaded from the mledoze/countries open dataset. Population and GDP per capita are requested from the World Bank API when available. World Bank values are the latest non-missing observation returned by the API; the observation year can differ by country.")
    st.write(f"Loaded {len(countries)} UN member country records. Population coverage: {countries['population'].notna().sum()} countries; GDP per capita coverage: {countries['gdp_per_capita'].notna().sum()} countries.")
