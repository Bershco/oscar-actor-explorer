from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from app.db import DEFAULT_DB_PATH, SessionLocal, configure_session
from app.findings import best_findings
from app.services import choose_fun_fact, get_person_profile, suggest_people
from app.wiki import fetch_wikipedia_profile


configure_session(DEFAULT_DB_PATH)


def title_case_text(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return stripped
    if stripped.isupper() or stripped.islower():
        return " ".join(word.capitalize() for word in stripped.split())
    return stripped


def format_percentage(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def format_years(year_labels: list[str]) -> str:
    if not year_labels:
        return "None"
    if len(year_labels) == 1:
        return year_labels[0]
    return f"{year_labels[0]} to {year_labels[-1]} ({len(year_labels)} ceremonies)"


def ensure_state() -> None:
    st.session_state.setdefault("search_input", "")
    st.session_state.setdefault("selected_person_id", None)
    st.session_state.setdefault("selected_tab", "Profile")
    st.session_state.setdefault("fun_fact", None)
    st.session_state.setdefault("fun_fact_person_id", None)
    st.session_state.setdefault("status_message", "")


@st.cache_data(show_spinner=False)
def cached_search_people(query: str) -> list[dict[str, int | str]]:
    with SessionLocal() as session:
        matches = suggest_people(session, query, limit=8)
    return [{"id": person.id, "name": person.name} for person in matches]


@st.cache_data(show_spinner=False)
def cached_dataset_profile(person_id: int):
    with SessionLocal() as session:
        return get_person_profile(session, person_id, include_wikipedia=False)


@st.cache_data(show_spinner=False)
def cached_wikipedia_profile(name: str):
    return fetch_wikipedia_profile(name)


@st.cache_data(show_spinner=False)
def cached_findings():
    with SessionLocal() as session:
        return best_findings(session)


def refresh_fun_fact(profile) -> None:
    with SessionLocal() as session:
        st.session_state["fun_fact"] = choose_fun_fact(
            session=session,
            nominations_count=profile.nominations_count,
            wins_count=profile.wins_count,
            categories=profile.categories,
            years_to_first_win=profile.years_to_first_win,
            nominated_films=profile.nominated_films,
            winning_films=profile.winning_films,
            year_labels=profile.year_labels,
            category_comparisons=profile.category_comparisons,
        )
    st.session_state["fun_fact_person_id"] = profile.person_id


def current_results() -> list[dict[str, int | str]]:
    query = st.session_state["search_input"].strip()
    if not query:
        return []
    return cached_search_people(query)


def first_autocomplete(results: list[dict[str, int | str]], query: str) -> str | None:
    query_lower = query.lower()
    for result in results:
        name = title_case_text(str(result["name"]))
        if name.lower().startswith(query_lower) and name.lower() != query_lower:
            return name
    return None


def match_label(result: dict[str, int | str]) -> str:
    return f"{title_case_text(str(result['name']))} [dataset id {result['id']}]"


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
          background:
            radial-gradient(circle at top left, #fff4d6 0, transparent 22rem),
            linear-gradient(180deg, #f7f2ea 0%, #f3eee4 100%);
        }
        .block-container {
          max-width: 96vw;
          padding-top: 0.75rem;
          padding-bottom: 1.5rem;
          padding-left: 1.25rem;
          padding-right: 1.25rem;
        }
        .title-box {
          display: inline-block;
          background: linear-gradient(135deg, #1f3a5f, #304f7d);
          color: #faf5ed;
          border-radius: 14px;
          padding: 8px 12px;
          box-shadow: 0 10px 20px rgba(31, 58, 95, 0.18);
          margin-bottom: 8px;
        }
        .title-box h1 {
          margin: 0;
          font-size: 1.05rem;
          line-height: 1.15;
        }
        .status-line {
          color: #72685c;
          font-size: 0.95rem;
          margin: 4px 2px 10px;
        }
        .stat-card,
        .panel-card {
          background: #fffaf1;
          border: 1px solid #d7c7ad;
          border-radius: 18px;
          box-shadow: 0 8px 22px rgba(61, 42, 18, 0.08);
        }
        .stat-card {
          background: #efe0c1;
          padding: 14px 16px;
          position: relative;
          overflow: hidden;
          min-height: 100px;
          margin-bottom: 10px;
        }
        .stat-card::before {
          content: "";
          position: absolute;
          inset: 0 auto 0 0;
          width: 6px;
          background: linear-gradient(180deg, #c79845, #8b5e34);
        }
        .stat-value {
          font-size: 1.65rem;
          font-weight: 700;
          color: #1f3a5f;
          margin-bottom: 6px;
        }
        .stat-label {
          color: #4d463d;
          font-size: 0.92rem;
        }
        .panel-card {
          padding: 16px;
          margin-bottom: 12px;
        }
        .panel-card h3 {
          margin: 0 0 10px;
          font-size: 0.98rem;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          color: #8b5e34;
        }
        .panel-card p,
        .panel-card li {
          line-height: 1.55;
          color: #1f2430;
        }
        .profile-name {
          color: #1f3a5f;
          font-size: 1.45rem;
          font-weight: 700;
          margin: 4px 2px 8px;
        }
        .autocomplete-note {
          color: #8d8377;
          font-size: 0.91rem;
          margin: -4px 2px 6px;
        }
        .film-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 8px;
        }
        .film-item {
          border: 1px solid #e2d6c1;
          border-radius: 12px;
          padding: 8px 10px;
          background: #fcf7ef;
          min-width: 0;
        }
        .film-title {
          color: #1f2430;
          font-weight: 600;
          font-size: 0.93rem;
          line-height: 1.25;
          word-break: break-word;
        }
        .film-badge {
          display: inline-block;
          margin-top: 6px;
          font-size: 0.78rem;
          padding: 2px 7px;
          border-radius: 999px;
        }
        .film-badge.win {
          background: #e5f2dd;
          color: #285b2a;
          border: 1px solid #b8d0ae;
        }
        .film-badge.nominee {
          background: #f7ead3;
          color: #875a18;
          border: 1px solid #e2c799;
        }
        .wiki-photo {
          margin-bottom: 12px;
        }
        .funfact-wrap {
          margin-top: 8px;
        }
        div[data-baseweb="select"] > div {
          border-radius: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="title-box"><h1>Oscar Actor Explorer</h1></div>
        """,
        unsafe_allow_html=True,
    )


def use_suggestion(completion: str) -> None:
    st.session_state["search_input"] = completion
    st.session_state["selected_person_id"] = None
    st.session_state["fun_fact"] = None
    st.session_state["fun_fact_person_id"] = None


def clear_search() -> None:
    st.session_state["search_input"] = ""
    st.session_state["selected_person_id"] = None
    st.session_state["fun_fact"] = None
    st.session_state["fun_fact_person_id"] = None
    st.session_state["status_message"] = ""


def render_search(results: list[dict[str, int | str]]) -> None:
    search_col, clear_col = st.columns([9, 1], vertical_alignment="bottom")
    with search_col:
        st.text_input(
            "Actor or director name",
            key="search_input",
            placeholder="Try Meryl Streep, Walt Disney, or Martin Scorsese",
            label_visibility="collapsed",
        )
    with clear_col:
        st.button("Clear", width="stretch", on_click=clear_search)

    query = st.session_state["search_input"].strip()
    if not query:
        st.session_state["status_message"] = ""
        return

    completion = first_autocomplete(results, query)
    if completion is not None:
        note_col, button_col = st.columns([8, 1.5], vertical_alignment="center")
        with note_col:
            st.markdown(
                f'<div class="autocomplete-note">Autocomplete suggestion: {html.escape(completion)}</div>',
                unsafe_allow_html=True,
            )
        with button_col:
            st.button("Use suggestion", width="stretch", on_click=use_suggestion, args=(completion,))

    if not results:
        st.session_state["status_message"] = f"No dataset match found for '{query}'."
    else:
        st.session_state["status_message"] = ""


def render_status() -> None:
    message = st.session_state["status_message"]
    if message:
        st.markdown(f'<div class="status-line">{html.escape(message)}</div>', unsafe_allow_html=True)


def selected_result(results: list[dict[str, int | str]]) -> dict[str, int | str] | None:
    if not results:
        st.session_state["selected_person_id"] = None
        return None

    ids = [int(item["id"]) for item in results]
    current_id = st.session_state.get("selected_person_id")
    if current_id not in ids:
        current_id = ids[0]
        st.session_state["selected_person_id"] = current_id

    labels = [match_label(item) for item in results]
    selected_index = ids.index(current_id)
    selected_label = st.selectbox("Possible matches", labels, index=selected_index)
    chosen = next(item for item in results if match_label(item) == selected_label)
    st.session_state["selected_person_id"] = int(chosen["id"])
    return chosen


def render_stat_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="stat-card">
          <div class="stat-value">{html.escape(value)}</div>
          <div class="stat-label">{html.escape(label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_card(title: str, body_html: str) -> None:
    st.markdown(
        f"""
        <div class="panel-card">
          <h3>{html.escape(title)}</h3>
          {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_films(profile) -> None:
    nominated = set(profile.nominated_films)
    winning = set(profile.winning_films)
    ordered = sorted(nominated | winning)
    if not ordered:
        render_panel_card("Films", "<p>No film data available.</p>")
        return

    blocks = ['<div class="panel-card"><h3>Films</h3><div class="film-grid">']
    for title in ordered:
        badge_class = "win" if title in winning else "nominee"
        badge_label = "Win" if title in winning else "Nomination"
        blocks.append(
            f'<div class="film-item"><div class="film-title">{html.escape(title)}</div><span class="film-badge {badge_class}">{html.escape(badge_label)}</span></div>'
        )
    blocks.append("</div></div>")
    st.markdown("".join(blocks), unsafe_allow_html=True)


def render_category_table(profile) -> None:
    render_panel_card("Category Comparison", "")
    rows = [
        {
            "Category": title_case_text(item.category_name),
            "Nominations": item.person_nominations,
            "Avg nominations": f"{item.average_nominations:.2f}",
            "Wins": item.person_wins,
            "Avg wins": f"{item.average_wins:.2f}",
        }
        for item in profile.category_comparisons
    ]
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.caption("No category comparison available.")


def render_profile_tab(profile, wikipedia) -> None:
    st.markdown(f'<div class="profile-name">{html.escape(title_case_text(profile.name))}</div>', unsafe_allow_html=True)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_stat_card("Nominations", str(profile.nominations_count))
    with metric_cols[1]:
        render_stat_card("Wins", str(profile.wins_count))
    with metric_cols[2]:
        render_stat_card("Win Rate", format_percentage(profile.win_rate))
    with metric_cols[3]:
        render_stat_card("Years To First Win", "No wins" if profile.years_to_first_win is None else str(profile.years_to_first_win))

    left, right = st.columns([1.8, 1], vertical_alignment="top")
    with left:
        render_panel_card(
            "Dataset Summary",
            "".join(
                [
                    f"<p><strong>Categories:</strong> {html.escape(', '.join(title_case_text(item) for item in profile.categories) or 'None')}</p>",
                    f"<p><strong>Years active at the Oscars:</strong> {html.escape(format_years(profile.year_labels))}</p>",
                ]
            ),
        )
        render_films(profile)
        render_category_table(profile)
    with right:
        if wikipedia is not None and wikipedia.status == "ok" and wikipedia.photo_url:
            st.image(
                wikipedia.photo_url,
                caption=wikipedia.photo_caption or wikipedia.title or profile.name,
                width="stretch",
            )
        elif wikipedia is None:
            st.caption("Loading photo...")


def render_wikipedia_tab(profile, wikipedia) -> None:
    left, right = st.columns([1.6, 1], vertical_alignment="top")
    with left:
        if wikipedia is None:
            render_panel_card("Wikipedia", "<p>Loading Wikipedia details...</p>")
        elif wikipedia.status == "ok":
            body = [
                f"<p><strong>Summary:</strong> {html.escape(wikipedia.summary or 'Not available')}</p>",
                f"<p><strong>Birth date:</strong> {html.escape(wikipedia.birth_date or 'Not available')}</p>",
                f"<p><strong>Page:</strong> {html.escape(wikipedia.page_url or 'Not available')}</p>",
            ]
            if wikipedia.note:
                body.append(f"<p><strong>Note:</strong> {html.escape(wikipedia.note)}</p>")
            if wikipedia.alternatives:
                body.append("<p><strong>Other possible matches:</strong></p><ul>")
                for option in wikipedia.alternatives:
                    label = title_case_text(option.title)
                    if option.url:
                        body.append(f'<li><a href="{html.escape(option.url)}" target="_blank">{html.escape(label)}</a></li>')
                    else:
                        body.append(f"<li>{html.escape(label)}</li>")
                body.append("</ul>")
            render_panel_card("Wikipedia", "".join(body))
        elif wikipedia.status == "ambiguous":
            options = ", ".join(title_case_text(option) for option in (wikipedia.options or []))
            render_panel_card(
                "Wikipedia",
                f"<p>{html.escape(wikipedia.message or 'Wikipedia returned an ambiguous result.')}</p><p><strong>Possible pages:</strong> {html.escape(options or 'None')}</p>",
            )
        else:
            render_panel_card("Wikipedia", f"<p>{html.escape(wikipedia.message or 'Wikipedia data not available.')}</p>")
    with right:
        if wikipedia is not None and wikipedia.status == "ok" and wikipedia.photo_url:
            st.image(
                wikipedia.photo_url,
                caption=wikipedia.photo_caption or wikipedia.title or profile.name,
                width="stretch",
            )


def render_findings_tab() -> None:
    for finding in cached_findings():
        render_panel_card(
            finding.title,
            "".join(
                [
                    f"<p><strong>Finding:</strong> {html.escape(finding.result)}</p>",
                    f"<p><strong>How it was found:</strong> {html.escape(finding.how_found)}</p>",
                    f"<p><strong>Why it is interesting:</strong> {html.escape(finding.why_interesting)}</p>",
                ]
            ),
        )


def render_fun_fact(profile, key_suffix: str) -> None:
    left, right = st.columns([1.8, 1], vertical_alignment="bottom")
    with left:
        render_panel_card(
            "Did You Know?",
            f"<p>{html.escape(st.session_state.get('fun_fact') or profile.fun_fact or 'Not available.')}</p>",
        )
    with right:
        if st.button("New fact", width="stretch", key=f"new_fact_{key_suffix}"):
            refresh_fun_fact(profile)
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Oscar Actor Explorer", page_icon="🏆", layout="wide")
    ensure_state()
    inject_css()
    render_header()

    results = current_results()
    render_search(results)
    render_status()

    if not st.session_state["search_input"].strip() or not results:
        return

    chosen = selected_result(results)
    if chosen is None:
        return

    with st.spinner("Loading profile..."):
        profile = cached_dataset_profile(int(chosen["id"]))
    if profile is None:
        st.error("Person not found.")
        return

    if st.session_state.get("fun_fact_person_id") != profile.person_id:
        st.session_state["fun_fact"] = profile.fun_fact
        st.session_state["fun_fact_person_id"] = profile.person_id

    tab_choice = st.radio(
        "View",
        ["Profile", "Wikipedia", "General Database Findings"],
        horizontal=True,
        label_visibility="collapsed",
        key="selected_tab",
    )

    content_placeholder = st.empty()
    fun_placeholder = st.empty()

    if tab_choice == "Profile":
        with content_placeholder.container():
            render_profile_tab(profile, None)
        with fun_placeholder.container():
            render_fun_fact(profile, "pending")
    elif tab_choice == "Wikipedia":
        with content_placeholder.container():
            render_wikipedia_tab(profile, None)
        with fun_placeholder.container():
            render_fun_fact(profile, "pending")
    else:
        with content_placeholder.container():
            render_findings_tab()

    if tab_choice != "General Database Findings":
        with st.spinner("Loading Wikipedia details..."):
            wikipedia = cached_wikipedia_profile(profile.name)
        if tab_choice == "Profile":
            with content_placeholder.container():
                render_profile_tab(profile, wikipedia)
            with fun_placeholder.container():
                render_fun_fact(profile, "loaded")
        elif tab_choice == "Wikipedia":
            with content_placeholder.container():
                render_wikipedia_tab(profile, wikipedia)
            with fun_placeholder.container():
                render_fun_fact(profile, "loaded")


if __name__ == "__main__":
    main()
