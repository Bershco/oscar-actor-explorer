from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from app.db import DEFAULT_DB_PATH, configure_session, get_engine, SessionLocal
from app.models import Base, Category, Ceremony, Film, Nomination, NominationPerson, Person


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "full_data.csv"


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def normalize_identifier(value: str | None) -> str | None:
    cleaned = normalize_text(value)
    if cleaned in {None, "?"}:
        return None
    return cleaned


def parse_bool(value: str | None) -> bool:
    return normalize_text(value) == "True"


def parse_year_start(year_label: str | None) -> int | None:
    text = normalize_text(year_label)
    if not text:
        return None
    digits = []
    for char in text:
        if char.isdigit():
            digits.append(char)
            if len(digits) == 4:
                return int("".join(digits))
        else:
            if digits:
                break
    return None


def split_people(names_text: str | None, ids_text: str | None) -> list[tuple[str | None, str]]:
    names = [item.strip() for item in (names_text or "").split(",") if item.strip()]
    ids = [item.strip() for item in (ids_text or "").split(",") if item.strip()]

    if names and ids and len(names) == len(ids):
        return list(zip(ids, names))
    if names and not ids:
        return [(None, name) for name in names]
    if len(names) == 1 and ids:
        return [(person_id, names[0]) for person_id in ids]
    if not names and ids:
        return [(person_id, f"Unknown nominee {person_id}") for person_id in ids]
    return []


def person_identity_key(source_person_id: str | None, name: str) -> tuple[str, str]:
    normalized_id = normalize_identifier(source_person_id)
    if normalized_id:
        return ("source", normalized_id)
    return ("name", name)


def get_or_create_person(session, cache: dict[tuple[str, str], Person], source_person_id: str | None, name: str) -> Person:
    key = person_identity_key(source_person_id, name)
    person = cache.get(key)
    if person is not None:
        return person

    normalized_id = normalize_identifier(source_person_id)
    if normalized_id:
        person = session.query(Person).filter_by(source_person_id=normalized_id).one_or_none()
    else:
        person = session.query(Person).filter_by(name=name, source_person_id=None).one_or_none()

    if person is None:
        person = Person(source_person_id=normalized_id, name=name)
        session.add(person)

    cache[key] = person
    return person


def get_or_create_film(session, cache: dict[tuple[str, str], Film], source_film_id: str | None, title: str | None) -> Film | None:
    title = normalize_text(title)
    if not title:
        return None

    key = ("source", source_film_id) if source_film_id else ("title", title)
    film = cache.get(key)
    if film is not None:
        return film

    if source_film_id:
        film = session.query(Film).filter_by(source_film_id=source_film_id).one_or_none()
    else:
        film = session.query(Film).filter_by(title=title, source_film_id=None).one_or_none()

    if film is None:
        film = Film(source_film_id=source_film_id, title=title)
        session.add(film)

    cache[key] = film
    return film


def get_or_create_category(session, cache: dict[str, Category], award_class: str, canonical_name: str, display_name: str) -> Category:
    category = cache.get(canonical_name)
    if category is not None:
        return category

    category = session.query(Category).filter_by(canonical_name=canonical_name).one_or_none()
    if category is None:
        category = Category(
            award_class=award_class,
            canonical_name=canonical_name,
            display_name=display_name,
        )
        session.add(category)

    cache[canonical_name] = category
    return category


def get_or_create_ceremony(session, cache: dict[int, Ceremony], ceremony_number: int, year_label: str) -> Ceremony:
    ceremony = cache.get(ceremony_number)
    if ceremony is not None:
        return ceremony

    ceremony = session.query(Ceremony).filter_by(ceremony_number=ceremony_number).one_or_none()
    if ceremony is None:
        ceremony = Ceremony(
            ceremony_number=ceremony_number,
            year_label=year_label,
            year_start=parse_year_start(year_label),
        )
        session.add(ceremony)

    cache[ceremony_number] = ceremony
    return ceremony


def load_rows(dataset_path: Path) -> Iterable[dict[str, str]]:
    with dataset_path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def create_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    engine = get_engine(db_path=db_path)
    Base.metadata.create_all(engine)


def load_dataset(dataset_path: Path = DATASET_PATH, db_path: Path = DEFAULT_DB_PATH) -> None:
    configure_session(db_path=db_path)
    engine = get_engine(db_path=db_path)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    person_cache: dict[tuple[str, str], Person] = {}
    film_cache: dict[tuple[str, str], Film] = {}
    category_cache: dict[str, Category] = {}
    ceremony_cache: dict[int, Ceremony] = {}

    with SessionLocal() as session:
        for row_number, row in enumerate(load_rows(dataset_path), start=1):
            ceremony_number = int(row["Ceremony"])
            year_label = normalize_text(row["Year"]) or ""
            award_class = normalize_text(row["Class"]) or "Unknown"
            canonical_name = normalize_text(row["CanonicalCategory"]) or "Unknown"
            display_name = normalize_text(row["Category"]) or canonical_name

            category = get_or_create_category(session, category_cache, award_class, canonical_name, display_name)
            ceremony = get_or_create_ceremony(session, ceremony_cache, ceremony_number, year_label)
            film = get_or_create_film(
                session,
                film_cache,
                normalize_identifier(row["FilmId"]),
                row["Film"],
            )

            nomination = Nomination(
                source_row_number=row_number,
                source_nomination_id=normalize_text(row["NomId"]),
                film=film,
                category=category,
                ceremony=ceremony,
                name_text=normalize_text(row["Name"]),
                nominees_text=normalize_text(row["Nominees"]),
                nominee_ids_text=normalize_text(row["NomineeIds"]),
                winner=parse_bool(row["Winner"]),
                detail=normalize_text(row["Detail"]),
                note=normalize_text(row["Note"]),
                citation=normalize_text(row["Citation"]),
                multifilm_nomination=parse_bool(row["MultifilmNomination"]),
            )
            session.add(nomination)
            session.flush()

            people = split_people(nomination.nominees_text or nomination.name_text, nomination.nominee_ids_text)
            seen_people: set[tuple[str, str]] = set()
            for index, (source_person_id, person_name) in enumerate(people, start=1):
                dedupe_key = person_identity_key(source_person_id, person_name)
                if dedupe_key in seen_people:
                    continue
                seen_people.add(dedupe_key)
                person = get_or_create_person(session, person_cache, source_person_id, person_name)
                nomination.nomination_people.append(NominationPerson(person=person, credit_order=index))

        session.commit()


if __name__ == "__main__":
    load_dataset()
    print(f"SQLite database created at: {DEFAULT_DB_PATH}")
