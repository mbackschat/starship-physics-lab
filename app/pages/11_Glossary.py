"""Chapter 11: what all these words mean."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import page, sidebar

from labbook.glossary import TERMS, define, search

page("11 · Glossary", "Every word this app uses without stopping to explain it.", icon="📖")
sidebar()

st.markdown(
    """
Written so each entry can be read cold. No definition assumes you have read
another one, and none of them defines a word using itself.
"""
)

query = st.text_input(
    "Search", placeholder="delta-v, staging, why is it in seconds...", label_visibility="collapsed"
)
matches = search(query) if query else list(TERMS)

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
        if term.related:
            links = " · ".join(
                related for related in term.related if define(related) is not None
            )
            st.markdown(f"**See also:** {links}")
