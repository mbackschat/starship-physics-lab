---
type: Engine
title: Raptor 3
description: SpaceX's full-flow staged-combustion methalox engine, in its third generation.
tags: [raptor, spacex, methalox, engine]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 5.1
    last_modified: 2026-08-16
  - id: spacex-2024
    resource: https://www.spacex.com/vehicles/starship/
    title: SpaceX, Raptor specifications, August 2024
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2026-11-30

provenance: published
feeds:
  - data/engines.yaml#raptor_3
  - data/engines.yaml#raptor_3_vacuum
---

# Raptor 3

Full-flow staged combustion, burning liquid methane and liquid oxygen. Two variants fly: a sea-level engine with a compact nozzle, and a vacuum engine whose nozzle is too large to run in atmosphere.

## What the library holds

| | Sea level | Vacuum |
|---|---:|---:|
| Thrust, sea level | 280 tf | not startable |
| Thrust, vacuum | 268 tf | see `data/engines.yaml` |
| Isp, sea level | 327 s | not applicable |
| Isp, vacuum | 350 s | higher, from the larger nozzle |
| Mass | 1,525 kg | |
| Minimum throttle | 40 % | |

Derived from the published Super Heavy Block 3 stack thrust of 80.8 MN across 33 engines.

## Two things worth knowing

**It flies throttled.** At liftoff Raptor 3 runs at roughly 250 tf, about 89 % of its 280 tf rating. Quoting the rating as if it were the liftoff thrust overstates a Super Heavy's thrust-to-weight ratio.

**Sources disagree on sea-level Isp by 3 seconds.** Wikipedia lists 330 s for the Block 3 stack; the source article uses 327 s, which is the Raptor 2 figure. The library takes 327 s, the conservative reading. Three seconds is about 1 %, comfortably inside this project's stated precision target, but it propagates into every delta-v computed from this engine and is worth knowing when a number lands 1 % from where a source says it should.

## Why specific impulse is in seconds

It is the same number in metric and US customary, which is exactly why engineers quote it that way, and why this project never converts it. See the glossary chapter.

## What would change this page

A published Raptor 3 specification from SpaceX with sea-level Isp stated directly, which would settle the 327 versus 330 question. Or Raptor 4, which is announced but has no figures attached.
