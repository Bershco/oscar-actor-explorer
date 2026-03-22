# Oscar Actor Explorer Project Summary

## What was built

This project implements the full **Oscar Actor Explorer** assignment around the Oscar awards dataset.

The finished codebase contains three main layers:

1. **An ORM-backed data layer**
   - The dataset is loaded from `full_data.csv` into `oscar_task2.sqlite3`.
   - SQLAlchemy models define people, films, categories, ceremonies, nominations, and the nomination-to-person join table.
   - The loader normalizes IDs, handles missing values, and deduplicates repeated nominee links.

2. **A reusable service/query layer**
   - Search logic finds matching people by exact, prefix, or partial name.
   - Profile logic assembles all dataset metrics required by the assignment.
   - Comparison logic computes per-category averages for the searched person.
   - Bonus logic generates a randomized "Did You Know?" fact from percentile-style statistics.

3. **Interactive app interface**
   - `streamlit_app.py`: the current Streamlit UI, which covers profile lookup, progressive Wikipedia enrichment, the bonus fact, and the Task 2.3 findings

4. **Task 2.3 findings/reporting**
   - ORM queries identify three interesting Oscar findings.
   - Each finding includes the result, how it was found, and why it is interesting.

## How it works

### Task 2.1: Data modeling and loading

The data model is centered on the fact that a single nomination row can involve more than one nominee. Because of that, a simple `person_id` inside `nominations` would have been incorrect. The schema instead uses:

- `persons`
- `films`
- `categories`
- `ceremonies`
- `nominations`
- `nomination_people`

`nomination_people` is the key relationship table. It preserves many-to-many links between nominations and people and also stores `credit_order` so nominee order is not lost.

The loader in `load_oscar_data.py`:

- reads the TSV dataset with `csv.DictReader`
- normalizes text and identifiers
- converts booleans from the dataset
- derives `year_start` from the year label
- reuses cached ORM objects while importing
- creates one `Nomination` row per source row
- links zero, one, or many people to each nomination

Important schema choices:

- `source_row_number` is unique because some rows do not have a reliable `NomId`
- `source_person_id` and `source_film_id` are unique when present
- `ceremony_number` is unique and checked to be positive
- all querying stays inside SQLAlchemy ORM logic; no raw SQL is used

### Task 2.2: Actor profile app

The profile app combines **dataset facts**, **live Wikipedia enrichment**, and **computed insights**.

#### Dataset-backed profile information

For a searched actor or director, the service layer returns:

- total nominations
- total wins
- categories nominated in
- years active at the Oscars
- nominated films
- winning films

This is assembled in `app/services.py` by loading all nominations tied to the selected person and then deriving sorted unique lists and counts.

#### Wikipedia integration

`app/wiki.py` fetches live Wikipedia data using the `wikipedia` package and enriches the profile with:

- biography summary
- birth date
- profile photo
- page URL

The implementation does more than a naive lookup:

- it searches for likely titles first
- it catches disambiguation errors
- it scores ambiguous options by name similarity and Oscar-related keywords
- it extracts birth date and photo from the returned page HTML
- it keeps alternative candidate pages and explanatory notes when ambiguity exists

In the current Streamlit UI, the dataset-backed profile renders first, and the Wikipedia fetch completes immediately afterward so the page is usable before the live lookup finishes. The main `Profile` tab keeps the photo visible on the right side, while the text-heavy Wikipedia details live in the dedicated `Wikipedia` tab.

#### Computed insights

The app computes all required derived metrics:

- **Win rate**: wins / nominations
- **Comparison to average nominee in their category**:
  - for every category the person appears in, the app computes that person's nomination and win totals
  - it then compares those values against the category-wide average person in the same category
- **Years between first nomination and first win**:
  - derived from the first ceremony year and first winning ceremony year

#### Bonus feature: "Did You Know?"

The bonus feature is implemented in `choose_fun_fact()` inside `app/services.py`.

It builds a pool of possible facts using cached dataset-wide distributions, including:

- nomination percentile
- win percentile
- category breadth percentile
- film breadth percentile
- ceremony span percentile
- first-win delay percentile
- category-specific percentile advantages
- whether the person outperforms the average nominee in one or more categories

One fact is selected at random for each profile view.

#### Edge cases handled

The app explicitly handles:

