# Task 2 Assignment Coverage

## Requirement Coverage

### Task 2.1: Data Modeling with ORM

- Dataset is loaded into SQLite with SQLAlchemy ORM only
- Model classes define typed columns, foreign keys, relationships, uniqueness constraints, and checks
- Schema design and ORM choice are explained in `task2_task21_design.md`

Files:

- `app/models.py`
- `app/db.py`
- `load_oscar_data.py`
- `task2_task21_design.md`

### Task 2.2: Actor Profile App

Implemented through the current Streamlit interface:

- `streamlit_app.py`

Dataset output:

- number of nominations and wins
- categories nominated in
- years active at the Oscars
- nominated films and winning films

Wikipedia output:

- summary in the `Wikipedia` tab
- birth date when available
- inline photo when available in both the `Profile` and `Wikipedia` tabs

Computed insights:

- win rate
- category comparison against average nominee
- years between first nomination and first win

Graceful handling:

- dataset person not found
- multiple dataset matches
- ambiguous Wikipedia results with automatic resolution notes or alternative options
- no wins
- missing birth date
- missing photo
- Wikipedia lookup failures

Files:

- `streamlit_app.py`
- `app/services.py`
- `app/wiki.py`

Run:

- Streamlit app: `streamlit run streamlit_app.py`

Note:

- The Streamlit app is the single current interface.
- Dataset-backed profile content renders first, then the live Wikipedia content fills in.
- The `Profile` tab keeps the image visible while the `Wikipedia` tab holds the text-heavy Wikipedia details.
- It presents profile lookup, live Wikipedia data, the bonus fact, and the Task 2.3 findings.

### Task 2.3: Interesting Finds

- 3 findings selected and explained
- candidate findings ranked first
- ORM-only query logic implemented

Files:

- `app/findings.py`
- `task2_findings.md`
- surfaced in `streamlit_app.py`

Run:

- `python3 -m app.findings`

### Bonus: Did You Know?

- Added multiple generated facts for each looked-up person
- Facts draw from nomination percentile, win percentile, category breadth, film breadth, ceremony span, first-win delay, and category-specific percentile comparisons

Files:

- `app/services.py`
- surfaced in `streamlit_app.py`
