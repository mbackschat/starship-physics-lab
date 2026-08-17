# Reproduce the Starship staging infographic

Use this recipe only for the existing poster or a requested derivative of it. The current full-resolution master is `docs/images/starship-staging-infographic.png`.

## Verification sources

The exact copy below was checked against:

- `docs/physics-reference.md`
- `studies/article-verification/finding.md`
- `studies/staging-split/finding.md`
- `docs/knowledge/vehicles/starship-v3.md`
- `docs/knowledge/vehicles/super-heavy-v3.md`
- `docs/knowledge/concepts/the-rocket-equation.md`
- `docs/knowledge/concepts/staging.md`
- `docs/knowledge/concepts/reuse.md`

Run the `review-physics` workflow before changing any number. Do not treat the 220 t ship dry mass as measured; it is contested and reconstructed from Flight 13.

## Canvas and title

Create a portrait poster, approximately 2:3, with one continuous white sheet, a thin rounded black outer border and six stacked sections.

Title: **Why Starship's Payload Hinges on Staging**

Subtitle: **The rocket equation, one unknown mass, and a 2.2× payload gap**

## 1. The load-bearing unknown

Header: **THE LOAD-BEARING UNKNOWN**

Show one bar labelled **≈300 t reaches orbit** and two aligned compositions:

- **220 t dry ship + ≈38 t recovery propellant → 38 t payload**
- **160 t dry ship + ≈28 t recovery propellant → 109 t payload**

Add a **CONTESTED** badge to the dry-mass assumption.

Conclusion: **Ship mass and cargo trade almost one for one.**

The compositions total 296 to 297 t, rounded to ≈300 t in the headline. Do not omit recovery propellant, because the visible parts would no longer add to the total.

## 2. Why speed gets expensive

Header: **WHY SPEED GETS EXPENSIVE**

Show `Δv = vₑ · ln(m₀ / m_f)` beside four equal speed steps with exponentially growing propellant blocks:

- **1× → 1 t**
- **2× → 3 t**
- **3× → 7 t**
- **4× → 15 t**

Caption: **Equal speed steps. Exponentially more propellant.**

## 3. Starship stages early

Header: **STARSHIP STAGES EARLY**

Compare aligned two-stage rockets:

- **STARSHIP V3**, **2.28 : 1**, **6,000 km/h**
- **FALCON 9**, **3.70 : 1**, **8,000 km/h**

Callout: **Super Heavy: 30% of ideal Δv**

Conclusion: **The ship must do most of the work, and its mass competes with cargo.**

## 4. Move the split, move the payload

Header: **MOVE THE SPLIT, MOVE THE PAYLOAD**

Draw a simple hump-shaped staging sweep from **6,000 km/h** to **16,000 km/h**. Mark **6,000 km/h (current)** and **≈11,500 km/h (optimum)**.

Primary badge: **2.2× PAYLOAD AT OPTIMUM**

Secondary badge: **10,000 km/h redesign: ≈110 t**

Note: **Controlled sweep and redesign use related, not identical, assumptions.**

The 2.2× result comes from the controlled staging study. The ≈110 t result is the article's redesign reproduced independently. Do not present them as the same calculation.

## 5. Reuse is paid for uphill

Header: **REUSE IS PAID FOR UPHILL**

Split **3,650 t propellant** into **3,320 t ascent** and **≈330 t return**. Label the return path **1,800 m/s boostback** and **600 m/s landing**. Beside it, show a ship tank labelled **≈38 t deorbit + landing**.

## 6. What the project verified

Header: **WHAT THE PROJECT VERIFIED**

Primary badge: **61 / 64 numbers reproduce within 2%**

Correction rows:

- **2,380 m/s, not 2,428**
- **22–25 t burn; 30 t is a padded reserve**
- **0.766 g vs 0.704 g at T+40 s**

Caption: **The corrections do not change the staging conclusion.**

## Conclusion and footer

Conclusion bar: **Raptor is not the bottleneck. The staging split is. Dry mass decides the payload.**

Footer: **Source: Golem.de article + independent Starship Physics Lab model**

## Accuracy and tone locks

- Keep every unit attached to its value.
- Distinguish contested and modelled values from measurements.
- Do not say the 100 t claim is disproved before an orbital payload flight measures it directly.
- Do not reuse the source article's loaded verdicts.
- Do not add future-flight, cost or economic claims.
- Do not use ByteByteGo or SpaceX logos.

The current master required one targeted correction after its first render: adding recovery propellant to both orbital-mass compositions. Preserve that correction in every regeneration.
