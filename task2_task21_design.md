# Task 2.1 Design

## Chosen ORM

The implementation uses `SQLAlchemy`.

Why `SQLAlchemy` was chosen here:

- It has strong SQLite support and a clear ORM mapping style.
- It handles both simple tables and one necessary association table cleanly.
- Relationships, uniqueness constraints, indexes, and typed models are straightforward to express.
- It stays readable for a small project while still being robust enough for later aggregation queries in Task 2.2 and Task 2.3.
- It does not force a more opinionated pattern than this task needs.

`Peewee` could also work, but `SQLAlchemy` is the safer default once the dataset requires a real many-to-many between nominations and people.

---

## Implemented Schema

The schema is normalized around the central `nominations` table.

### `persons`
- internal integer primary key
- `source_person_id` from the dataset, nullable, unique when present
- `name`, required

Purpose:
- stores one person record per nominee identity when possible
- allows fallback matching by name when the source dataset omits a person identifier

### `films`
- internal integer primary key
- `source_film_id` from the dataset, nullable, unique when present
- `title`, required

### `categories`
- internal integer primary key
- `award_class`, required
- `canonical_name`, required, unique
- `display_name`, required

### `ceremonies`
- internal integer primary key
- `ceremony_number`, required
- `year_label`, required
- `year_start`, nullable integer

Uniqueness:
- unique on `ceremony_number`

### `nominations`
- internal integer primary key
- `source_row_number`, required, unique
- `source_nomination_id`, nullable, indexed
- foreign key to `film`, nullable because some rows do not point to a film
- foreign key to `category`, required
- foreign key to `ceremony`, required
- `name_text`, nullable
- `nominees_text`, nullable
- `nominee_ids_text`, nullable
- `winner`, required boolean
- `detail`, nullable text
- `note`, nullable text
- `citation`, nullable text
- `multifilm_nomination`, required boolean

### `nomination_people`
- composite primary key of `nomination_id` and `person_id`
- optional `credit_order` to preserve source order when a nomination has multiple nominees

---

## Relationship Summary

This is the relationship model to implement:

- One `Ceremony` : Many `Nomination`
- One `Category` : Many `Nomination`
- One `Film` : Many `Nomination`
- Many `Nomination` : Many `Person`

Effective relationships through `Nomination`:

- Many `Person` : Many `Film`
- Many `Person` : Many `Ceremony`
- Many `Person` : Many `Category`
- Many `Film` : Many `Ceremony`

Why `Nomination <-> Person` is many-to-many:

- The dataset contains rows with multiple nominee names and IDs in a single nomination row.
- A simple `nominations.person_id` would lose information.
- A join table keeps the schema correct without making it complex.

---

## Loading Approach

- Read the TSV with Python's `csv.DictReader`.
- Drop and recreate tables through SQLAlchemy ORM metadata during a full reload.
- Reuse cached people, films, categories, and ceremonies while importing to avoid duplicate ORM objects and repeated lookups.
- Insert nominations and then attach nominee people through the association table.
- Use the dataset row number as a guaranteed unique import key because some rows have a blank `NomId`.
- Deduplicate repeated nominee links within the same nomination during import if the source row repeats the same person.
- Treat placeholder IDs like `?` as missing IDs during import so unrelated nominees are not merged.

## Why this schema works well for the assignment

- It preserves the source data cleanly enough for exact counting queries.
- It supports the profile app without denormalizing the dataset.
- It supports the three findings in Task 2.3 with ORM queries only.
- It avoids raw SQL entirely.
