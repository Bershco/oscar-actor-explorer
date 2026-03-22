from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import random
from typing import Iterable

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.db import SessionLocal
from app.models import Category, Nomination, NominationPerson, Person
from app.wiki import WikipediaProfile, fetch_wikipedia_profile


@dataclass
class CategoryComparison:
    category_id: int
    category_name: str
    person_nominations: int
    average_nominations: float
    person_wins: int
    average_wins: float


@dataclass
class PersonProfile:
    person_id: int
    name: str
    exact_name_match_count: int
    nominations_count: int
    wins_count: int
    categories: list[str]
    year_labels: list[str]
    nominated_films: list[str]
    winning_films: list[str]
    win_rate: float | None
    years_to_first_win: int | None
    category_comparisons: list[CategoryComparison]
    wikipedia: WikipediaProfile
    fun_fact: str | None


def empty_wikipedia_profile() -> WikipediaProfile:
    return WikipediaProfile(
        status="pending",
        title=None,
        summary=None,
        birth_date=None,
        photo_url=None,
        page_url=None,
        message="Loading Wikipedia data...",
    )


def nomination_sort_key(nomination: Nomination) -> tuple[int, int, int]:
    return (
        nomination.ceremony.year_start if nomination.ceremony.year_start is not None else 9999,
        nomination.ceremony.ceremony_number,
        nomination.id,
    )


def get_person_nominations(session: Session, person_id: int) -> list[Nomination]:
    return session.scalars(
        select(Nomination)
        .join(NominationPerson, NominationPerson.nomination_id == Nomination.id)
        .where(NominationPerson.person_id == person_id)
        .options(
            joinedload(Nomination.category),
            joinedload(Nomination.ceremony),
            joinedload(Nomination.film),
        )
        .order_by(Nomination.ceremony_id.asc(), Nomination.id.asc())
    ).all()


def unique_sorted_values(values: Iterable[str]) -> list[str]:
    return sorted(set(values))


def ordered_year_labels(nominations: list[Nomination]) -> list[str]:
    ordered: dict[str, None] = {}
    for nomination in sorted(nominations, key=nomination_sort_key):
        ordered[nomination.ceremony.year_label] = None
    return list(ordered.keys())


def first_year(nominations: list[Nomination], wins_only: bool = False) -> int | None:
    for nomination in sorted(nominations, key=nomination_sort_key):
        if wins_only and not nomination.winner:
            continue
        if nomination.ceremony.year_start is not None:
            return nomination.ceremony.year_start
    return None


def count_exact_name_matches(session: Session, name: str) -> int:
    return session.scalar(
        select(func.count())
        .select_from(Person)
        .where(func.lower(Person.name) == name.lower())
    ) or 0


def suggest_people(session: Session, query_text: str, limit: int = 8) -> list[Person]:
    query_text = query_text.strip()
    if not query_text:
        return []

    prefix_matches = session.scalars(
        select(Person)
        .where(Person.name.ilike(f"{query_text}%"))
        .order_by(Person.name.asc(), Person.id.asc())
        .limit(limit)
    ).all()
    if prefix_matches:
        return prefix_matches

    return session.scalars(
        select(Person)
        .where(Person.name.ilike(f"%{query_text}%"))
        .order_by(Person.name.asc(), Person.id.asc())
        .limit(limit)
    ).all()
