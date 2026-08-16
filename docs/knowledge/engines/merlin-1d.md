---
type: Engine
title: Merlin 1D
description: Falcon 9's kerosene engine, and the reason Raptor's efficiency advantage is smaller than it looks.
tags: [merlin, spacex, kerolox, engine, falcon-9]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 5.1
    last_modified: 2026-08-16
  - id: wiki-f9
    resource: https://en.wikipedia.org/wiki/Falcon_9
    title: Wikipedia, Falcon 9, Block 5 figures
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-02-28

provenance: published
feeds:
  - target: data/engines.yaml#merlin_1d
    asserts:
      thrust_sl_tf: 86.2
      thrust_vac_tf: 93.4
      isp_sl_s: 283.0
      isp_vac_s: 312.0
      mass_kg: 470.0
      min_throttle: 0.57
  - data/engines.yaml#merlin_1d_vacuum
---

# Merlin 1D

Gas-generator kerolox. Nine on a Falcon 9 first stage, one vacuum variant on the second.

| | Sea level | Vacuum |
|---|---:|---:|
| Thrust | 86.2 tf | 93.4 tf |
| Isp | 283 s | 312 s |
| Mass | 470 kg | |
| Minimum throttle | 57 % | |

## What it is here to show

**The engine is the smaller half of the story.**

Raptor 3 manages 327 s at sea level against Merlin's 283 s, a 16 % advantage in efficiency, and Raptor is a far more sophisticated machine: full-flow staged combustion against a gas generator, methane against kerosene.

Yet Falcon 9 turns a higher fraction of its liftoff mass into payload than Starship claims to. Better engines did not settle it, because [where the stages separate](../vehicles/falcon-9.md) mattered more.

That is worth holding onto, because "build a better engine" is the intuitive answer to every rocket problem and it is usually the expensive one. Specific impulse enters the rocket equation linearly; the mass ratio enters through a logarithm. Improving the engine moves the whole curve, which is real, but it moves it far less than most people expect.

## A note on throttling

57 % minimum is high, and it is why Falcon 9 shuts engines down rather than throttling deeply during landing. Raptor's 40 % gives Starship more room, which matters for a vehicle that lands under power.

## What would change this page

Merlin is a mature, published engine and its figures have been stable for years. The likeliest change is a Block 5 thrust uprating.
