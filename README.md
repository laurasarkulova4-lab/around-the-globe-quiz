# 🌍 Around the Globe Quiz

An interactive geography quiz that automatically generates four-option multiple-choice questions about countries. Players can choose a difficulty, answer a round of questions, receive a difficulty-weighted score, review their answers, and explore performance charts.

## Project goals

- Generate questions about capitals, currencies, official languages, flags, regions, population, and GDP per capita.
- Always provide four distinct answer options with exactly one correct option.
- Adjust distractor similarity to the selected difficulty.
- Let a human player answer questions in an interactive Streamlit app.
- Calculate a score that gives more points to harder questions.
- Analyze performance by topic and difficulty using pandas, NumPy, and matplotlib.

## Data sources

1. **World countries dataset** — [mledoze/countries](https://github.com/mledoze/countries). Used for country names, capitals, flags, official languages, currencies, regions, subregions, borders, and area. The app downloads the JSON file on first run and caches it locally. The dataset is licensed under Open Data Commons Open Database License (ODbL-1.0); see the [source license](https://github.com/mledoze/countries/blob/master/LICENSE).
2. **World Bank Indicators API** — [API documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation). Used for population (`SP.POP.TOTL`) and GDP per capita (`NY.GDP.PCAP.CD`). The latest non-missing observation returned for each country is used. Indicator data are optional: if the API is unavailable, the app continues with the country dataset and population questions are omitted automatically only when there are insufficient population records (see note below).

The World Bank API does not require an API key. Values can refer to different years across countries because the latest available observation is selected independently for each country. The GDP-per-capita indicator is `NY.GDP.PCAP.CD` and is expressed in current US dollars.

## Project structure

```text
around_the_globe_quiz/
├── app.py                  # Streamlit user interface
├── globe_quiz/
│   ├── __init__.py
│   ├── data.py              # External data loading, caching and cleaning
│   ├── quiz.py              # Question generation, distractors and scoring
│   └── analysis.py          # Performance summaries using pandas and NumPy
├── tests/
│   └── test_quiz.py         # Basic tests for question generation and scoring
├── data/                    # Local cache is created here at runtime
├── .streamlit/config.toml   # App theme
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

Python 3.10 or newer is recommended.

### 1. Download or clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/around-the-globe-quiz.git
cd around-the-globe-quiz
```

If you downloaded the ZIP file instead, extract it and open a terminal in the extracted folder.

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the application

**Windows shortcut:** double-click `run_windows.bat`. It creates the virtual environment, installs the dependencies, and launches the app.

**Manual command (all operating systems):**

```bash
streamlit run app.py
```

Streamlit will open the application in your browser, usually at `http://localhost:8501`. An internet connection is needed the first time country data are downloaded and when World Bank indicators are refreshed. The country JSON is cached locally after the first successful download.

## How the quiz works

### Question generation

Each generated question has one prompt and four distinct options. The generator first chooses a country with a valid answer for the selected topic. It then chooses three other countries as distractors.

- **Easy:** distractors are selected randomly from the available countries.
- **Medium:** distractors are sampled from a shortlist of countries with similar geographic or factual characteristics.
- **Hard:** the three most similar available distractors are selected. For population and GDP per capita, similarity is based on logarithmic distance between values, so relative differences are compared rather than raw differences. For other topics, countries in the same region/subregion and countries sharing a language or currency are preferred.

The answer is unique at the country-record level: records with duplicate answer labels are removed before generating the question. This avoids duplicate choices and ambiguous correct answers.

### Scoring

Each question is worth a number of points based on its difficulty:

| Difficulty | Points for a correct answer |
|---|---:|
| Easy | 1 |
| Medium | 2 |
| Hard | 3 |

Incorrect answers earn zero points. The final score is normalized to a percentage:

`score = earned points / maximum available points * 100`

This means a correct hard question contributes more to the final score than a correct easy question.

### Analysis

After a round, the app displays:

- weighted score and number of correct answers;
- accuracy by question topic;
- accuracy by difficulty;
- mean, median, and standard deviation of points earned per question;
- a detailed answer-review table;
- a downloadable CSV file of the round.

## Testing

Run the basic tests from the project root:

```bash
pytest -q
```

The tests check that generated questions have four unique options and that the scoring formula weights difficulty correctly.

## Limitations and possible extensions

- Country names, capital cities, currencies and language names depend on the source dataset and can change over time.
- Population questions require population values from the World Bank API. The API may not return a value for every country.
- The current app keeps a quiz round in Streamlit session state; it does not create user accounts or store a permanent leaderboard.
- Possible extensions include adding neighbouring-country questions, historical trends, a persistent leaderboard, and a wider set of World Bank indicators.

## Reproducibility and Git history

Use small, meaningful commits rather than one large upload. Suggested sequence:

```bash
git init
git add README.md .gitignore requirements.txt
git commit -m "Add project documentation and dependencies"
git add globe_quiz/data.py
git commit -m "Add country data loading and cleaning"
git add globe_quiz/quiz.py tests/test_quiz.py
git commit -m "Implement difficulty-aware question generation and scoring"
git add globe_quiz/analysis.py app.py .streamlit/config.toml
git commit -m "Build Streamlit quiz and performance dashboard"
```

Then create an empty GitHub repository named `around-the-globe-quiz`, connect it, and push:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/around-the-globe-quiz.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Do not commit the local country cache or virtual environment.

## Academic note

The MIT license in this repository applies to the original project code. The mledoze/countries dataset is a separate third-party database under ODbL-1.0; its attribution and share-alike conditions remain applicable. World Bank data are subject to the World Bank's data terms.

This is an individual project template prepared for the Python module assignment. Before submission, run it yourself, verify the data and outputs, personalize the README with your details, and make sure you can explain the functions, difficulty logic, scoring formula, data sources, and charts during the oral discussion.