def get_person_profile(session: Session, person_id: int, include_wikipedia: bool = True) -> PersonProfile | None:
    person = session.get(Person, person_id)
    if person is None:
        return None

    nominations = get_person_nominations(session, person_id)
    wikipedia = fetch_wikipedia_profile(person.name) if include_wikipedia else empty_wikipedia_profile()

    if not nominations:
        return PersonProfile(
            person_id=person.id,
            name=person.name,
            exact_name_match_count=count_exact_name_matches(session, person.name),
            nominations_count=0,
            wins_count=0,
            categories=[],
            year_labels=[],
            nominated_films=[],
            winning_films=[],
            win_rate=None,
            years_to_first_win=None,
            category_comparisons=[],
            wikipedia=wikipedia,
            fun_fact=None,
        )

    categories = unique_sorted_values(nomination.category.display_name for nomination in nominations)
    nominated_films = unique_sorted_values(
        nomination.film.title for nomination in nominations if nomination.film is not None
    )
    winning_films = unique_sorted_values(
        nomination.film.title for nomination in nominations if nomination.winner and nomination.film is not None
    )
    wins_count = sum(1 for nomination in nominations if nomination.winner)
    win_rate = wins_count / len(nominations)

    first_nomination_year = first_year(nominations)
    first_win_year = first_year(nominations, wins_only=True)
    years_to_first_win = None if first_win_year is None or first_nomination_year is None else first_win_year - first_nomination_year

    category_comparisons = get_category_comparisons(session, person_id, nominations)

    return PersonProfile(
        person_id=person.id,
        name=person.name,
        exact_name_match_count=count_exact_name_matches(session, person.name),
        nominations_count=len(nominations),
        wins_count=wins_count,
        categories=categories,
        year_labels=ordered_year_labels(nominations),
        nominated_films=nominated_films,
        winning_films=winning_films,
        win_rate=win_rate,
        years_to_first_win=years_to_first_win,
        category_comparisons=category_comparisons,
        wikipedia=wikipedia,
        fun_fact=choose_fun_fact(
            session=session,
            nominations_count=len(nominations),
            wins_count=wins_count,
            categories=categories,
            years_to_first_win=years_to_first_win,
            nominated_films=nominated_films,
            winning_films=winning_films,
            year_labels=ordered_year_labels(nominations),
            category_comparisons=category_comparisons,
        ),
    )


def get_category_comparisons(session: Session, person_id: int, nominations: list[Nomination]) -> list[CategoryComparison]:
    person_counts: dict[int, tuple[int, int]] = {}
    for nomination in nominations:
        nominations_count, wins_count = person_counts.get(nomination.category_id, (0, 0))
        person_counts[nomination.category_id] = (
            nominations_count + 1,
            wins_count + (1 if nomination.winner else 0),
        )

    if not person_counts:
        return []

    grouped_rows = session.execute(
        select(
            Category.id,
            Category.display_name,
            NominationPerson.person_id,
            func.count(Nomination.id).label("nomination_count"),
            func.sum(case((Nomination.winner.is_(True), 1), else_=0)).label("win_count"),
        )
        .join(Nomination, Nomination.category_id == Category.id)
        .join(NominationPerson, NominationPerson.nomination_id == Nomination.id)
        .where(Category.id.in_(person_counts.keys()))
        .group_by(Category.id, Category.display_name, NominationPerson.person_id)
        .order_by(Category.display_name.asc(), NominationPerson.person_id.asc())
    ).all()

    category_people_stats: dict[int, tuple[str, list[int], list[int]]] = {}
    for category_id, category_name, _, nomination_count, win_count in grouped_rows:
        saved_name, nomination_counts, win_counts = category_people_stats.get(category_id, (category_name, [], []))
        nomination_counts.append(nomination_count)
        win_counts.append(win_count or 0)
        category_people_stats[category_id] = (saved_name, nomination_counts, win_counts)

    comparisons: list[CategoryComparison] = []
    for category_id, (category_name, nomination_counts, win_counts) in category_people_stats.items():
        person_nominations, person_wins = person_counts[category_id]
        comparisons.append(
            CategoryComparison(
                category_id=category_id,
                category_name=category_name,
                person_nominations=person_nominations,
                average_nominations=sum(nomination_counts) / len(nomination_counts),
                person_wins=person_wins,
                average_wins=sum(win_counts) / len(win_counts),
            )
        )

    comparisons.sort(key=lambda item: item.category_name)
    return comparisons


