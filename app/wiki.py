from __future__ import annotations

import re
from functools import lru_cache
from dataclasses import dataclass
from difflib import SequenceMatcher

from bs4 import BeautifulSoup
import wikipedia


@dataclass
class WikipediaAlternative:
    title: str
    url: str | None = None


@dataclass
class WikipediaProfile:
    status: str
    title: str | None
    summary: str | None
    birth_date: str | None
    photo_url: str | None
    page_url: str | None
    photo_caption: str | None = None
    message: str | None = None
    options: list[str] | None = None
    note: str | None = None
    alternatives: list[WikipediaAlternative] | None = None
    shared_name_ambiguity: bool = False


@lru_cache(maxsize=512)
def fetch_wikipedia_profile(name: str) -> WikipediaProfile:
    try:
        search_results = wikipedia.search(name, results=5)
        if not search_results:
            return WikipediaProfile(
                status="not_found",
                title=None,
                summary=None,
                birth_date=None,
                photo_url=None,
                page_url=None,
                message="No Wikipedia result found.",
            )

        chosen_title = next((item for item in search_results if item.lower() == name.lower()), search_results[0])
        return build_profile_from_title(chosen_title)
    except wikipedia.exceptions.DisambiguationError as exc:
        return resolve_disambiguation(name, exc.options[:8])
    except wikipedia.exceptions.PageError:
        return WikipediaProfile(
            status="not_found",
            title=None,
            summary=None,
            birth_date=None,
            photo_url=None,
            page_url=None,
            message="No Wikipedia page found.",
        )
    except Exception as exc:
        return WikipediaProfile(
            status="error",
            title=None,
            summary=None,
            birth_date=None,
            photo_url=None,
            page_url=None,
            message=f"Wikipedia lookup failed: {exc}",
        )


def build_profile_from_title(title: str, message: str | None = None, note: str | None = None, alternatives: list[WikipediaAlternative] | None = None, shared_name_ambiguity: bool = False) -> WikipediaProfile:
    page = wikipedia.page(title, auto_suggest=False)
    summary = page.summary
    html = page.html()
    birth_date = extract_birth_date(html, summary)
    photo_url, photo_caption = extract_primary_photo(html, page.images, page.title)
    return WikipediaProfile(
        status="ok",
        title=page.title,
        summary=summary,
        birth_date=birth_date,
        photo_url=photo_url,
        photo_caption=photo_caption,
        page_url=page.url,
        message=message,
        note=note,
        alternatives=alternatives,
        shared_name_ambiguity=shared_name_ambiguity,
    )


def resolve_disambiguation(search_name: str, options: list[str]) -> WikipediaProfile:
    evaluated = [candidate for option in options if (candidate := evaluate_option(search_name, option)) is not None]
    if not evaluated:
        return WikipediaProfile(
            status="ambiguous",
            title=None,
            summary=None,
            birth_date=None,
            photo_url=None,
            page_url=None,
            message="Wikipedia returned an ambiguous result.",
            options=options[:5],
        )

    oscar_related = [candidate for candidate in evaluated if candidate["is_oscar_related"]]
    pool = oscar_related or evaluated
    chosen = sorted(pool, key=lambda candidate: (-candidate["score"], candidate["title"]))[0]

    same_name_candidates = [
        candidate for candidate in pool
        if normalize_base_title(candidate["title"]) == normalize_base_title(chosen["title"])
    ]
    shared_name_ambiguity = len(same_name_candidates) > 1

    alternatives = [
        WikipediaAlternative(title=candidate["title"], url=candidate["url"])
        for candidate in sorted(pool, key=lambda candidate: (-candidate["score"], candidate["title"]))
        if candidate["title"] != chosen["title"]
    ][:4]

    if len(oscar_related) == 1:
        note = "Wikipedia returned multiple results, but only one appeared Oscar-related, so it was selected automatically."
    elif len(oscar_related) >= 2:
        note = "Wikipedia returned multiple Oscar-related results. The closest name match was selected automatically."
    else:
        note = "Wikipedia returned multiple results. The closest name match was selected automatically."

    if shared_name_ambiguity:
        note = f"{note} Multiple Oscar-related pages share this name."

    return build_profile_from_title(
        chosen["title"],
        message="Wikipedia result was resolved automatically.",
        note=note,
        alternatives=alternatives,
        shared_name_ambiguity=shared_name_ambiguity,
    )


