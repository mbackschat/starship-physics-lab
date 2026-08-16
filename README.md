# Starship Physics Lab

An interactive rocket physics explorer for beginners. Move any number in the model and watch the consequences propagate through a real physics engine.

Starship is the worked example that gives the app a spine, but the subject is the physics, not the polemic. A user who has never heard of the rocket equation should be able to work out for themselves why payload is so hard to come by.

## Status

Early build. See [docs/plan.md](docs/plan.md) for the milestone plan.

- [x] **M0** Scaffold
- [ ] **M1** Physics core
- [ ] **M2** Data library
- [ ] **M3** App shell, chapters 1 and 2
- [ ] **M4** Ascent simulation, chapter 3
- [ ] **M5** Staging and reuse, chapters 4 and 5
- [ ] **M6** The Starship case study, chapters 6, 7 and 7b
- [ ] **M7** Sandbox, chapter 8
- [ ] **M8** Polish

## Documentation

- [docs/physics-reference.md](docs/physics-reference.md) — the verified physics, the reference data, the model specifications and the golden numbers. Every claim the app makes traces back to a row in here.
- [docs/plan.md](docs/plan.md) — architecture, chapter design, milestones and the decisions taken.

## Layout

```
src/rocketry/   physics core, zero UI dependencies, fully unit-tested
app/            Streamlit front end
data/           rocket library as human-editable YAML
tests/          golden numbers and property tests
analysis/       standalone verification scripts, the audit trail for every number
```

The hard rule: `src/rocketry/` never imports Streamlit, Plotly or pandas.

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
