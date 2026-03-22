# Task Coverage Checklist

Source checked against: `unparsed.md`

## Core Requirement

- [x] Use an ORM only
  Implemented with SQLAlchemy in `app/models.py`, `app/services.py`, `app/findings.py`, and `load_oscar_data.py`.
- [x] No raw SQL
  The current implementation uses SQLAlchemy ORM queries and model metadata only.

## Task 2.1: Data Modeling With ORM

- [x] Load the dataset into SQLite using the chosen ORM
  `load_oscar_data.py` imports `full_data.csv` into `oscar_task2.sqlite3`.
- [x] Define proper entity/model classes
  Implemented in `app/models.py`.
- [x] Appropriate types
  Models use typed SQLAlchemy columns such as `String`, `Integer`, `Boolean`, and `Text`.
- [x] Relationships
  `Nomination` links to `Film`, `Category`, and `Ceremony`, with `NominationPerson` modeling the many-to-many relation to `Person`.
- [x] Constraints
  Includes uniqueness and check constraints such as unique source IDs and positive `ceremony_number`.
- [x] Explain schema design and ORM choice in markdown
  Covered in `task2_task21_design.md`.

## Task 2.2: Actor Profile App

- [x] Build an interactive app or widget
  Implemented in `streamlit_app.py`.
- [x] User enters an actor or director name
  Search input is at the top of the Streamlit app.
- [x] Rich profile card from dataset: nominations and wins
  Displayed in the stat cards.
- [x] Rich profile card from dataset: categories nominated in
  Displayed in the dataset summary panel.
- [x] Rich profile card from dataset: years active at the Oscars
  Displayed in the dataset summary panel.
- [x] Rich profile card from dataset: list of nominated and winning films
  Displayed in the films panel with separate labels and colors.
- [x] Wikipedia: short biography summary
  Displayed in the Profile and Wikipedia views.
- [x] Wikipedia: birth date
  Displayed in the Profile and Wikipedia views when available.
- [x] Wikipedia: photo if available
  Displayed on the right side in the Profile and Wikipedia views when available.
- [x] Computed insight: win rate
  Displayed in the stat cards.
- [x] Computed insight: comparison to the average nominee in their category
  Displayed in the category comparison table.
- [x] Computed insight: years between first nomination and first win
  Displayed in the stat cards.
- [x] Handle actor not found in dataset
  The app shows a clear not-found message.
- [x] Handle ambiguous Wikipedia matches
  The app surfaces ambiguity messaging and alternative candidate pages when returned.
- [x] Handle actors with no wins
  The app displays `No wins` where applicable.

## Task 2.3: Interesting Finds

- [x] Find and report 3 interesting discoveries
  Implemented in `app/findings.py` and surfaced in the `General Database Findings` tab.
- [x] State the finding
  Each finding includes a result statement.
- [x] Show how it was found
  Each finding includes a `How it was found` explanation.
- [x] Explain why it is interesting
  Each finding includes a `Why it is interesting` explanation.

Current findings:

- [x] Most nominations without a win
- [x] Longest gap from first nomination to first win
- [x] Broadest category range for an individual nominee

## Bonus

- [x] Add a "Did You Know?" feature
  Implemented in `app/services.py`.
- [x] Auto-generate a fun fact when looking up an actor
  Surfaced in the Streamlit app with a refresh button.
