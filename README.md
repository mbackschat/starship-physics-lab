# Starship Physics Lab

An interactive rocket physics explorer for beginners. Move any number in the model and watch the consequences propagate through a real physics engine.

Starship is the worked example that gives the app a spine, but the subject is the physics, not the polemic. A user who has never heard of the rocket equation should be able to work out for themselves why payload is so hard to come by.

## Status

See [docs/plan.md](docs/plan.md) for the milestone plan.

- [x] **M0** Scaffold
- [x] **M1** Physics core (51 golden-number tests, 20 property tests)
- [x] **M2** Data library (7 engines, 18 stages, 10 vehicles, 3 flights)
- [x] **M2c** Analysis workbench (units, tables, charts, export)
- [ ] **M2b** More presets
- [ ] **M3** App shell, chapters 1 and 2
- [ ] **M4** Ascent simulation, chapter 3
- [ ] **M5** Staging and reuse, chapters 4 and 5
- [ ] **M6** The Starship case study, chapters 6, 7 and 7b
- [ ] **M7** Sandbox, chapter 8
- [ ] **M8** Polish

## Documentation

- [docs/physics-reference.md](docs/physics-reference.md) — the verified physics, the reference data, the model specifications and the golden numbers. Every claim the app makes traces back to a row in here.
- [docs/plan.md](docs/plan.md) — architecture, chapter design, milestones and the decisions taken.

## Two ways to use it

**As a web app**, for beginners who want to move sliders and watch what happens.

**As a workbench**, for anyone (including a coding agent) who wants to answer a specific question and get a table, a chart and a CSV back:

```python
from labbook import Col, Quantity, table
from labbook.units import US                 # or METRIC
from rocketry.library import load
from rocketry.vehicle import analyse

lib = load()
rows = [analyse(lib, k) for k in ("starship_v3", "falcon9_droneship")]
print(table(rows, [
    Col("name", "Vehicle"),
    Col("total_delta_v", "Ideal Δv", Quantity.VELOCITY),
    Col("payload_t", "Payload", Quantity.MASS, digits=1),
], formatter=US))
```

Both consumers share the same physics, the same rocket library, the same validated colour palette and the same unit system, so an answer produced in a script is the same answer the app shows.

## Layout

```
src/rocketry/   physics core. SI throughout. zero UI dependencies. fully tested
src/labbook/    presentation: units, palette, tables, charts, export
app/            Streamlit front end
data/           rocket library as human-editable YAML, every entry sourced
analysis/       one script per question, committed and re-runnable
docs/findings/  the writeup for each investigation
tests/          golden numbers and property tests
```

Two hard rules:

- `src/rocketry/` never imports Streamlit, Plotly, pandas or `labbook`.
- `src/rocketry/` is SI throughout. Unit conversion happens once, at the edge, in `labbook.units`. A unit bug can change a label but never a result.

## Development

```sh
uv sync                                  # install
uv run pytest                            # tests
uv run ruff check . && uv run mypy       # lint and types
uv run streamlit run app/Home.py         # the app (from M3 onwards)
python3 analysis/verify_article.py       # reproduce the source article's numbers
```

## Provenance

The physics analysis started from ["SpaceX: Wie das Starship den Kampf gegen die Physik verliert"](https://www.golem.de/news/spacex-wie-das-starship-den-kampf-gegen-die-physik-verliert-2608-211916.html), Golem.de, 14 August 2026. Every number in that article was independently recomputed before being used here; the verification log, including the three errors found, is in [docs/physics-reference.md](docs/physics-reference.md) section 3.
