# Rocket Physics Reference

Verified physics, data and models behind the German article ["SpaceX: Wie das Starship den Kampf gegen die Physik verliert"](https://www.golem.de/news/spacex-wie-das-starship-den-kampf-gegen-die-physik-verliert-2608-211916.html), published by Golem.de on **14 August 2026** (local copy: `~/Downloads/starship-article.md`).

**This document was verified on 16 August 2026, two days after publication.** The article is current, but the situation is moving fast: Flight 14 is expected before the end of August 2026 and will be the first orbital attempt and the first ship tower-catch attempt. See [Live context](#9-live-context-as-of-16-august-2026), which is the section to re-check before every work session.

This is not a translation. It is a rewrite in my own words, with every number recomputed independently, every factual claim checked against sources, and every model written down in the form the visualisation app needs. The companion build plan is [plan.md](plan.md).

**Status of the article after verification: the physics is sound and the arithmetic is almost entirely correct.** I reproduced 61 of 64 checkable numbers to within 2 %. Three numbers are wrong or misleading (see [Corrections](#4-corrections-and-caveats)), none of which changes the article's conclusions. The real uncertainty is not in the maths, it is in one input: Starship's dry mass, which SpaceX has not published since 2019.

---

## 1. How to read this document

| Section | What it gives the app |
|---|---|
| [2. The physics](#2-the-physics-from-first-principles) | Every formula the simulator implements, with the intuition a beginner needs |
| [3. Verification log](#3-verification-log) | Which article claims hold, so the app can quote them safely |
| [4. Corrections](#4-corrections-and-caveats) | Where the app must deviate from the article |
| [5. Reference data](#5-reference-data) | Seed dataset for the rocket library |
| [6. Models to implement](#6-models-the-app-must-implement) | Precise algorithm specs |
| [7. Golden numbers](#7-golden-numbers-test-fixtures) | Ready-made pytest fixtures for red/green TDD |
| [8. Teaching insights](#8-teaching-insights-worth-building-an-interaction-around) | The handful of ideas the whole app exists to convey |
| [9. Live context](#9-live-context-as-of-16-august-2026) | What is about to change, and what the app must be built to absorb |

Units throughout: mass in tonnes (t), velocity in m/s, thrust in tonnes-force (tf) or kN, specific impulse in seconds. Standard gravity `g0 = 9.80665 m/s²`. The article uses `9.81`; the difference is 0.03 % and irrelevant, but the app should use one constant consistently and state which.

---

## 2. The physics, from first principles

### 2.1 Thrust, exhaust velocity and specific impulse

A rocket engine throws mass backwards. Newton's third law does the rest. Thrust is the momentum thrown per second:

```
F = ṁ · v_e
```

where `ṁ` is propellant mass flow (kg/s) and `v_e` is effective exhaust velocity (m/s).

Rocketry quotes efficiency as **specific impulse** instead, in seconds:

```
Isp = F / (ṁ · g0)          v_e = Isp · g0
```

The seconds have a physical meaning worth showing a beginner: *an engine with Isp = 350 s could produce 1 tonne of thrust for 350 seconds while burning 1 tonne of propellant.* Higher Isp means less propellant burnt for the same push.

The article's worked example checks out: a Raptor 3 at 250 tf and Isp 327 s consumes `250 / 327 = 0.765 t/s`.

**Pressure dependence.** Isp is lower at sea level because ambient air pressure pushes back on the nozzle exit:

```
F(h) = F_vac − A_e · p_ambient(h)
```

This is why the same engine is quoted twice (Raptor 3: 330 s at sea level, 350 s in vacuum, 380 s with the big vacuum nozzle). It is also why an ascent simulator must vary thrust with altitude.

### 2.2 The rocket equation (Tsiolkovsky, 1903)

```
Δv = v_e · ln(m_0 / m_f) = Isp · g0 · ln(m_0 / m_f)
```

`m_0` = mass before the burn, `m_f` = mass after. The ratio `m_0/m_f` is the **mass ratio**.

Rearranged into the three forms the app needs:

```
mass ratio needed:        MR   = exp(Δv / v_e)
propellant, from m_f:     m_p  = m_f · (exp(Δv / v_e) − 1)
propellant, from m_0:     m_p  = m_0 · (1 − exp(−Δv / v_e))
final mass, from m_0:     m_f  = m_0 · exp(−Δv / v_e)
```

**Beginners get burnt by the two propellant forms.** Both are correct; they answer different questions. "What fraction of what I have now do I burn?" gives 3.96 % for a 139 m/s burn at `v_e = 3433`. "What fraction of what remains at the end do I burn?" gives 4.13 %. The article rounds both to "4 %" but its mass estimates only work with the second reading. The app should label this explicitly.

### 2.3 Why the logarithm is the whole problem

The velocity gained is logarithmic in mass ratio, so propellant is *exponential* in velocity. The article's ladder is the cleanest way to show this. Take a 1 t empty rocket and let `V` be the speed it reaches with a mass ratio of 2:

| Target speed | Mass ratio | Propellant | Added over previous |
|---|---|---|---|
| 1 × V | 2 | 1 t | 1 t |
| 2 × V | 4 | 3 t | 2 t |
| 3 × V | 8 | 7 t | 4 t |
| 4 × V | 16 | 15 t | 8 t |

Verified: mass ratio `2^n`, propellant `2^n − 1`. Each additional `V` costs double the previous step. Since tanks and engines scale roughly linearly with propellant, the structure grows too, and payload gets squeezed out from both sides.

For a Raptor in vacuum (Isp 350 s), `V = v_e · ln2 = 3433 · 0.693 = 2380 m/s`. The article prints 2428 m/s; see [C1](#c1-binary-velocity-constant).

### 2.4 The losses the rocket equation does not include

Tsiolkovsky assumes a burn in free space with no gravity, no atmosphere and no steering. A real launch loses:

```
Δv_required = Δv_orbit + Δv_gravity + Δv_drag + Δv_steering + Δv_pressure
```

- **Gravity loss** `= ∫ g · sin(γ) dt`, where `γ` is the flight path angle. Straight up, it is simply `g · t`. This is the big one: 1000 to 1500 m/s on a typical launch. A 20 s hover burn throws away `20 · 9.81 = 196 m/s` for nothing, which is exactly how the article budgets landing burns.
- **Drag loss** `= ∫ (D/m) dt` with `D = ½ ρ(h) v² C_d A`. Typically 100 to 300 m/s. Small, but it sets the max-Q throttle-down.
- **Steering loss**: thrust not aligned with velocity. Small if the gravity turn is flown well.
- **Pressure loss**: already folded in by using altitude-dependent Isp.

**The counterintuitive part, and the article is right about it.** Low thrust-to-weight at liftoff wastes thrust. If liftoff TWR is 1.41, then `1/1.41 = 71 %` of the thrust is spent merely holding the rocket up and only 29 % accelerates it. Both Falcon 9 and Starship lift off at TWR ≈ 1.41, i.e. 0.41 g of net acceleration.

The subtler effect the article identifies is real: a more efficient engine burns *less* propellant per second for the same thrust, so the vehicle sheds mass more slowly, so TWR climbs more slowly, so it spends longer deep in the gravity-loss regime. Falcon 9 burns 0.50 % of its liftoff mass per second, Starship only 0.43 %. Verified from published thrust and Isp. (The article overstates the size of the effect, see [C4](#c4-falcon-9-acceleration-at-t40-s).)

### 2.5 Δv budget to orbit

Circular orbital velocity: `v_orb = sqrt(μ / r)` with `μ = 3.986e14 m³/s²`, `r = R_earth + h`, `R_earth = 6371 km`. At 200 km: **7784 m/s**. At 400 km: 7669 m/s.

Total ideal Δv from the pad is typically **9300 to 9600 m/s** for LEO. The article's Starship model lands on 9404 m/s and its Falcon 9 cross-check on 9258 m/s. Both are squarely in the normal band, which is the strongest evidence that the whole model is calibrated correctly.

**Launch site and inclination.** Earth's surface moves east at `465.1 · cos(latitude)` m/s. A launch to inclination `i` from latitude `φ` flies at azimuth `A` with:

```
sin(A) = cos(i) / cos(φ)          (requires i ≥ φ)
rotation bonus = 465.1 · cos(φ) · sin(A)
```

From Starbase (25.997° N), verified:

| Target inclination | Azimuth term | Rotation bonus | Penalty vs due east |
|---|---|---|---|
| 26° (due east) | 1.000 | +418 m/s | 0 |
| 53° (Starlink) | 0.670 | +280 m/s | 138 m/s |
| 90° (polar) | 0.000 | 0 m/s | 418 m/s |
| 97.4° (sun-synchronous) | −0.147 | −62 m/s | 480 m/s |

The article quotes ~600 m/s for polar. Geometry alone gives 418 to 480 m/s; the remainder is dogleg and altitude. Falcon 9's own published payload drop (17.5 t → 13.5 t) implies about 700 m/s, so the article's 600 m/s is if anything conservative. Good enough to use.

### 2.6 Staging: why, and how to split it

A single stage carries its empty tanks all the way to orbit. Staging throws them away mid-flight, which resets the mass ratio.

**The optimal split.** For two stages with the *same* exhaust velocity and the *same* structural coefficient `ε = m_dry / (m_dry + m_prop)`, payload is maximised when both stages provide the **same Δv**. I verified this numerically (Δv 9404 m/s, ε = 0.08, Isp 350 s): the payload fraction peaks sharply at a 50/50 split (3.587 %) and falls to 1.87 % at a 20/80 or 80/20 split. A factor of two in payload for getting the split wrong.

When the stages differ, the optimum shifts: the stage with **higher Isp** should do **more** of the Δv, and the stage with the **worse structural fraction** should do **less**. Since first stages use lower-Isp sea-level engines, the first stage should do slightly *less* than half. The article states this correctly.

Reality check on real vehicles:

| Vehicle | Stage 1 share of ideal Δv |
|---|---|
| Falcon 9 (Starlink, droneship) | 35 % |
| Starship / Super Heavy | 30 % |
| Article's "Raptor 33/4" redesign | 41 % |
| Theoretical optimum (equal stages) | ~50 % |

So Falcon 9 is not optimal either. Starship is worse. The article's redesign is better but still short of the ideal, which the article itself admits.

### 2.7 What reuse costs

A recovered stage must keep propellant back. Budgets, verified against the article and Falcon 9 practice:

| Manoeuvre | Δv | Notes |
|---|---|---|
| Boostback (return to launch site) | 1500 to 1800 m/s | Must null all downrange velocity and reverse it |
| Entry burn (droneship profile) | 500 to 1300 m/s | Only to survive reentry heating, not to return |
| Landing burn | 500 to 600 m/s | Residual velocity plus `g · t_burn` gravity loss plus throttling inefficiency |

Super Heavy's return-to-launch-site profile is the expensive one. The article's budget: 1800 m/s boostback plus 600 m/s landing, which at ~330 s average Isp needs **1.10 t of propellant per tonne of dry mass**. I reproduce 1.04 t/t at Isp 350/327 and 1.10 t/t at Isp 330/330. For a 300 t booster that is 311 to 330 t of propellant carried uphill and back down.

Falcon 9 on a droneship keeps only ~25 t back on a 25.6 t stage, roughly 1.0 t/t, but it stages 550 m/s faster and does not fly back. That is the whole trade.

Measured cost of reuse on Falcon 9: payload 22.8 t expendable → 17.5 t with droneship recovery, a 23 % payload loss and a 20 % loss of total mass delivered to orbit. Both verified.

### 2.8 Reentry: the square-cube law

Deceleration in the atmosphere depends on the **ballistic coefficient** `β = m / (C_d · A)`. Mass scales with volume (length³), frontal area only with length². Scale a stage up and `β` grows linearly with size: it penetrates deeper into dense air before slowing, arriving faster, with less surface to dump the heat into.

Verified numbers: Super Heavy at 9 m diameter has `(9/3.66)² = 6.05×` the frontal area of Falcon 9 but `300/25.6 = 11.7×` the dry mass, so roughly double the ballistic coefficient. Matching Falcon 9's loading would need a 12.7 m diameter booster. The article's "12.5 m" is right, and its aside about flying saucers is the correct physical intuition: for reentry you want maximum area per unit mass.

---

## 3. Verification log

I recomputed every number in the article in Python. Full results below, condensed. "OK" means reproduced within 2 %.

### 3.1 Engines and the rocket equation

| Article claim | My result | Verdict |
|---|---|---|
| Raptor 3 flow = 250 tf / 327 s = 0.764 t/s | 0.7645 t/s | OK |
| 250 tf is 11 % throttled from 280 tf | 10.7 % | OK |
| Isp 350 s → 3433 m/s exhaust | 3434 m/s | OK |
| Binary velocity V = Isp × 6.937 = 2428 m/s | 6.80 → 2380 m/s | **Wrong, see C1** |
| Doubling ladder 1 / 3 / 7 / 15 t | 1 / 3 / 7 / 15 t | OK |

### 3.2 Weighing Starship from the 14 s relight

| Article claim | My result | Verdict |
|---|---|---|
| 14 s full-thrust burn = 10.7 t propellant | 10.70 t | OK |
| 500 km/h = 139 m/s | 138.9 m/s | OK |
| Costs "4 % of own weight" | 3.96 % of pre-burn mass, 4.13 % of post-burn mass | OK, ambiguous |
| 10 to 10.7 t burnt → vehicle 240 to 257 t | 242 to 259 t (post-burn) | OK |
| Landing burn: 20 s → 200 m/s gravity loss | 196 m/s | OK |
| Landing burn total 300 m/s | 300 m/s (196 + 100 residual) | OK |
| Landing burn costs "over 10 %", ~30 t | 21.6 t at Isp 327, 25.4 t at Isp 280 | **Padded, see C3** |

### 3.3 The plausible Starship model

Inputs: Starship 300 t in orbit including payload and landing propellant, 1600 t propellant, average Isp 365 s. Super Heavy 300 t dry, 3650 t propellant of which 3320 t burnt to staging, average Isp 340 s.

| Article claim | My result | Verdict |
|---|---|---|
| Stack liftoff mass 5850 t | 5850 t exactly | OK |
| Starship ideal Δv 6609 m/s | 6609.3 m/s | OK |
| Super Heavy ideal Δv 2795 m/s | 2796.1 m/s | OK |
| Total 9404 m/s | 9405 m/s | OK |
| Super Heavy provides 30 % of Δv | 29.7 % | OK |
| Boostback Δv (5400 + 1000 km/h) ≥ 1800 m/s | 1778 m/s | OK (rounded up) |
| Return needs ≥ 1.1 t propellant per t dry | 1.04 to 1.10 t/t depending on Isp | OK |
| 330 t held back (3650 − 3320) | 330 t | OK |
| Liftoff TWR 1.41, net 0.41 g, gravity eats 70 % | 1.410, 0.410 g, 70.9 % | OK |

### 3.4 Falcon 9 cross-check

| Article claim | My result | Verdict |
|---|---|---|
| Stage 2 Δv with 17.5 t payload = 6100 m/s | 6104 m/s | OK |
| Minus 0.5 t deorbit propellant = 6025 m/s | 6025 m/s | OK |
| Stage 1 Δv 3233 m/s | 3233 m/s at 25.6 t dry, 385 t propellant, Isp 301 s average | OK (reverse engineered) |
| Stage 1 has 438 m/s more Δv than Super Heavy | 437 m/s | OK |
| F9 burns 0.5 % of liftoff mass/s, Starship 0.43 % | 0.501 % and 0.431 % | OK |
| Raptor uses 14 % less propellant than Merlin | 13.8 % | OK |
| F9 at T+40 s reaches 0.875 g, Starship 0.69 g | 0.766 g and 0.704 g | **Wrong, see C4** |
| Gravity eats 53 % (F9) vs 59 % (Starship) | 56.6 % and 58.7 % | **Wrong, see C4** |
| Reuse costs 25 % of payload, 20 % of orbital mass | 23.2 % and 19.8 % | OK |

### 3.5 Mass fractions

| Article claim | My result | Verdict |
|---|---|---|
| Starship dry fraction 12 % | 12.1 % (220 / 1820) | OK |
| Falcon 9 stage 2 + fairing 6 % | 5.3 % | OK (rounded) |
| Ariane 6 upper stage scaled to Starship = 300 t dry | 300 t | OK |
| Ariane 6 lifts 3.67× its own dry mass | 3.67× | OK |
| Falcon 9 stage 1 scaled to 3650 t propellant = 240 t | 242.7 t | OK |
| Super Heavy: 6× the area, 12× the mass of F9 stage 1 | 6.05× and 11.7× | OK |
| Equal ballistic loading needs 12.5 m diameter | 12.68 m | OK |
| Shuttle had "almost double" Starship's payload | True only as payload *fraction*, 2.1× | **Ambiguous, see C14** |

### 3.6 The redesign thought experiments

Staging at 10 000 km/h ("Raptor 33" booster + "Raptor 4" ship), same 5850 t liftoff mass:

| Article claim | My result | Verdict |
|---|---|---|
| Booster Δv 3920 m/s | 3907 m/s | OK |
| Burns 69.1 % of liftoff mass | 69.0 % | OK |
| 1806 t left at staging | 1813 t | OK |
| Landing costs 17 % of dry mass | 16.9 % | OK |
| Braking 10 000 → 5300 km/h costs 46 % | 46.3 % | OK |
| Booster at separation = 171 % of dry = 513 t | 170.9 %, 512.8 t | OK |
| 1293 t left for upper stage + payload | 1300 t | OK |
| 271 t reaches orbit, 1022 t burnt | 272 t, 1028 t | OK |
| Upper stage 160 t instead of 250 t | 160.7 t by linear scaling | OK |
| Payload 110 t | 112 t | OK |
| 53° orbit: ~87 t payload | 88 t | OK |
| Polar orbit: ~68 t payload | 70 t | OK |
| Expendable 40 t upper stage: 230 t to LEO | 232 t | OK |
| Same, >50 t to Mars | 60 t at Isp 365, 64 t at Isp 380 | OK |

Staging at 12 000 km/h ("Raptor 3" ship):

| Article claim | My result | Verdict |
|---|---|---|
| Upper stage 942 t total | 932 t | OK |
| 231 t to orbit, 711 t propellant burnt | 230 t, 712 t | OK |
| Stage mass 111 t, payload 120 t | 111 t, 119 t | OK |
| Booster needs ~300 t for braking + landing | 303 t | OK |
| Full booster mass 4908 t | 4908 t | OK |
| Sensitivity: 400 t booster → 742 t upper stage, 94 t payload | 731 t, 93.6 t | OK |

### 3.7 Independent check of the central thesis

The article claims Starship stages far too early and that a smaller upper stage on the same 5850 t stack would carry more payload. I did not take its word for it. I built the model from scratch, swept staging velocity from 6000 to 16 000 km/h, held the total mission Δv fixed at 9404 m/s, scaled the upper stage's inert mass linearly with its propellant, and charged the booster for braking to 5300 km/h plus a 500 m/s landing:

| Staging speed | Booster Δv | Upper stage Δv | To orbit | Upper stage inert | **Payload** |
|---|---|---|---|---|---|
| 6000 km/h (as flown) | 2796 | 6608 | 341 t | 284 t | **57 t** |
| 8000 km/h | 3351 | 6053 | 315 t | 217 t | **97 t** |
| 10 000 km/h | 3907 | 5497 | 280 t | 159 t | **121 t** |
| 11 500 km/h | 4324 | 5080 | 247 t | 121 t | **126 t (peak)** |
| 12 000 km/h | 4462 | 4942 | 234 t | 109 t | **125 t** |
| 14 000 km/h | 5018 | 4386 | 174 t | 65 t | **108 t** |
| 16 000 km/h | 5574 | 3830 | 92 t | 27 t | **64 t** |

**The thesis is confirmed.** The optimum sits near 11 500 km/h and is worth roughly 2× the payload of the as-flown 6000 km/h split. The curve is also flat near the top, which supports the article's remark that the split need not be perfect, only better. My absolute numbers run higher than the article's because I scale the upper stage's inert mass strictly linearly, which is generous at the large end; the *shape* of the curve is the robust result.

### 3.8 The V4 stretch: the article's sharpest prediction

The article notes in passing that SpaceX intends to grow the ship again in the fourth generation, to 2300 t of propellant on a 4050 t booster, and says this "will make Starship's problems worse". Both figures are confirmed by SpaceX's published V4 plans. The propellant ratio between the stages moves the wrong way:

| Vehicle | Stage 1 propellant | Stage 2 propellant | Ratio |
|---|---|---|---|
| Falcon 9 Block 5 | 395.7 t | 107 t | **3.70 : 1** |
| Starship V3 (flying now) | 3650 t | 1600 t | **2.28 : 1** |
| Starship V4 (announced) | 4050 t | 2300 t | **1.76 : 1** |
| Article's "Raptor 33 / Raptor 4" | 4020 t | 1022 t | 3.93 : 1 |
| Article's "Raptor 33 / Raptor 3" | 4608 t | 711 t | 6.48 : 1 |

I ran V4 through the same model, scaling both stages' dry mass linearly with their propellant and holding the 9404 m/s mission budget and the 1.1 t/t recovery reserve fixed:

| Configuration | Liftoff mass | Booster share of Δv | Mass in orbit | **Payload** |
|---|---|---|---|---|
| V3 as flown | 5850 t | 30 % | 300 t | **40 t** |
| V4 as announced (2300 t ship) | 7069 t | 26 % | 386 t | **12 t** |
| V4 booster with today's 1600 t ship | 6297 t | 31 % | 314 t | **54 t** |
| V4 booster with a 1100 t ship | 5738 t | 36 % | 255 t | **77 t** |
| V4 booster with a 700 t ship (model optimum) | ~5300 t | 42 % | ~180 t | **84 t** |

**Under the article's own assumptions the V4 stretch is not merely suboptimal, it is strongly negative:** a 21 % heavier rocket delivering less than a third of the payload, because every tonne added to the ship is a tonne that must be carried to orbital velocity by the ship itself.

Two honest caveats, both of which the app must expose as parameters rather than bury:

1. **Dry-mass scaling is the load-bearing assumption.** A ship's nose, heat shield, fins and engines do not scale fully with tank length, so real scaling is sublinear, which softens the penalty. Conversely, longer tanks mean higher bending loads, which pushes the other way. Writing `dry = 220 t · (prop/1600)^k`:

| Scaling exponent `k` | Ship dry mass | **V4 payload** |
|---|---|---|
| 1.0 (fully linear, the article's assumption) | 316 t | **12 t** |
| 0.9 | 305 t | 23 t |
| 0.8 (a realistic guess) | 294 t | **34 t** |
| 0.7 | 284 t | 45 t |
| 0.5 | 264 t | 65 t |
| 0.0 (mass does not grow at all) | 220 t | **108 t** |

Note that the mass reaching orbit is 386 t in every row. Only its composition changes. This is [C15](#c15-the-one-input-that-decides-everything) again, in a second guise, and it is the reason the app needs `k` as a visible control rather than a hidden constant.

2. **V4's ship gets six vacuum Raptors instead of three**, which raises its flight-average Isp above the 365 s I assumed. At 375 s and fully linear scaling, the V4 payload rises from 12 t to 35 t. Real, and roughly as large as one full step of the scaling exponent, but nowhere near enough to rescue the configuration on its own.

So the article's *direction* is solidly right and the mechanism is correct. Its implied magnitude depends entirely on how well SpaceX scales ship dry mass, which is the same contested number that decides everything else. This makes an excellent app interaction: a "how does dry mass scale?" exponent slider from 0 (fixed mass) to 1 (fully linear), showing the V4 payload swing from 108 t to 12 t.

### 3.9 Facts checked against sources

| Article claim | Source check | Verdict |
|---|---|---|
| Flight 13 carried 20 satellites, previous flight 22 at 37.5 t | 20 Starlink V3 sats, ~34 100 kg total; 1.705 t each ⇒ 22 sats = 37.5 t | Confirmed |
| Flight 13 deliberately fell short of orbit | "a controlled suborbital trajectory designed to fall just short of orbit" | Confirmed |
| Super Heavy has never survived to a soft water landing in this generation | B20 landing burn relit only 10 of 13 engines, vehicle destroyed on impact | Confirmed |
| Super Heavy V3 holds 3650 t of propellant | Block 3: 3 650 000 kg | Confirmed |
| Starship V3 holds 1600 t | V3 ship propellant 1600 t (up from 1500 t) | Confirmed |
| Raptor 3: 250 tf at liftoff, announced 280 tf | SpaceX: 280 tf. Block 3 stack max thrust 80.8 MN / 33 = 249.7 tf | Confirmed |
| Payload claims went 150 t → 100 t, then restated as 15 t (V1) and 35 t (V2), 100 t (V3) | V1 15 t, V2 35 t (originally announced as 100 t), V3 100 t | Confirmed |
| Musk 2019: prototype was 200 t, not the 120 t on the slide | "Mk1 ship is around 200 tons dry & 1400 tons wet, but aiming for 120 by Mk4 or Mk5" | Confirmed verbatim |
| Long March 10 showed cable-based landing without legs | LM-10B first stage caught 10 July 2026 in a pretensioned cable net on the ship *Linghangzhe*, using four hooks, no landing legs | Confirmed, and it was at **sea**, which strengthens the article's argument |
| Shuttle: 2000 t liftoff, 27.5 t payload, 7 crew | 2030 t, 27 500 kg to 204 km, orbiter 78 t dry | Confirmed |
| Falcon 9 stage 2: 4 t dry, 107 t propellant, MVac 348 s / 100 tf, fairing ~2 t | 3.9 t dry, 981 kN, 348 s, fairing 1.9 t; propellant quoted 92.7 t to 111 t across sources, 107.5 t is the common Block 5 figure | Confirmed |
| Falcon 9 stage 1: 385 t propellant, 3.66 m diameter | 395.7 t (Block 5), 3.7 m | **Slightly low, see C6** |
| Ariane 6 upper stage: 6 t dry, 32 t propellant, 22 t to LEO | 31 t propellant (25 t LOX + 5 t LH2), Vinci 180 kN; 6 t dry is the commonly cited figure | Confirmed |
| Atlas 1957, balloon tanks, dropped 2 of 3 engines, Glenn to orbit without staging | SM-65 Atlas, 1.5-stage design, first flight 1957, Friendship 7 in 1962 | Confirmed |
| NASA failed at large composite tanks on X-33 | X-33 composite LH2 tank failed in test Nov 1999, programme cancelled 2001 | Confirmed |
| SpaceX bought two oil rigs named Phobos and Deimos | Purchased 2020, named after the Mars moons, later sold | Confirmed |
| Fifth steel tank prototype survived pressure testing | Mk1, SN1, SN3 failed, SN2 and SN4 passed; "the fifth" is approximately right but the year was 2020, not 2019 | Approximately right |
| V4 will carry 2300 t in the ship on only 4050 t in the booster | Confirmed: booster propellant rises 3650 → 4050 t, V4 ship 2300 t, 42 engines total (33 booster, 9 ship: 3 sea level + 6 vacuum), ~142 m stacked, 2027 debut, stretch goal 300 tf per engine | Confirmed |

---

## 4. Corrections and caveats

Ordered by how much they matter for the app.

### C15: the one input that decides everything

**Starship's dry mass is unpublished, and it is the entire argument.**

The rocket equation fixes the mass arriving in orbit almost independently of what that mass consists of. With 1600 t of propellant, Isp 365 s and 6609 m/s of Δv, the mass in orbit is `1600 / (e^(6609/3581) − 1) = 300 t`. Full stop. Everything else is bookkeeping inside that 300 t:

| Assumed ship dry mass | Residual propellant | Payload |
|---|---|---|
| 220 t (article's estimate) | 40 t | **40 t** |
| 190 t | 40 t | 70 t |
| 160 t (needed for SpaceX's claim) | 40 t | **100 t** |
| 120 t (2020 target) | 40 t | 140 t |
| 85 t (Wikipedia's V2 figure) | 40 t | 175 t |

The article's evidence for ~200 to 220 t is circumstantial but consistent: Musk's own 2019 statement of 200 t for a prototype without a heat shield; the hover-thrust bracket (two engines at minimum throttle vs one at full thrust puts the landing mass between roughly 200 and 250 t); and the 14 s relight, which measures a **total** mass of 242 to 259 t before reentry.

What the relight actually measures is total mass, not dry mass. Splitting it into dry mass plus residual propellant is an assumption. The app must therefore treat ship dry mass as a **slider, not a constant**, and show the payload consequence live. That single interaction is the most honest and most instructive thing the app can do.

### C4: Falcon 9 acceleration at T+40 s

The article states Falcon 9 reaches 0.875 g while Starship reaches only 0.69 g, and that gravity eats 53 % vs 59 % of thrust.

Using the article's own stated premise (both lift off at essentially the same TWR ≈ 1.41) and its own propellant-flow figures, the correct values are **0.766 g and 0.704 g**, with gravity taking **56.6 % and 58.7 %**. The article's Falcon 9 figure silently assumes a liftoff TWR of 1.51.

The mechanism the article describes is real and the sign is right. The magnitude is roughly three times too large. The app should show the correct 0.77 vs 0.70 and let the user vary liftoff TWR to see the effect properly.

### C3: Starship's landing propellant

The article budgets "over 10 % of remaining dry mass, so about 30 t" for a 300 m/s landing on a 220 t vehicle. Straight computation gives 21.6 t at Isp 327 s, 23.6 t at 300 s, 25.4 t at 280 s. Reaching 30 t needs Isp ≈ 240 s or Δv ≈ 400 m/s.

The 30 t is a padded allowance, not a calculation. It is defensible as a reserve but should be presented as such. The app should expose landing Δv and landing Isp as inputs.

### C1: binary velocity constant

The footnote defines a "binary" velocity V such that a mass ratio of 2 gives V, and states `V = Isp × 6.937 m/s²`, giving 2428 m/s for Isp 350 s.

The correct constant is `g0 · ln2 = 9.80665 × 0.6931 = 6.798 m/s²`, giving **2380 m/s**. A 2 % error. The idea itself is a genuinely good teaching device and worth keeping: *every doubling of the mass ratio buys one more V*. The app should use the correct constant.

### C14: the Space Shuttle comparison

"The Shuttle had almost double the payload of a Starship three times its launch mass" is only true as a payload *fraction*:

| | Liftoff mass | Payload | Payload fraction | Mass to orbit | Useful fraction of that |
|---|---|---|---|---|---|
| Space Shuttle | 2030 t | 27.5 t | 1.35 % | 105.5 t (orbiter + payload) | 26 % |
| Starship (article model) | 5850 t | 40 t | 0.68 % | 300 t | 13 % |
| Starship (Flight 13 actual) | 5850 t | 34.1 t | 0.58 % | ~300 t | 11 % |

In absolute tonnes, Flight 13's 34.1 t beat the Shuttle's 27.5 t. The fair statements are: the Shuttle delivered about **twice the payload per tonne of rocket**, and, strikingly, **both vehicles put almost exactly the same fraction of their liftoff mass into orbit (5.2 % vs 5.1 %)**. The difference is entirely in how much of that arriving mass is useful cargo rather than vehicle. This reframing is better than the article's and belongs in the app.

### C6: Falcon 9 first stage propellant

The article uses 385 t. Wikipedia's Block 5 entry gives 395.7 t; other published figures run to 411 t. Using a higher number makes the article's own point stronger: the Falcon 9 first-stage-to-second-stage propellant ratio becomes 3.7 to 3.8, versus Starship's 2.3.

### C8: staging altitude comparison

The article says Falcon 9 separates "50 km higher" than Super Heavy. I could not verify this. Published MECO altitudes for both vehicles cluster in the 60 to 80 km band. The **velocity** difference (about 550 m/s, or 2000 km/h) is well supported and is what the physics actually turns on. The app should compare staging velocities and not lean on altitude.

### C5: attributing the missing 2000 km/h

The article says Flight 13 would have needed 28 500 km/h instead of the 26 500 km/h achieved to reach a real 53° Starlink orbit. The 2000 km/h total is plausible, but it lumps three different things together. Broken out: about 140 m/s (500 km/h) to close the deliberate suborbital shortfall, about 140 m/s for the inclination change, and the remaining ~275 m/s for the higher and properly circularised orbit. Only a quarter of the gap is the inclination penalty. The app should break the budget into named line items rather than quoting one number.

### Minor items, no action needed

- **C2**: "4 % of its own weight" is 3.96 % of pre-burn mass or 4.13 % of post-burn mass. The article's masses use the second. Worth labelling in the UI.
- **C7**: Falcon 9 stage 2 + fairing dry fraction is 5.3 %, printed as 6 %.
- **C9**: the Super Heavy landing budget of 600 m/s computes to 565 m/s; rounded up to cover throttling losses, stated as such.
- **C10**: boostback Δv of 1778 m/s printed as "at least 1800".
- **C11**: the redesign gives its upper stage 5600 m/s where the article's own budget implies 5484 m/s. Conservative, which strengthens its conclusion.
- **C12**: the article uses Isp 327 s at sea level for Raptor 3; that is the Raptor 2 figure. SpaceX and Wikipedia give 330 s. Conservative.
- **C13**: `1 tf = 9.81 kN` in the article vs the standard 9.80665. Irrelevant at 0.03 %, but pick one.

### What the article gets right that is easy to doubt

- The Ariane 6 comparison is not a gotcha, it is the key insight. Ariane 6's upper stage has a **worse** dry-mass fraction than Starship (15.8 % vs 12.1 %) and still delivers 22 t, because it starts from a much higher staging velocity. Structural quality is not the problem; the staging split is.
- Starship's 12 % dry-mass fraction really is good engineering for a vehicle carrying a heat shield, fins, a nose and header tanks. The article says so explicitly, and it is right to.
- The square-cube reentry argument is correct and is a real, underappreciated scaling limit.

---

## 5. Reference data

Seed dataset for the rocket library. Confidence: **P** = published, **E** = estimated by the article, **D** = derived by me.

### 5.1 Engines

| Engine | Propellants | Thrust SL (tf) | Thrust vac (tf) | Isp SL (s) | Isp vac (s) | Mass (kg) | Conf |
|---|---|---|---|---|---|---|---|
| Raptor 3 (SL) | CH4/LOX | 250 (throttled) / 280 (rated) | ~268 | 327 to 330 | 350 | 1525 | P |
| Raptor 3 Vacuum | CH4/LOX | n/a | ~300 | n/a | 380 | ~1900 | P/E |
| Raptor 2 | CH4/LOX | 230 | 258 | 327 | 347 | 1630 | P |
| Merlin 1D (SL) | RP-1/LOX | 86.2 | 93.4 | 282 to 283 | 311 to 312 | 470 | P |
| Merlin 1D Vacuum | RP-1/LOX | n/a | 100 | n/a | 348 | 490 | P |
| Vinci (Ariane 6) | LH2/LOX | n/a | 18.4 | n/a | 457 | 550 | P |
| RS-25 (Shuttle) | LH2/LOX | 190 | 232 | 366 | 452 | 3200 | P |

Raptor 3 minimum throttle is roughly 40 %, about 90 to 100 tf. This bracket is what the article uses to weigh Starship at landing, so the app needs it as an explicit parameter.

### 5.2 Stages

| Stage | Dry (t) | Propellant (t) | Engines | Isp used | Conf |
|---|---|---|---|---|---|
| Super Heavy V3 | 300 (E), 275 published for Block 1/2 | 3650 | 33 × Raptor 3 | 340 avg ascent | E/P |
| Starship V3 | 220 (E), 85 to 100 published for V1/V2 | 1600 | 3 SL + 3 Vac Raptor | 365 avg | **E, contested** |
| Falcon 9 stage 1 (Block 5) | 25.6 | 395.7 (article: 385) | 9 × Merlin 1D | ~301 avg ascent | P |
| Falcon 9 stage 2 (Block 5) | 3.9 to 4.0 | 107 (92.7 to 111 across sources) | 1 × MVac | 348 | P |
| Falcon 9 fairing | 1.9 | n/a | n/a | n/a | P |
| Ariane 6 ULPM | 6.0 | 31 to 32 | 1 × Vinci | 457 | P |
| Shuttle orbiter | 78 | n/a (external tank) | 3 × RS-25 | 452 vac | P |

### 5.3 Vehicles

| Vehicle | Liftoff mass (t) | Liftoff thrust (tf) | TWR | Staging speed | Payload LEO | Conf |
|---|---|---|---|---|---|---|
| Starship / Super Heavy V3 | 5850 | 8250 | 1.41 | ~6000 km/h | 40 t (E) / 100 t (SpaceX claim) | E/P |
| Falcon 9 (droneship) | 549 | 776 | 1.41 | ~8000 km/h | 17.5 t | P |
| Falcon 9 (expendable) | 549 | 776 | 1.41 | ~10 800 km/h | 22.8 t | P |
| Falcon 9 (RTLS) | 549 | 776 | 1.41 | ~6300 km/h | ~15 t | P |
| Space Shuttle | 2030 | 3060 | 1.5 | SRB sep ~4900 km/h | 27.5 t | P |
| Ariane 64 | 860 | 1500 | 1.8 | n/a | 21.6 t | P |

### 5.4 The article's redesign concepts

| Concept | Booster | Upper stage | Staging | Payload LEO | Payload 53° | Payload polar |
|---|---|---|---|---|---|---|
| Starship as flown | Super Heavy 300 t / 3650 t | Starship 220 t / 1600 t | 6000 km/h | 40 t | ~14 t | ~0 t |
| "Raptor 33 + Raptor 4" | 300 t / 4020 t | 140 t / 1022 t | 10 000 km/h | 110 t | 87 t | 68 t |
| "Raptor 33 + Raptor 3" | 300 t / 4608 t | 95 t / 711 t | 12 000 km/h | 120 t | n/a | n/a |
| Raptor 33 + expendable | 300 t / 4020 t | 40 t / 1022 t | 10 000 km/h | 230 t | n/a | 50+ t to Mars |
| Pessimistic booster | 400 t / 4708 t | 75 t / 560 t | 12 000 km/h | 94 t | n/a | n/a |

Upper stage masses above are inert mass including landing propellant, per the article's own bookkeeping.

### 5.5 Δv budgets

| Manoeuvre | Δv (m/s) |
|---|---|
| LEO 200 km circular, orbital velocity | 7784 |
| Typical total from pad to LEO including losses | 9300 to 9600 |
| Earth rotation bonus, due east from 26° N | 418 |
| 26° → 53° inclination penalty | ~140 (geometry), ~330 (from F9 payload chart) |
| 26° → polar penalty | ~420 (geometry), ~600 to 700 (in practice) |
| LEO → Mars transfer injection | ~3600 |
| LEO → Moon transfer injection | ~3150 |
| Deorbit from LEO | 100 to 150 |
| Super Heavy boostback (RTLS) | 1800 |
| Super Heavy landing | 600 |
| Falcon 9 entry burn (droneship) | ~500 |
| Falcon 9 landing burn | ~500 |

---

## 6. Models the app must implement

### M1: Ideal Δv (stack)

Walk stages bottom-up. For stage `i` with all stages above it plus payload as its top mass:

```
m_top   = payload + Σ (dry_j + prop_j) for all j above i
m_0     = m_top + dry_i + prop_i
m_f     = m_top + dry_i + prop_reserved_i
Δv_i    = Isp_i · g0 · ln(m_0 / m_f)
Δv_total = Σ Δv_i
```

`prop_reserved_i` is propellant held back for recovery. This one function reproduces every headline number in the article.

### M2: Payload solver (inverse problem)

Given a Δv target, stage propellants and dry masses, solve for payload. Closed form, walking top-down from the required Δv per stage; or just bisect on payload using M1. Bisection is simpler, robust, and fast enough. **This is the app's core interaction.**

### M3: Reuse propellant budget

```
prop_reserved = dry · (exp(Δv_boostback / v_e_vac) · exp(Δv_landing / v_e_sl) − 1)
```

Composed multiplicatively, in reverse burn order. Landing Δv should be built from its parts so the user can see them:

```
Δv_landing = v_residual + g0 · t_burn + throttle_penalty
```

### M4: Staging optimiser

Sweep staging velocity. At each point: booster Δv = base + (v_stage − v_ref); upper stage Δv = total budget − booster Δv; upper stage inert mass scales with its propellant by a user-adjustable coefficient; booster pays a braking burn from `v_stage` down to a survivable entry speed plus a landing burn. Output the payload curve and mark the peak. Verified against the article in [3.7](#37-independent-check-of-the-central-thesis).

### M5: Δv budget builder

Named, additive line items so nothing is a black box: orbital velocity at target altitude, minus rotation bonus, plus inclination penalty, plus gravity loss, plus drag loss, plus circularisation. Each item explained on hover.

### M6: Numerical ascent simulation

2D (downrange, altitude), integrated with `scipy.integrate.solve_ivp`, RK45, event-based staging.

State: `[x, y, vx, vy, m]`.

```
g(h)     = g0 · (R_e / (R_e + h))²
ρ(h)     = International Standard Atmosphere to 80 km, then 0
F(h)     = F_vac − A_e · p(h)
D        = ½ · ρ(h) · v² · C_d · A
ṁ        = F_vac / (Isp_vac · g0)     [constant while throttle is constant]
pitch    = gravity turn: vertical to a kick altitude, then hold thrust along velocity
```

Track cumulative losses separately by integrating each term, so the app can show a live stacked "where did my Δv go" chart. This is the single most illuminating visual for a beginner.

Library note: `ambiance` provides ISA up to 80 km directly and avoids hand-rolling the atmosphere.

### M7: Inclination and launch site

```
sin(A) = cos(i) / cos(φ)
bonus  = 465.1 · cos(φ) · sin(A)
```

Guard `i ≥ φ`; below that the orbit is unreachable without a plane change, which is a good teaching moment rather than an error dialog.

### M8: Reentry ballistic coefficient

```
β = m / (C_d · A),   A = π · (d/2)²
```

Compare vehicles on `β`. Optionally integrate a ballistic entry to show peak deceleration and peak heat flux `q̇ ∝ sqrt(ρ) · v³`.

### Implementation note: charge landing propellant once

The article budgets Starship a flat 40 t of header-tank propellant. The library instead records it as recovery *burns*, 350 m/s of landing at Isp 300 and 140 m/s of deorbit at Isp 350, which come to 38 t on a 220 t ship.

The two agree, but the burn form is better for an interactive model because it **scales with the ship's mass the way real propellant does**. A heavier ship needs more propellant to land, so every tonne added to the vehicle costs slightly more than a tonne of payload. A flat allowance hides that.

Recording it both ways at once is a bug, and was one: the first version of the library carried the 40 t residual *and* the landing burns, charging the same propellant twice and understating payload by about 30 t. The `Stage` validator catches the general case where reserves exceed the tanks, but not double-counting inside them, which is why the case-study tests check the payload against the article's independent figure.

With the correction the app reproduces the article: **37.7 t of payload at 220 t dry** against its 40 t, and **109 t at 160 t dry** against its 100 t.

### M9: Dry-mass scaling law

Stage inert mass as a function of propellant load, with a tunable exponent:

```
dry(prop) = dry_ref · (prop / prop_ref) ** k
```

`k = 1` is fully linear, which is what the article assumes throughout and which is conservative for large stages. `k = 0` holds mass fixed, which is what SpaceX's claims implicitly require. Real stages sit somewhere around `k = 0.7 to 0.9`, because engines, nose, fins and heat shield do not scale with tank length while tank mass and structural loads do.

Exposing `k` as a slider turns the single biggest hidden assumption in the whole debate into something a beginner can see and argue with. Used by the builder, by the V4 chapter and by the staging optimiser.

---

## 7. Golden numbers (test fixtures)

Red/green TDD targets. Every one recomputed independently. Tolerance 1 % unless noted.

```python
# M1: ideal delta-v
dv(m0=1900, mf=300, isp=365)                    == 6609.3   # Starship
dv(m0=5850, mf=2530, isp=340)                   == 2796.1   # Super Heavy
dv(m0=128.5, mf=21.5, isp=348)                  == 6104.3   # F9 stage 2, 17.5 t payload
dv(m0=128.5, mf=22.0, isp=348)                  == 6025.4   # ... with 0.5 t deorbit reserve

# rocket equation inverse forms
mass_ratio(dv=6609, isp=365)                    == 6.333
prop_from_final(mf=300, dv=6609, isp=365)       == 1600.0
prop_from_initial(m0=5850, dv=2796, isp=340)    == 3320.0
final_mass(m0=1293, dv=5600, isp=365)           == 270.6

# exhaust velocity
v_exhaust(isp=350)                              == 3433.3   # using g0=9.80665: 3432.3
binary_velocity(isp=350)                        == 2379.6   # NOT the article's 2428

# M2: payload solver
payload(ship_dry=220, ship_prop=1600, isp=365,
        dv=6609, residual_prop=40)              == 40.0
payload(ship_dry=160, ...)                      == 100.0    # what SpaceX's claim requires

# M3: reuse budget
reserve(dry=300, dv_boost=1800, isp_boost=330,
        dv_land=600, isp_land=330)              == 330.0    # 1.10 t/t
reserve(dry=300, dv_boost=1800, isp_boost=350,
        dv_land=600, isp_land=327)              == 311.0    # 1.04 t/t

# mass measurement from a burn (the article's method)
mass_after_burn(prop=10.0,  dv=138.9, isp=350)  == 242.2
mass_after_burn(prop=10.7,  dv=138.9, isp=350)  == 259.2
prop_burnt(thrust_tf=250, isp=327, seconds=14)  == 10.70

# thrust-to-weight and losses
twr(thrust_tf=8250, mass_t=5850)                == 1.410
net_accel_g(twr=1.410)                          == 0.410
gravity_fraction(twr=1.410)                     == 0.709
accel_after(t=40, twr0=1.410, flow_frac=0.00431) == 0.704   # Starship
accel_after(t=40, twr0=1.412, flow_frac=0.00501) == 0.766   # Falcon 9, NOT 0.875

# M7: inclination
rotation_bonus(lat=25.997, inc=25.997)          == 418.2
rotation_bonus(lat=25.997, inc=53.0)            == 280.0
rotation_bonus(lat=25.997, inc=90.0)            == 0.0

# M4: redesign chain, staging at 10 000 km/h
booster_dv_10k                                  == 3907     # article: 3920
mass_at_staging(glow=5850, dv=3907, isp=340)    == 1813     # article: 1806
booster_sep_mass(dry=300, brake_dv=1305.6,
                 land_dv=500)                   == 512.8
upper_stage_to_orbit(avail=1293, dv=5600,
                     isp=365)                   == 270.6
redesign_payload_10k                            == 110      # tol 3 %

# M4: optimiser
optimal_staging_speed(glow=5850, ...)           == 11500    # +/- 1000 km/h
payload_at_optimum                              >  2 * payload_at_6000

# classical staging theory
optimal_dv_split(isp_equal=350, eps_equal=0.08) == 0.50     # 50/50

# M8: ballistic coefficient
area_ratio(d1=9.0, d2=3.66)                     == 6.047
diameter_for_equal_beta(d_ref=3.66, mass_ratio=12) == 12.68

# M9 + V4: the scaling-exponent swing (section 3.8). tol 5 %
v4_payload(sh_prop=4050, ss_prop=2300, k=1.0)   == 12      # fully linear scaling
v4_payload(sh_prop=4050, ss_prop=2300, k=0.0)   == 108     # ship dry mass stays at 220 t
v4_payload(sh_prop=4050, ss_prop=1600, k=1.0)   == 54      # V4 booster, today's ship
stage_ratio("starship_v3")                      == 2.28
stage_ratio("starship_v4")                      == 1.76
stage_ratio("falcon9_block5")                   == 3.70
```

Additional integration-level assertion: the full Starship stack model must produce a total ideal Δv of 9400 ± 100 m/s and a mass in orbit of 300 ± 5 t, and the Falcon 9 model must produce 9250 ± 150 m/s with 17.5 t payload. If either drifts outside that, the model is miscalibrated and every downstream conclusion is worthless.

---

## 8. Teaching insights worth building an interaction around

Ranked by how much they change a beginner's mental model.

1. **The mass arriving in orbit is fixed by the rocket equation; only its composition is negotiable.** 300 t arrives regardless. Whether that is 40 t or 100 t of payload depends purely on how heavy the ship itself is. Slider on dry mass, payload updates live. This is the article's whole argument in one control.

2. **Exponential cost of speed.** The doubling ladder: 1, 3, 7, 15 tonnes of propellant for 1×, 2×, 3×, 4× the velocity. Show it as a growing tank next to a linear speed bar.

3. **Staging split is worth a factor of two in payload.** The sweep curve from [3.7](#37-independent-check-of-the-central-thesis), with a draggable staging-velocity marker and Starship, Falcon 9 and the redesigns marked on it.

4. **A worse-built stage can carry more payload.** Ariane 6's upper stage has a worse dry-mass fraction than Starship and lifts 22 t. Side-by-side, with staging velocity as the explanation.

5. **Reuse is paid for in propellant carried uphill.** Show the booster's propellant bar splitting into "used to accelerate the payload" and "used to come home". For Super Heavy's RTLS that is 330 t of the 3650 t.

6. **Low TWR wastes thrust.** At liftoff TWR 1.41, 71 % of the thrust merely holds the rocket up. A dial from TWR 1.0 (hovering forever, going nowhere) upward makes this visceral.

7. **Bigger is harder to bring back.** Square-cube: double the size, double the ballistic coefficient, deeper into thick air before slowing.

8. **The Shuttle and Starship put the same *fraction* of their liftoff mass into orbit; they differ in how much of it is cargo.** 5.2 % vs 5.1 %, but 26 % useful vs 13 % useful.

9. **Where the Δv actually goes.** The stacked loss chart from the ascent simulation: orbital velocity, gravity loss, drag loss, minus the rotation bonus.

10. **Published numbers are estimates too.** Show every input with its confidence, let the user challenge them, and show which conclusions survive. This is the difference between a propaganda tool and a teaching tool, in both directions.

---

## 9. Live context as of 16 August 2026

The article is two days old and already sits on the edge of a change. Re-check this section before each work session.

### Flight 14, expected late August 2026

Announced by Musk on SpaceX's first earnings call as a public company (4 August 2026) and corroborated by an FCC filing. Three firsts on one flight:

1. **First orbital attempt.** Flights 1 to 13 were all deliberately suborbital. Flight 13 was described as "a controlled suborbital trajectory designed to fall just short of orbit".
2. **First tower catch of the ship.** Pending regulatory approval.
3. **Booster returns to the launch site**, per the FCC filing.
4. **Operational Starlink V3 satellites deployed to orbit**, not simulators and not a suborbital toss.

**Why this matters for the app.** Flight 14 will produce the first direct measurement of what Starship actually delivers to a real orbit. That single data point either supports or refutes the article's ~40 t estimate against SpaceX's 100 t claim, and it lands right in the middle of the app's central chapter.

The app must therefore be built so this is a **data update, not a code change**: an `observed_flights` table in the YAML library with payload mass, achieved velocity, inclination and altitude per flight, rendered as points against the model's prediction curve. Add Flight 14 as an empty row now so its absence is visible.

Also note that a successful ship catch would remove one of the article's implicit assumptions, that the ship must carry landing propellant for a soft water landing, and would give the first real evidence on landing propellant reserves.

### Known flight record relevant to the model

| Flight | Date | Payload | Trajectory | Booster | Ship |
|---|---|---|---|---|---|
| 12 | 2026 | 22 Starlink V3 simulators, 37.5 t | Suborbital | Flipped after separation, most engines failed, hit the Gulf at 1450 km/h | — |
| 13 | 24 Jul 2026 | 20 Starlink V3 satellites, 34.1 t | Suborbital by design, ~500 km/h short of orbit | Boostback ended early, landing burn relit only 10 of 13 engines, destroyed on impact | Softest splashdown yet, stayed intact and operational after tipping over. Raptor relight at T+38:58 |
| 14 | late Aug 2026 (planned) | Starlink V3, operational | **First orbital attempt** | RTLS | **First tower catch attempt** |

Flight 13's stage separation was at T+2:21, SECO at T+8:05, splashdown at T+1:05:21.

### Other current context worth carrying into the app

- **Long March 10B, 10 July 2026.** China caught an orbital-class first stage at sea in a pretensioned cable net on the recovery ship *Linghangzhe*, using four hooks and no landing legs. Second nation ever to recover an orbital-class booster, first anywhere to do it with a net. This is direct evidence for the article's central recommendation, a nautical return rather than a return-to-launch-site burn, and it happened five weeks before the article was published.
- **Starship V4, 2027.** 42 Raptors total, ~142 m stacked, 4050 t booster, 2300 t ship, 300 tf per engine as a stretch goal (~10 000 tf liftoff thrust, roughly 3× Saturn V). SpaceX targets 200+ t to LEO fully reusable. See [3.8](#38-the-v4-stretch-the-articles-sharpest-prediction) for what the physics says about that.
- **Cadence claim.** Musk stated on the same earnings call an expectation of "at least one flight a day" within a year. Worth having in the app as a claim to test against the article's economic argument, but out of scope for the physics.

### Standing instruction

Any number in this document tagged **E** (estimated) or **contested** is a candidate for replacement by measurement. When new flight data arrives, update [section 5](#5-reference-data) and re-run the golden-number tests. If a golden number moves, that is information, not a bug, but it must be a deliberate, recorded change.

---

## 10. Sources

**Article under review (primary source):** ["SpaceX: Wie das Starship den Kampf gegen die Physik verliert"](https://www.golem.de/news/spacex-wie-das-starship-den-kampf-gegen-die-physik-verliert-2608-211916.html), Golem.de, August 2026 (German). The URL slug `2608` dates it to 2026-08, which is consistent with its references to Flight 13 (24 July 2026). Local copy used for this verification: `~/Downloads/starship-article.md`.

Every claim attributed to "the article" in this document traces to that piece. Attribution rule for the app: the article is the source of the *argument* and of the estimated inputs marked **E**; it is not a source for published specifications, which are cited separately below.

- [Starship flight test 13, Wikipedia](https://en.wikipedia.org/wiki/Starship_flight_test_13)
- [SpaceX Super Heavy, Wikipedia](https://en.wikipedia.org/wiki/SpaceX_Super_Heavy)
- [SpaceX Starship (spacecraft), Wikipedia](https://en.wikipedia.org/wiki/SpaceX_Starship_(spacecraft))
- [Falcon 9, Wikipedia](https://en.wikipedia.org/wiki/Falcon_9)
- [Space Shuttle, Wikipedia](https://en.wikipedia.org/wiki/Space_Shuttle)
- [SpaceX on Raptor 3 specifications](https://x.com/SpaceX/status/1819772716339339664)
- [Starship Flight 13 splashdown report, Space.com](https://www.space.com/space-exploration/launches-spacecraft/spacexs-starship-megarocket-makes-the-softest-splashdown-ever-after-launching-next-gen-starlink-satellites-in-flight-13-test-video)
- [Starship V3 debut, SatNews](https://satnews.com/2026/05/14/spacex-debuts-starship-v3-redefining-heavy-lift-launch-capability/)
- [Long March 10B sea recovery, China Daily](https://www.chinadaily.com.cn/a/202607/11/WS6a512adea310986e2b464b1e.html)
- [Long March 10B cable-net catch, Universe Today](https://www.universetoday.com/articles/china-successfully-tests-reusable-long-march-10b)
- [Musk on Mk1 mass, NextBigFuture coverage of the Sept 2019 presentation](https://www.nextbigfuture.com/2019/09/elon-musk-explains-the-greatness-of-the-spacex-super-heavy-starship.html)
- [Ariane 6 upper stage, ESA](https://www.esa.int/Enabling_Support/Space_Transportation/Ariane/Ariane_6_what_s_it_made_of)
- [Vinci engine, Wikipedia](https://en.wikipedia.org/wiki/Vinci_(rocket_engine))

Verification scripts, kept in the repo as the seed of the test suite and as the audit trail for every number above:

- `studies/article-verification/run.py` — reproduces all 64 checkable numbers in the article, sections 3.1 to 3.7
- `studies/v4-scaling/run.py` — the V4 stretch analysis and the scaling-exponent sweep, section 3.8

Both are dependency-free (standard library only) and print a pass/fail line per claim. Run with `uv run python studies/article-verification/run.py`.