def evaluate_option(search_name: str, option_title: str) -> dict[str, object] | None:
    try:
        page = wikipedia.page(option_title, auto_suggest=False)
    except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
        return None

    summary = (page.summary or "").lower()
    base_title = normalize_base_title(page.title)
    query_base = normalize_base_title(search_name)
    similarity = SequenceMatcher(None, query_base, base_title).ratio()
    exact_base_match = 1.0 if base_title == query_base else 0.0
    oscar_related = is_oscar_related(page.title.lower(), summary)

    score = exact_base_match * 10 + similarity * 5 + (3 if oscar_related else 0)
    return {
        "title": page.title,
        "url": page.url,
        "score": score,
        "is_oscar_related": oscar_related,
    }


def is_oscar_related(title: str, summary: str) -> bool:
    text = f"{title} {summary}"
    keywords = (
        "academy award",
        "oscar",
        "actor",
        "actress",
        "director",
        "filmmaker",
        "screenwriter",
        "producer",
        "cinematographer",
        "composer",
        "film editor",
        "film producer",
        "motion picture",
        "hollywood",
    )
    return any(keyword in text for keyword in keywords)


def normalize_base_title(value: str) -> str:
    base = re.sub(r"\s*\([^)]*\)\s*", "", value).strip().lower()
    return re.sub(r"[^a-z0-9]+", "", base)


def extract_birth_date(html: str | None, summary: str | None) -> str | None:
    if html:
        html_match = re.search(r'class="bday">([^<]+)<', html)
        if html_match:
            return html_match.group(1).strip()

    if summary:
        summary_match = re.search(
            r"\(born\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4}|\d{4})",
            summary,
        )
        if summary_match:
            return summary_match.group(1).strip()

    return None


def pick_photo_url(images: list[str], page_title: str | None = None) -> str | None:
    normalized_title = ""
    if page_title:
        normalized_title = re.sub(r"[^a-z0-9]+", "", page_title.lower())

    preferred: list[str] = []
    fallback: list[str] = []
    for image_url in images:
        lowered = image_url.lower()
        if not lowered.endswith((".jpg", ".jpeg", ".png")):
            continue
        if any(token in lowered for token in ("icon", "logo", "question_book", "wiktionary", "svg")):
            continue
        normalized_url = re.sub(r"[^a-z0-9]+", "", lowered)
        if normalized_title and normalized_title in normalized_url:
            preferred.append(image_url)
        else:
            fallback.append(image_url)

    if preferred:
        return preferred[0]
    if fallback:
        return fallback[0]
    return None


def extract_primary_photo(html: str | None, images: list[str], page_title: str | None) -> tuple[str | None, str | None]:
    if html:
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table", class_=lambda value: value and "infobox" in value)
        if infobox is not None:
            image_tag = infobox.find("img")
            caption_node = infobox.find(class_=lambda value: value and ("infobox-caption" in value or "thumbcaption" in value))
            caption = clean_caption(caption_node.get_text(" ", strip=True)) if caption_node else None
            if image_tag and image_tag.get("src"):
                src = image_tag["src"]
                if src.startswith("//"):
                    return f"https:{src}", caption
                if src.startswith("/"):
                    return f"https://en.wikipedia.org{src}", caption
                return src, caption

    return pick_photo_url(images, page_title), None


def clean_caption(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\[[^\]]+\]", "", value).strip()
    return cleaned or None
