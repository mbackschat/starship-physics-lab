# ByteByteGo infographic style study

This study distils the recurring visual grammar in the supplied ByteByteGo reference set and applies it to a single Starship explainer. It is a design reference, not a licence to copy ByteByteGo branding, logos or individual illustrations.

## Visual grammar

### Start with one question

The poster title names the subject as a question or a compact explanation. A short colored rule at the left anchors the title. There is no introductory paragraph.

### Turn the explanation into numbered panels

Portrait examples use four to six sections. Each section has a black pill-shaped header, usually overlapping a thin rounded border. The number is either embedded in the pill or shown in an adjacent black circle. This creates a strong top-to-bottom reading order without relying on long prose.

Landscape examples use the same logic with fewer, wider stages. A single flow runs left to right, connected by arrows.

### Give each panel one job

Each section explains one mechanism, comparison or consequence. Internal subdivisions use thin rules or tinted boxes, but do not create a second competing hierarchy. The reader should understand the panel from its diagram and labels before reading any supporting sentence.

### Use flat outlined objects as the nouns

Rockets, chips, servers, databases and sensors are compact, front-facing illustrations with thick dark outlines, simple fills and almost no shading. They function as labeled nouns rather than decorative art. Repeated objects keep the same shape and color so comparisons are immediate.

### Use arrows, bars and containers as the verbs

Solid arrows show the main causal path. Dashed arrows show requests, messages or secondary movement. Rounded containers show boundaries and ownership. Bars and repeated tiles make quantities visible. The artwork avoids ornamental scenes, dramatic lighting and perspective because those compete with the mechanism.

### Keep color semantic and sparse

The reference palette is a white or faintly tinted ground with black text and borders, then a small family of clear accents: mint green, sky blue, violet, yellow and coral. One accent is assigned to one role within a panel. Pale tints may fill containers, while saturated versions mark the key object or result.

### Make typography carry the hierarchy

The title is large, bold and left aligned. Panel pills use uppercase white text. Subheads are bold black. Supporting labels are short and close to the object they name. Numbers are larger than their units. Body copy is rare, and the smallest text is reserved for assumptions or provenance.

### Prefer comparisons over standalone facts

The strongest panels place two systems, two states or two outcomes side by side. Differences are aligned on a shared baseline and called out with a single arrow, badge or result bar. A panel usually ends with one highlighted conclusion rather than a list of observations.

## Starship poster blueprint

The poster should be a portrait infographic with a roughly 4:5 canvas, a white background, generous outer margin and six stacked sections. It should use the visual grammar above without the ByteByteGo name or logo.

### Title

**Why Starship's Payload Hinges on Staging**

Subtitle: **The rocket equation, one unknown mass, and a 2.2× payload gap**

### 1. The load-bearing unknown

Show one bar labeled **≈300 t reaches orbit**, then compare two possible compositions:

- **220 t dry ship + ≈38 t recovery propellant → 38 t payload**
- **160 t dry ship + ≈28 t recovery propellant → 109 t payload**

Mark the ship dry mass as **CONTESTED**. The two compositions total 296 to 297 t, rounded to ≈300 t in the headline. The point is that the total arriving mass barely moves; ship and payload trade almost one for one.

### 2. Why speed gets expensive

Show the rocket equation, `Δv = vₑ · ln(m₀ / m_f)`, beside the doubling ladder for one tonne of dry vehicle:

- **1× speed → 1 t propellant**
- **2× → 3 t**
- **3× → 7 t**
- **4× → 15 t**

The visual should grow the propellant blocks exponentially while the speed steps stay equal.

### 3. Starship stages early

Compare the stage propellant split:

- **Starship V3: 2.28 : 1, separates at 6,000 km/h**
- **Falcon 9: 3.70 : 1, separates at 8,000 km/h**

Add **Super Heavy supplies only 30% of ideal Δv**. The smaller upper stage must otherwise carry more of the velocity, and its own mass competes directly with cargo.

### 4. Move the split, move the payload

Draw a simple hump-shaped staging sweep from **6,000 km/h** to **16,000 km/h**. Mark the current split at the left and the model optimum near **11,500 km/h**. Highlight **2.2× payload at the optimum**. Add a smaller badge: **Article redesign at 10,000 km/h: ≈110 t**.

The 2.2× result is from the project's controlled staging study. The 110 t figure is the article's redesign reproduced independently. They use related but not identical assumptions and must not be presented as the same calculation.

### 5. Reuse is paid for uphill

Split Super Heavy's **3,650 t propellant** into **3,320 t ascent** and **≈330 t return**. Label the return budget **1,800 m/s boostback + 600 m/s landing**. Beside it, show the ship reserving **≈38 t** for deorbit and landing at the 220 t dry-mass estimate.

### 6. What the project verified

Use a large green badge: **61 / 64 article numbers reproduce within 2%**.

Show the three corrections in compact rows:

- **2,380 m/s**, not 2,428, for one Raptor-vacuum mass doubling
- **22–25 t** calculated landing burn; 30 t is a padded reserve
- **0.766 g vs 0.704 g** at T+40 s; the gap is smaller than claimed

End with one conclusion bar: **Raptor is not the bottleneck. The staging split is. Dry mass decides the payload.**

## Accuracy and tone rules

- Distinguish **PUBLISHED**, **ESTIMATED**, **CONTESTED** and **MODELLED** with small badges rather than presenting every number as equally certain.
- Keep tonnes, kilometres per hour, metres per second and seconds attached to every value.
- Call the 220 t ship dry mass an estimate reconstructed from Flight 13, never a measurement.
- Do not describe the 100 t SpaceX figure as disproved before an orbital payload flight measures it directly.
- Do not reuse the source article's loaded verdicts. The poster explains the mechanism and lets the numbers carry the conclusion.
- Do not use ByteByteGo branding, the supplied reference logos or copied illustrations.
- Do not add unverified future-flight claims, cost claims or economic conclusions. They are outside this poster's physics scope.
