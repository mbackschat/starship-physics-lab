"""Chapter 11: what all these words mean."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import chapter_footer, page, sidebar

from labbook.glossary import TERMS, define, search

# Where the search box keeps its text. A "see also" button writes here and
# reruns, which is how one entry sends the reader to another without leaving the
# page. A comment rather than an attribute docstring on purpose: Streamlit's
# magic renders a bare string expression as page content, so the convention the
# rest of the project uses would print this paragraph to the reader.
QUERY_KEY = "glossary_query"

page("11 · Glossary", "Every word this app uses without stopping to explain it.", icon="📖")
sidebar()

st.markdown(
    """
Written so each entry can be read cold. No definition assumes you have read
another one, and none of them defines a word using itself.
"""
)

query = st.text_input(
    "Search",
    placeholder="delta-v, staging, why is it in seconds...",
    label_visibility="collapsed",
    key=QUERY_KEY,
)
matches = search(query) if query else list(TERMS)

if query:
    found, clear = st.columns([4, 1], vertical_alignment="center")
    found.caption(f"{len(matches)} of {len(TERMS)} terms match **{query}**.")
    clear.button(
        "Show all",
        width="stretch",
        on_click=lambda: st.session_state.update({QUERY_KEY: ""}),
    )

if not matches:
    st.info(
        f"Nothing here matches **{query}**. The glossary covers "
        f"{len(TERMS)} terms; try a shorter word.",
        icon="🔍",
    )

for term in matches:
    with st.container(border=True):
        st.markdown(f"### {term.word}")
        st.markdown(term.plain)
        if term.detail:
            st.caption(term.detail)

        # "See also" used to be plain text, which left the reader to scroll for
        # the entry it named. These jump to it.
        #
        # Buttons rather than links because the destination is on this same
        # page: a link would reload the whole browser runtime to arrive back
        # where it started. Tertiary and packed onto one line so they read as
        # the cross-references they are, rather than as a row of full-width
        # buttons competing with the definition above them.
        related = [name for name in term.related if define(name) is not None]
        if related:
            with st.container(
                horizontal=True,
                horizontal_alignment="left",
                vertical_alignment="center",
                gap="small",
            ):
                # Content width, or the caption stretches and shoves the links
                # to the far edge of the card, away from the words they follow.
                st.caption("See also", width="content")
                for name in related:
                    st.button(
                        name,
                        key=f"see-{term.word}-{name}",
                        type="tertiary",
                        help=f"Jump to {name}",
                        on_click=lambda chosen=name: st.session_state.update(
                            {QUERY_KEY: chosen}
                        ),
                    )

chapter_footer(11)