- no dataset match
- multiple dataset matches
- no wins
- missing birth dates
- missing photos
- Wikipedia page not found
- Wikipedia ambiguity
- general Wikipedia request failures

### Task 2.3: Interesting findings

Three findings were selected and implemented in `app/findings.py`.

#### Finding 1: Most nominations without a win

The query groups nominations by person, filters to individual nominees, removes anyone with at least one win, orders by nomination count descending, and returns the top result.

Why it matters:
- it highlights long-term Academy recognition without a win

#### Finding 2: Longest gap between first nomination and first win

The code loads each nominee's ordered nomination history, captures the first nomination year and first winning year, computes the gap in Python, and keeps the maximum.

Why it matters:
- it shows how delayed Oscar recognition can be

#### Finding 3: Broadest category range for an individual nominee

The query counts the number of distinct categories attached to each person, orders descending, and then lists the winner's categories.

Why it matters:
- it surfaces unusually broad Oscar careers instead of only total volume

## Technologies and libraries used, and why

### `SQLAlchemy`

Chosen because the assignment required an ORM and this dataset needed a correct many-to-many design. SQLAlchemy made typed models, relationships, foreign keys, uniqueness constraints, and aggregate ORM queries straightforward.

### `SQLite`

Chosen because it is lightweight, local, file-based, and ideal for a coursework-style deliverable.

### `wikipedia`

Chosen because the assignment explicitly allowed live Wikipedia fetching through the API or Python package. It provides a quick path to page search, summaries, and URLs.

### `beautifulsoup4`

Used because the Wikipedia package does not expose everything needed cleanly. HTML parsing was necessary to extract a better birth date source and the infobox image.

### `Streamlit`

Used as the single interactive frontend because it is browser-based, simple to deploy, and light enough for this assignment without extra backend complexity.

## Challenges encountered and how they were solved

### 1. One nomination row can contain multiple people

Problem:
- some Oscar records list multiple nominees in a single row

Solution:
- introduced `nomination_people` as an explicit join table
- stored `credit_order`
- split names and IDs carefully during import
- deduplicated repeated nominee links within a row

### 2. The source dataset has incomplete or inconsistent identifiers

Problem:
- some rows contain missing IDs or placeholder values like `?`

Solution:
- normalized identifiers before import
- treated placeholder IDs as missing
- fell back to name-based identity keys when needed
- used `source_row_number` as a stable unique import key for nominations

### 3. Wikipedia names are often ambiguous

Problem:
- many people share names, and a plain Wikipedia lookup can return the wrong page or a disambiguation page

Solution:
- ranked search/disambiguation candidates by base-name similarity
- preferred candidates whose title/summary looked Oscar-related
- returned notes and alternative candidates when the selection was ambiguous

### 4. Birth date and image were not directly reliable from the basic package response

Problem:
- the package gives summary text, but structured fields like birth date and best profile photo are not guaranteed

Solution:
- pulled the page HTML
- parsed the infobox for birth date and image
- added fallbacks using summary text and the page image list

### 5. Cloud deployment needs a browser-friendly frontend

Problem:
- a local-only interface would not be a realistic browser deployment target

Solution:
- kept the implementation focused on `streamlit_app.py` as the single frontend
- documented Streamlit Community Cloud as the deployment target

### 6. Documentation had drifted from the actual code

Problem:
- project documentation had drifted away from the single current implementation

Solution:
- updated the assignment coverage doc
- updated the Task 2.1 design doc
- added a root `README.md`
- added this summary file
- added a dedicated deployment document

## What is currently true in the codebase

- Task 2.1 is implemented with SQLAlchemy and SQLite.
- Task 2.2 is implemented through a single Streamlit interface.
- Task 2.3 is implemented with ORM-only findings logic.
- The bonus "Did You Know?" feature is implemented.
- The repo is prepared for Streamlit Community Cloud deployment.
- The repository no longer keeps obsolete alternate frontends that are not part of the current implementation.

## What to read if you want to understand the project quickly

Read these in order:

1. `README.md`
2. `task2_assignment_coverage.md`
3. `task2_task21_design.md`
4. `project_summary.md`
5. `app/models.py`
6. `load_oscar_data.py`
7. `app/services.py`
8. `app/wiki.py`
9. `streamlit_app.py`
10. `app/findings.py`
