# Oscar Actor Explorer

Oscar Actor Explorer is an ORM-backed Oscar awards exploration project built around the Kaggle Oscar dataset. It loads the source TSV into SQLite with SQLAlchemy, exposes reusable query/services code, and provides multiple ways to inspect the data:

- a Streamlit app that covers the profile workflow, Wikipedia integration, bonus fact generation, and the Task 2.3 findings

## What the project does

For a searched actor or director, the app combines:

- dataset-backed Oscar metrics: nominations, wins, categories, years active, nominated films, winning films
- live Wikipedia enrichment: summary, birth date, profile photo, page link
- computed insights: win rate, category-vs-average comparison, years from first nomination to first win
- bonus output: a generated "Did You Know?" fact

Task 2.3 is implemented through ORM queries and is also surfaced inside the Streamlit app.

## Technology choices

- `SQLAlchemy`: chosen for typed ORM models, strong SQLite support, and clean many-to-many modeling
- `SQLite`: lightweight local database suitable for a single-file assignment deliverable
- `wikipedia`: simple live Wikipedia access for person summaries and page resolution
- `beautifulsoup4`: extracts birth dates and the primary image from Wikipedia page HTML
- `Streamlit`: added as the deployment-friendly cloud UI

## Main files

- `load_oscar_data.py`: imports the dataset into SQLite through SQLAlchemy ORM models
- `app/models.py`: ORM schema
- `app/services.py`: search, profile assembly, comparisons, and fun-fact generation
- `app/wiki.py`: Wikipedia lookup and ambiguity resolution
- `streamlit_app.py`: Streamlit application
- `app/findings.py`: Task 2.3 findings logic

## Current UI behavior

- dataset-backed profile information renders first
- Wikipedia data is fetched immediately after the dataset profile starts rendering
- the `Profile` tab keeps the photo on the right side
- the `Wikipedia` tab contains the textual Wikipedia details
- the `General Database Findings` tab contains the three Task 2.3 discoveries

## Run locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Rebuild the SQLite database from the dataset:

```bash
python3 load_oscar_data.py
```

3. Run one of the interfaces:

```bash
streamlit run streamlit_app.py
```

4. Generate the findings report:

```bash
python3 -m app.findings
```

## Documentation

- `task2_task21_design.md`: schema design and ORM choice
- `task2_findings.md`: the three selected findings
- `task_coverage.md`: strict checklist against `unparsed.md`
- `task2_assignment_coverage.md`: requirement-by-requirement coverage
- `project_summary.md`: detailed explanation of what was built, how it works, challenges, and implementation status
- `deployment.md`: deployment target and cloud deployment steps

## Deployment target

The repo is now prepared for `Streamlit Community Cloud` deployment through `streamlit_app.py`. The exact steps and current limitations are documented in `deployment.md`.