def choose_fun_fact(
    session: Session,
    nominations_count: int,
    wins_count: int,
    categories: list[str],
    years_to_first_win: int | None,
    nominated_films: list[str],
    winning_films: list[str],
    year_labels: list[str],
    category_comparisons: list[CategoryComparison],
) -> str | None:
    if nominations_count <= 0:
        return None

    facts: list[str] = []

    total_people, nomination_counts = get_nomination_count_distribution(session)
    if total_people > 0:
        people_below = sum(1 for count in nomination_counts if count < nominations_count)
        percentile = round((people_below / total_people) * 100)
        facts.append(
            f"This person has more nominations than {percentile}% of Oscar-nominated individuals in this dataset."
        )
        if percentile >= 95:
            facts.append("This person's nomination total is a real outlier in the Oscar dataset.")

    total_people, win_counts = get_win_count_distribution(session)
    if total_people > 0 and wins_count > 0:
        people_below = sum(1 for count in win_counts if count < wins_count)
        percentile = round((people_below / total_people) * 100)
        facts.append(
            f"This person has more Oscar wins than {percentile}% of Oscar-nominated individuals in this dataset."
        )
        if percentile >= 90:
            facts.append("Their Oscar win total puts them in a very small top slice of nominees in this dataset.")

    total_people, category_counts = get_category_count_distribution(session)
    if total_people > 0 and categories:
        people_below = sum(1 for count in category_counts if count < len(categories))
        percentile = round((people_below / total_people) * 100)
        facts.append(
            f"This person was nominated in more distinct Oscar categories than {percentile}% of Oscar-nominated individuals in this dataset."
        )

    total_people, film_counts = get_film_count_distribution(session)
    if total_people > 0 and nominated_films:
        people_below = sum(1 for count in film_counts if count < len(nominated_films))
        percentile = round((people_below / total_people) * 100)
        facts.append(
            f"This person is tied to nominations across more films than {percentile}% of Oscar-nominated individuals in this dataset."
        )

    total_people, ceremony_counts = get_ceremony_span_distribution(session)
    if total_people > 0 and year_labels:
        people_below = sum(1 for count in ceremony_counts if count < len(year_labels))
        percentile = round((people_below / total_people) * 100)
        facts.append(
            f"This person's Oscar activity spans more ceremonies than {percentile}% of Oscar-nominated individuals in this dataset."
        )

    if years_to_first_win is not None and years_to_first_win > 0:
        total_people, gap_counts = get_years_to_first_win_distribution(session)
        if total_people > 0:
            people_below = sum(1 for count in gap_counts if count < years_to_first_win)
            percentile = round((people_below / total_people) * 100)
            facts.append(
                f"This person's wait to a first Oscar win was longer than {percentile}% of eventual Oscar winners in this dataset."
            )
            if percentile >= 90:
                facts.append("Their path to a first Oscar win is an outlier compared with most eventual winners.")

    category_percentile_facts = build_category_percentile_facts(session, category_comparisons)
    facts.extend(category_percentile_facts)

    better_than_average_categories = sum(
        1
        for comparison in category_comparisons
        if comparison.person_nominations > comparison.average_nominations
        or comparison.person_wins > comparison.average_wins
    )
    if better_than_average_categories > 0:
        facts.append(
            f"They outperform the average nominee in {better_than_average_categories} of their Oscar categories."
        )

    if better_than_average_categories == 0 and categories:
        facts.append(
            "Their Oscar record is concentrated in categories where they are close to or below the average nominee profile."
        )

    if winning_films and wins_count > 0:
        facts.append(
            f"Their wins are spread across {len(winning_films)} different films rather than coming from just one title."
        )

    if wins_count == 0:
        facts.append("They are still searching for a first Oscar win despite multiple nominations in the dataset.")

    if not facts:
        return None

    return random.choice(facts)


