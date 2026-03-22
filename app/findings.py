from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db import DEFAULT_DB_PATH, SessionLocal, configure_session
from app.models import Category, Ceremony, Nomination, NominationPerson, Person


@dataclass
class Finding:
    title: str
    result: str
    how_found: str
    why_interesting: str


def top_nominations_without_win(session: Session) -> Finding:
    row = session.execute(
        select(
            Person.name,
            func.count(Nomination.id).label("nominations"),
        )
        .join(NominationPerson, NominationPerson.person_id == Person.id)
        .join(Nomination, Nomination.id == NominationPerson.nomination_id)
        .where(Person.source_person_id.like("nm%"))
        .group_by(Person.id, Person.name)
        .having(func.sum(case((Nomination.winner.is_(True), 1), else_=0)) == 0)
        .order_by(func.count(Nomination.id).desc(), Person.name.asc())
        .limit(1)
    ).one()

    return Finding(
        title="Most nominations without a win",
        result=f"{row.name} has {row.nominations} Oscar nominations and 0 wins.",
        how_found=(
            "Grouped nominations by person, filtered to individual nominees "
            "(`source_person_id` starting with `nm`), kept only people whose summed "
            "winner flag was 0, then ordered by nomination count descending."
        ),
        why_interesting="It highlights sustained Academy recognition without a single win.",
    )


def longest_gap_to_first_win(session: Session) -> Finding:
    rows = session.execute(
        select(
            Person.id,
            Person.name,
            Ceremony.year_start,
            Ceremony.year_label,
            Nomination.winner,
        )
        .join(NominationPerson, NominationPerson.person_id == Person.id)
        .join(Nomination, Nomination.id == NominationPerson.nomination_id)
        .join(Ceremony, Ceremony.id == Nomination.ceremony_id)
        .where(Person.source_person_id.like("nm%"))
        .order_by(Person.id.asc(), Ceremony.year_start.asc(), Ceremony.ceremony_number.asc(), Nomination.id.asc())
    ).all()

    current_person_id = None
    current_name = None
    first_nomination: tuple[int, str] | None = None
    first_win: tuple[int, str] | None = None
    best_gap: tuple[int, str, str, str] | None = None

    for person_id, name, year_start, year_label, winner in rows:
        if person_id != current_person_id:
            if first_nomination and first_win:
                gap = first_win[0] - first_nomination[0]
                candidate = (gap, current_name, first_nomination[1], first_win[1])
                if best_gap is None or candidate[0] > best_gap[0]:
                    best_gap = candidate
            current_person_id = person_id
            current_name = name
            first_nomination = None
            first_win = None

        if year_start is not None and first_nomination is None:
            first_nomination = (year_start, year_label)
        if year_start is not None and winner and first_win is None:
            first_win = (year_start, year_label)

    if first_nomination and first_win:
        gap = first_win[0] - first_nomination[0]
        candidate = (gap, current_name, first_nomination[1], first_win[1])
        if best_gap is None or candidate[0] > best_gap[0]:
            best_gap = candidate

    assert best_gap is not None

    return Finding(
        title="Longest wait from first nomination to first win",
        result=(
            f"{best_gap[1]} waited {best_gap[0]} years, from the {best_gap[2]} ceremony "
            f"to the {best_gap[3]} ceremony, for a first Oscar win."
        ),
        how_found=(
            "Loaded each individual nominee's nominations ordered by ceremony year, "
            "took the first nomination year and the first winning year for each person, "
            "computed the year gap in Python, and selected the maximum."
        ),
        why_interesting="It shows how long Oscar recognition can take, even for eventual winners.",
    )


def broadest_category_range(session: Session) -> Finding:
    row = session.execute(
        select(
            Person.id,
            Person.name,
            func.count(func.distinct(Category.display_name)).label("category_count"),
        )
        .join(NominationPerson, NominationPerson.person_id == Person.id)
        .join(Nomination, Nomination.id == NominationPerson.nomination_id)
        .join(Category, Category.id == Nomination.category_id)
        .where(Person.source_person_id.like("nm%"))
        .group_by(Person.id, Person.name)
        .order_by(func.count(func.distinct(Category.display_name)).desc(), func.count(Nomination.id).desc(), Person.name.asc())
        .limit(1)
    ).one()

    categories = session.execute(
        select(Category.display_name)
        .join(Nomination, Nomination.category_id == Category.id)
        .join(NominationPerson, NominationPerson.nomination_id == Nomination.id)
        .where(NominationPerson.person_id == row.id)
        .group_by(Category.display_name)
        .order_by(Category.display_name.asc())
    ).scalars().all()

    return Finding(
        title="Broadest category range for an individual nominee",
        result=f"{row.name} appears in {row.category_count} distinct Oscar categories: {', '.join(categories)}.",
        how_found=(
            "Joined people to nominations and categories, counted distinct category names "
            "per individual nominee, ordered descending, then fetched that person's category list."
        ),
        why_interesting="It highlights an unusually broad Oscar footprint across very different types of work.",
    )


def candidate_findings_summary() -> list[tuple[int, str, str]]:
    return [
        (1, "Most nominations without a win", "Strong, simple, and directly comparable across the whole dataset."),
        (2, "Longest wait from first nomination to first win", "Time-based and memorable, with a clear verification path."),
        (3, "Broadest category range for an individual nominee", "Shows unusual career breadth across multiple Oscar categories."),
        (4, "People nominated in both acting and directing", "Relevant to the actor/director app, but less striking than the top three."),
        (5, "Modern high-profile nominees with many losses", "Readable, but overlaps too much with the no-win finding."),
    ]


def best_findings(session: Session) -> list[Finding]:
    return [
        top_nominations_without_win(session),
        longest_gap_to_first_win(session),
        broadest_category_range(session),
    ]


def build_report() -> str:
    configure_session(DEFAULT_DB_PATH)
    lines = ["# Task 2.3 Findings", "", "## Candidate Findings Ranked"]

    for rank, title, reason in candidate_findings_summary():
        lines.append(f"{rank}. {title}")
        lines.append(f"   Reason: {reason}")

    lines.extend(["", "## Selected Findings"])

    with SessionLocal() as session:
        for index, finding in enumerate(best_findings(session), start=1):
            lines.append(f"### Finding {index}: {finding.title}")
            lines.append(f"- Finding: {finding.result}")
            lines.append(f"- How it was found: {finding.how_found}")
            lines.append(f"- Why it is interesting: {finding.why_interesting}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    print(build_report())


if __name__ == "__main__":
    main()
