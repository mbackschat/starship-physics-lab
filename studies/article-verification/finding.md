# Do the source article's numbers hold up?

**Question.** The project started from a German article arguing that Starship carries far less payload than SpaceX claims. Before building anything on it, does its arithmetic survive independent recomputation?

**Answer. Almost entirely. 61 of 64 checkable numbers reproduce within 2 %.** Three are wrong, none of which changes its conclusions.

| Correction | Article says | Correct value |
|---|---|---|
| C1 | Binary velocity constant 6.937, giving 2428 m/s | `g0 · ln2` = 6.798, giving 2380 m/s |
| C3 | Starship landing burn costs "about 30 t" | 22 to 25 t at any plausible Isp; 30 t is a padded reserve, not a calculation |
| C4 | Falcon 9 reaches 0.875 g at T+40 s against Starship's 0.69 g | 0.766 g against 0.704 g. The mechanism is real, the effect is a third the claimed size |

The model is also well calibrated, which matters more than any single number: its Starship stack totals 9404 m/s and its Falcon 9 cross-check 9258 m/s, both squarely inside the normal 9300 to 9600 m/s band for low Earth orbit.

**What does not hold up is an input, not the maths.** Starship's dry mass has been unpublished since 2019 and it decides everything. The rocket equation fixes 300 t arriving in orbit regardless of what that mass consists of; whether 40 t or 100 t of it is cargo depends only on how heavy the ship itself is.

**Reproduce.** `uv run python studies/article-verification/run.py`

**Full log.** [docs/physics-reference.md section 3](../../docs/physics-reference.md#3-verification-log) has the claim-by-claim table, [section 4](../../docs/physics-reference.md#4-corrections-and-caveats) the corrections in detail.