def build_category_percentile_facts(session: Session, category_comparisons: list[CategoryComparison]) -> list[str]:
    category_stats = get_category_person_distributions(session)
    facts: list[str] = []

    for comparison in category_comparisons:
        counts = category_stats.get(comparison.category_id)
        if not counts:
            continue
        nomination_counts, win_counts = counts
        if nomination_counts:
            people_below = sum(1 for count in nomination_counts if count < comparison.person_nominations)
            percentile = round((people_below / len(nomination_counts)) * 100)
            if percentile >= 75:
                facts.append(
                    f"In {comparison.category_name.title()}, this person has more nominations than {percentile}% of other Oscar nominees in that category."
                )
        if comparison.person_wins > 0 and win_counts:
            people_below = sum(1 for count in win_counts if count < comparison.person_wins)
            percentile = round((people_below / len(win_counts)) * 100)
            if percentile >= 75:
                facts.append(
                    f"In {comparison.category_name.title()}, this person has more wins than {percentile}% of other Oscar nominees in that category."
                )

    return facts


@lru_cache(maxsize=1)
def _cached_nomination_count_distribution(_db_path: str) -> tuple[int, tuple[int, ...]]:
    with SessionLocal() as session:
        rows = session.execute(
            select(func.count(Nomination.id).label("nomination_count"))
            .select_from(NominationPerson)
            .join(Nomination, Nomination.id == NominationPerson.nomination_id)
            .join(Person, Person.id == NominationPerson.person_id)
            .where(Person.source_person_id.like("nm%"))
            .group_by(NominationPerson.person_id)
        ).all()
    counts = tuple(row.nomination_count for row in rows)
    return len(counts), counts


def get_nomination_count_distribution(session: Session) -> tuple[int, tuple[int, ...]]:
    bind = session.get_bind()
    database_url = str(bind.url) if bind is not None else "sqlite:///unknown"
    return _cached_nomination_count_distribution(database_url)


@lru_cache(maxsize=1)
def _cached_win_count_distribution(_db_path: str) -> tuple[int, tuple[int, ...]]:
    with SessionLocal() as session:
        rows = session.execute(
            select(func.sum(case((Nomination.winner.is_(True), 1), else_=0)).label("win_count"))
            .select_from(NominationPerson)
            .join(Nomination, Nomination.id == NominationPerson.nomination_id)
            .join(Person, Person.id == NominationPerson.person_id)
            .where(Person.source_person_id.like("nm%"))
            .group_by(NominationPerson.person_id)
        ).all()
    counts = tuple((row.win_count or 0) for row in rows)
    return len(counts), counts


def get_win_count_distribution(session: Session) -> tuple[int, tuple[int, ...]]:
    bind = session.get_bind()
    database_url = str(bind.url) if bind is not None else "sqlite:///unknown"
    return _cached_win_count_distribution(database_url)


@lru_cache(maxsize=1)
def _cached_category_count_distribution(_db_path: str) -> tuple[int, tuple[int, ...]]:
    with SessionLocal() as session:
        rows = session.execute(
            select(func.count(func.distinct(Nomination.category_id)).label("category_count"))
            .select_from(NominationPerson)
            .join(Nomination, Nomination.id == NominationPerson.nomination_id)
            .join(Person, Person.id == NominationPerson.person_id)
            .where(Person.source_person_id.like("nm%"))
            .group_by(NominationPerson.person_id)
        ).all()
    counts = tuple(row.category_count for row in rows)
    return len(counts), counts


def get_category_count_distribution(session: Session) -> tuple[int, tuple[int, ...]]:
    bind = session.get_bind()
    database_url = str(bind.url) if bind is not None else "sqlite:///unknown"
    return _cached_category_count_distribution(database_url)


@lru_cache(maxsize=1)
def _cached_film_count_distribution(_db_path: str) -> tuple[int, tuple[int, ...]]:
    with SessionLocal() as session:
        rows = session.execute(
            select(func.count(func.distinct(Nomination.film_id)).label("film_count"))
            .select_from(NominationPerson)
            .join(Nomination, Nomination.id == NominationPerson.nomination_id)
            .join(Person, Person.id == NominationPerson.person_id)
            .where(Person.source_person_id.like("nm%"))
            .group_by(NominationPerson.person_id)
        ).all()
    counts = tuple(row.film_count for row in rows)
    return len(counts), counts


