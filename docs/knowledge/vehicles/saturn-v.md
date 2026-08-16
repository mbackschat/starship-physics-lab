---
type: Vehicle
title: Saturn V
description: Still the best payload fraction ever flown, and the antidote to assuming newer means better.
tags: [saturn-v, nasa, apollo, historic, reference]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 5.2
    last_modified: 2026-08-16
  - id: nasa
    resource: https://www.nasa.gov/reference/saturn-v/
    title: NASA, Saturn V
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-06-30

provenance: published
feeds:
  - target: data/vehicles.yaml#saturn_v
    asserts:
      payload_leo_t: 140.0
---

# Saturn V

Retired in 1973, and it still holds the best payload fraction in the library.

| | Liftoff mass | Payload | Payload fraction |
|---|---:|---:|---:|
| **Saturn V** | 2,944 t | 140 t | **4.75 %** |
| Falcon 9, expendable | 557 t | 22.8 t | 4.09 % |
| Falcon 9, droneship | 552 t | 17.5 t | 3.17 % |
| Ariane 64 | 837 t | 21.6 t | 2.58 % |
| Starship V3, as claimed | 5,870 t | 100 t | 1.70 % |

## Why it wins, and why that is not an insult to anyone

Three stages instead of two, all expended, and a hydrogen upper stage at high specific impulse.

**Every one of those is a choice Starship deliberately rejected.** Saturn V threw away three stages per flight and flew thirteen times. Starship keeps both stages and intends to fly them repeatedly. A vehicle optimised for payload fraction and a vehicle optimised for cost per tonne are solving different problems, and payload fraction is the wrong scoreboard for the second one.

So the honest reading is not "Saturn V was better". It is that **payload fraction is what you give up when you decide to bring the rocket home**, and the size of that sacrifice is worth seeing plainly.

| Stage | Dry fraction | Δv contributed |
|---|---:|---:|
| S-IC first | 6.2 % | 3,296 m/s |
| S-II second | 9.1 % | 3,626 m/s |
| S-IVB third | 12.6 % | 2,138 m/s |

Note the S-IVB at 12.6 %, almost identical to Starship's ship at 12.1 %. Sixty years apart, and the two upper stages are built to the same standard by this measure. What separates the vehicles is architecture, not craft.

## The third stage is the interesting part

Two stages get Saturn V most of the way; the third is small, efficient and staged very late. That is the shape the staging chapter argues for, arrived at in 1967 without anyone running a sweep on a laptop.

It is also why the comparison with Starship is fair despite the sixty years: both are asked to put a large mass into low Earth orbit, and the model treats them identically.

## What would change this page

Nothing. Saturn V is a closed historical record, which is why its `stale_after` is the most distant in the corpus. It is here as a fixed point: any model that cannot reproduce a vehicle whose every number was published decades ago should not be trusted on one whose key number is unpublished.
