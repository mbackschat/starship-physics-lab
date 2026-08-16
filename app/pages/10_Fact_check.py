"""Chapter 10: was the article right?"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import (
    chapter_footer,
    chapter_link,
    page,
    sidebar,
    why,
)

from labbook.factcheck import Verdict, check_all
from labbook.tables import Col, table

page("10 · Fact check", "Every number in the source article, recomputed here and now.")
formatter = sidebar()

st.markdown(
    """
This whole project started from one article. Before building anything on it,
every checkable number in it was recomputed independently.

Nothing below is a stored answer. Each row is calculated when this page loads,
by the same physics engine that runs every other chapter. If the library changed,
these numbers would change with it.
"""
)

results = check_all()
confirmed = [item for item in results if item.verdict is Verdict.CONFIRMED]
wrong = [item for item in results if item.verdict is Verdict.WRONG]

one, two, three = st.columns(3)
one.metric("Numbers checked here", len(results))
two.metric("Reproduce", len(confirmed))
three.metric("Do not", len(wrong))

st.success(
    f"**{len(confirmed)} of {len(results)} reproduce.** Across the full written "
    "verification, 61 of 64 checkable numbers hold within 2 %. The physics in "
    "the article is sound and its arithmetic is very nearly clean.",
    icon="✅",
)

st.markdown(
    table(
        [
            {
                "topic": item.claim.topic,
                "statement": item.claim.statement,
                "article": item.claim.article_value,
                "computed": item.computed,
                "error": item.relative_error,
                "verdict": item.verdict.label,
            }
            for item in results
        ],
        [
            Col("topic", "Number"),
            Col("article", "Article says", digits=3),
            Col("computed", "Recomputed", digits=3),
            Col("error", "Difference", digits=1),
            Col("verdict", "Verdict"),
        ],
        formatter=formatter,
    )
)

st.divider()
st.subheader("Where it goes wrong")

for item in wrong:
    with st.container(border=True):
        st.markdown(f"**{item.claim.topic}** · {item.claim.statement}")
        left, right = st.columns(2)
        left.metric("The article", f"{item.claim.article_value:,.3f} {item.claim.unit}")
        right.metric("Recomputed", f"{item.computed:,.3f} {item.claim.unit}")
        st.markdown(item.claim.note)
        st.caption(f"Verified in docs/physics-reference.md section {item.claim.section}")

st.info(
    "A third error is not shown above because it cannot be reduced to a single "
    "number: the article budgets Starship about 30 t of landing propellant where "
    "the calculation gives 22 to 25 t. It is a padded reserve rather than a "
    "computed figure, which is defensible, but it is not what the surrounding "
    "text implies.",
    icon="ℹ️",
)

st.divider()

why(
    "If the arithmetic is right, why is there an argument at all?",
    """
Because the argument is not about arithmetic.

Every number checked on this page is a calculation anyone can repeat. The
disagreement is about a single **input**: how much Starship weighs empty. SpaceX
has not published it since 2019, and the credible estimates span more than a
factor of two.

Feed the same equations a different weight and you get a different answer, with
no error anywhere. That is why the payload chapter gives you the slider instead
of a verdict.
""",
)

chapter_link(7)

why(
    "What would change these conclusions?",
    """
A measurement. Flight 14 is the first orbital attempt and will deploy real
satellites to a real orbit, which is a direct reading of the number this whole
argument turns on.

The library is built so that arrives as a data change rather than a code change:
one row in `data/flights.yaml`, and every chart that plots predictions against
observations updates itself.
""",
)

st.caption(
    "The complete log, including the numbers not reduced to formulas here, is in "
    "docs/physics-reference.md section 3, with the corrections in section 4 and "
    "the sources in section 10."
)

chapter_footer(10)
