from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class NominationPerson(Base):
    __tablename__ = "nomination_people"

    nomination_id: Mapped[int] = mapped_column(ForeignKey("nominations.id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    credit_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    nomination: Mapped["Nomination"] = relationship(back_populates="nomination_people")
    person: Mapped["Person"] = relationship(back_populates="nomination_people")


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_person_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    nomination_people: Mapped[List[NominationPerson]] = relationship(back_populates="person", cascade="all, delete-orphan")
    nominations: Mapped[List["Nomination"]] = relationship(
        secondary="nomination_people",
        back_populates="people",
        viewonly=True,
    )


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_film_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    nominations: Mapped[List["Nomination"]] = relationship(back_populates="film")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    award_class: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    nominations: Mapped[List["Nomination"]] = relationship(back_populates="category")


class Ceremony(Base):
    __tablename__ = "ceremonies"
    __table_args__ = (
        UniqueConstraint("ceremony_number", name="uq_ceremonies_ceremony_number"),
        CheckConstraint("ceremony_number > 0", name="ck_ceremonies_positive_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ceremony_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    year_label: Mapped[str] = mapped_column(String(20), nullable=False)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    nominations: Mapped[List["Nomination"]] = relationship(back_populates="ceremony")


class Nomination(Base):
    __tablename__ = "nominations"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    source_nomination_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    film_id: Mapped[Optional[int]] = mapped_column(ForeignKey("films.id"), nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    ceremony_id: Mapped[int] = mapped_column(ForeignKey("ceremonies.id"), nullable=False, index=True)

    name_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nominees_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nominee_ids_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    winner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    multifilm_nomination: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    film: Mapped[Optional[Film]] = relationship(back_populates="nominations")
    category: Mapped[Category] = relationship(back_populates="nominations")
    ceremony: Mapped[Ceremony] = relationship(back_populates="nominations")
    nomination_people: Mapped[List[NominationPerson]] = relationship(
        back_populates="nomination",
        cascade="all, delete-orphan",
    )
    people: Mapped[List[Person]] = relationship(
        secondary="nomination_people",
        back_populates="nominations",
        viewonly=True,
    )