def get_film_count_distribution(session: Session) -> tuple[int, tuple[int, ...]]:
    bind = session.get_bind()
    database_url = str(bind.url) if bind is not None else "sqlite:///unknown"
    return _cached_film_count_distribution(database_url)


@lru_cache(maxsize=1)
def _cached_ceremony_span_distribution(_db_path: str) -> tuple[int, tuple[int, ...]]:
    with SessionLocal() as session:
        rows = session.execute(
            select(func.count(func.distinct(Nomination.ceremony_id)).label("ceremony_count"))
            .select_from(NominationPerson)
            .join(Nomination, Nomination.id == NominationPerson.nomination_id)
            .join(Person, Person.id == NominationPerson.person_id)
            .where(Person.source_person_id.like("nm%"))
            .group_by(NominationPerson.person_id)
        ).all()
    counts = tuple(row.ceremony_count for row in rows)
    return len(counts), counts


def get_ceremony_span_distribution(session: Session) -> tuple[int, tuple[int, ...]]:
    bind = session.get_bind()
    database_url = str(bind.url) if bind is not None else "sqlite:///unknown"
    return _cached_ceremony_span_distribution(database_url)


@lru_cache(maxsize=1)
def _cached_years_to_first_win_distribution(_db_path: str) -> tuple[int, tuple[int, ...]]:
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Person.id,
                Nomination.winner,
                Nomination.ceremony_id,
            )
            .select_from(NominationPerson)
            .join(Person, Person.id == NominationPerson.person_id)
            .join(Nomination, Nomination.id == NominationPerson.nomination_id)
            .where(Person.source_person_id.like("nm%"))
            .order_by(Person.id.asc(), Nomination.ceremony_id.asc())
        ).all()

    from collections import defaultdict

    by_person = defaultdict(list)
    for person_id, winner, ceremony_id in rows:
        by_person[person_id].append((ceremony_id, bool(winner)))

    gaps: list[int] = []
    for values in by_person.values():
        first_nom = values[0][0]
        first_win = next((ceremony_id for ceremony_id, winner in values if winner), None)
        if first_win is not None:
            gaps.append(first_win - first_nom)
    return len(gaps), tuple(gaps)


def get_years_to_first_win_distribution(session: Session) -> tuple[int, tuple[int, ...]]:
    bind = session.get_bind()
    database_url = str(bind.url) if bind is not None else "sqlite:///unknown"
    return _cached_years_to_first_win_distribution(database_url)


@lru_cache(maxsize=1)
def _cached_category_person_distributions(_db_path: str) -> dict[int, tuple[tuple[int, ...], tuple[int, ...]]]:
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Nomination.category_id,
                NominationPerson.person_id,
                func.count(Nomination.id).label("nomination_count"),
                func.sum(case((Nomination.winner.is_(True), 1), else_=0)).label("win_count"),
            )
            .select_from(NominationPerson)
            .join(Nomination, Nomination.id == NominationPerson.nomination_id)
            .join(Person, Person.id == NominationPerson.person_id)
            .where(Person.source_person_id.like("nm%"))
            .group_by(Nomination.category_id, NominationPerson.person_id)
        ).all()

    distributions: dict[int, tuple[list[int], list[int]]] = {}
    for category_id, _, nomination_count, win_count in rows:
        nomination_counts, win_counts = distributions.get(category_id, ([], []))
        nomination_counts.append(nomination_count)
        win_counts.append(win_count or 0)
        distributions[category_id] = (nomination_counts, win_counts)

    return {
        category_id: (tuple(nomination_counts), tuple(win_counts))
        for category_id, (nomination_counts, win_counts) in distributions.items()
    }


def get_category_person_distributions(session: Session) -> dict[int, tuple[tuple[int, ...], tuple[int, ...]]]:
    bind = session.get_bind()
    database_url = str(bind.url) if bind is not None else "sqlite:///unknown"
    return _cached_category_person_distributions(database_url)
