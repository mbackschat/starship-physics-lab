# Does making Starship's ship bigger in V4 help?

**Question.** SpaceX plans to grow the ship to 2300 t of propellant on a 4050 t booster in V4. The article says in passing that this "will make Starship's problems worse". Is it right, and by how much?

**Answer. Right on direction. The magnitude turns entirely on one assumption.** Stretching the ship moves the stage propellant ratio the wrong way:

| Vehicle | Stage 1 : stage 2 propellant |
|---|---|
| Falcon 9 Block 5 | 3.70 : 1 |
| Starship V3 | 2.28 : 1 |
| Starship V4 (announced) | **1.76 : 1** |

Run through the same model, with ship dry mass scaling as `220 t · (prop/1600)^k`:

| Scaling exponent `k` | Ship dry mass | V4 payload |
|---|---|---|
| 1.0 (linear, the article's assumption) | 316 t | **12 t** |
| 0.8 (a realistic guess) | 294 t | 34 t |
| 0.0 (mass does not grow at all) | 220 t | **108 t** |

The mass arriving in orbit is 386 t in every row. Only its composition changes.

So a 21 % heavier rocket delivers between a third and three times today's payload, depending on a number nobody outside SpaceX knows. The article's direction is solid; its implied magnitude rests on the same contested input as everything else.

Two things push back the other way and are worth naming: real dry mass scales sublinearly, because a nose, fins, heat shield and engines do not grow with tank length; and V4's six vacuum Raptors instead of three should lift the flight-average Isp, worth roughly 23 t on its own.

**Reproduce.** `uv run python studies/v4-scaling/run.py`

**Related.** [docs/physics-reference.md section 3.8](../../docs/physics-reference.md#38-the-v4-stretch-the-articles-sharpest-prediction).
