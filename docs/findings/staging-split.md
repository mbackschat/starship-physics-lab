# Where should a two-stage rocket separate?

**Question.** The source article claims Starship stages far too early, and that a smaller upper stage on the same rocket would carry more payload. Is that right, and what does the current split cost?

**Answer. Yes, and it costs roughly a factor of 2.2 in payload.** Holding the liftoff mass at 5850 t, the mission budget at 9404 m/s and the booster's recovery profile fixed, and changing only the speed at which the stages separate:

| Staging speed | Payload |
|---|---|
| 6 000 km/h (as flown) | 57 t |
| 8 000 km/h (Falcon 9's split) | 97 t |
| 10 000 km/h (article's Raptor 33 + 4) | 121 t |
| **11 480 km/h (optimum)** | **126 t** |
| 12 000 km/h (article's Raptor 33 + 3) | 125 t |
| 16 000 km/h | 64 t |

![Payload against staging speed](../../analysis/out/staging-split.png)

The curve is flat near its peak, which supports the article's own remark that the split does not need to be perfect, only better. Anywhere between 9 500 and 13 500 km/h delivers more than twice what 6 000 km/h does.

**A second, independent signal.** Running each vehicle through the library at its operator's *claimed* payload gives its implied ideal Δv:

| Vehicle | Claimed payload | Implied ideal Δv |
|---|---|---|
| Falcon 9 (droneship) | 17.5 t | 9 333 m/s |
| Space Shuttle | 27.5 t | 9 445 m/s |
| Starship V3 | 100 t | **8 545 m/s** |
| Starship V4 (announced) | 200 t | **7 880 m/s** |

Falcon 9 and the Shuttle land in the normal 9 300 to 9 600 m/s band for LEO, which is what makes the method trustworthy. Starship at its claimed 100 t comes out roughly 850 m/s short of orbit, and V4 at its claimed 200 t is 1 500 m/s short. Either those payload claims are wrong, or the ships are far lighter than any public estimate suggests. This is the article's argument, reached without using any of its reasoning.

**Assumptions, all of them arguable.**

- Mission budget fixed at 9404 m/s regardless of staging speed. Staging later slightly reduces the upper stage's gravity losses, so this mildly understates the benefit of a later split.
- Upper stage inert mass scales linearly with its propellant, 250 t per 1600 t. Real scaling is sublinear, which understates the benefit further.
- Booster dry mass held at 300 t across the whole sweep, and it brakes to 5300 km/h before reentry and lands on 500 m/s.
- Payloads in the second table are the operators' claims, not computed values. The point of the table is to test those claims, not to use them.

**Reproduce.** `uv run python analysis/staging_split.py`

**Related.** [physics-reference.md section 3.7](../physics-reference.md#37-independent-check-of-the-central-thesis) for the verification, [section 2.6](../physics-reference.md#26-staging-why-and-how-to-split-it) for the theory, [correction C15](../physics-reference.md#c15-the-one-input-that-decides-everything) for why the dry mass is the load-bearing input.
