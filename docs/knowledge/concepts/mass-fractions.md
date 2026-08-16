---
type: Concept
title: Mass fractions
description: How to read dry-mass fraction and payload fraction, and the trap in comparing them across vehicles.
tags: [physics, mass-fraction, payload-fraction, dry-mass]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 3.5
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-08-31

provenance: derived
---

# Mass fractions

Two ratios do most of the comparing in this project, and one of them is routinely misread.

## Dry-mass fraction: how well a stage is built

A stage's own weight divided by its weight when full. **Lower is better**: more of what was lifted was propellant doing useful work.

| Stage | Dry-mass fraction |
|---|---:|
| [Saturn V](../vehicles/saturn-v.md) S-IC first | 6.2 % |
| [Ariane 6](../vehicles/ariane-6.md) boosters | 6.7 % |
| Saturn V S-II second | 9.1 % |
| Ariane 6 core | 11.3 % |
| [Starship](../vehicles/starship-v3.md) ship | 12.1 % |
| Saturn V S-IVB third | 12.6 % |
| Ariane 6 upper (ULPM) | 16.2 % |

Around 5 % is excellent for an expendable stage. 12 % sounds poor until you remember that stage is also carrying a heat shield, flaps and a nose so it can come home.

**Upper stages are always worse than lower ones.** They are smaller, so structure is a larger share, and they carry the fittings the payload needs. Comparing an upper stage against a booster tells you nothing.

## The trap

**A worse-built stage can carry more.** Ariane 6's upper stage is 16.2 % against Starship's 12.1 %, and lifts a larger fraction of its vehicle's liftoff mass.

The reason is [staging](staging.md). Ariane's upper stage starts fast, so it needs less of its own velocity, so its own weight matters less. Starship's ship separates at 6,000 km/h and must supply far more itself.

So dry-mass fraction measures *construction*. It does not measure *performance*, and treating it as though it did is the single most common mistake in these comparisons.

## Payload fraction: the fairest single number

Payload divided by liftoff mass. It compares what you got against everything it took.

| Vehicle | Payload fraction |
|---|---:|
| Saturn V | 4.75 % |
| Falcon 9, expendable | 4.09 % |
| [Falcon 9](../vehicles/falcon-9.md), droneship | 3.17 % |
| Ariane 64 | 2.58 % |
| Starship V3, as claimed | 1.70 % |

Under 1 % is normal across the industry, and around 4 % is exceptional.

It is the fairest measure available, and it is still **the wrong scoreboard for a reusable vehicle**, because a vehicle that keeps its stages is deliberately trading this number for cost per flight. See [what reuse costs](reuse.md).

## The one that decides the Starship argument

Neither of these, in the end. The disputed quantity is the ship's **absolute dry mass**, unpublished since 2019, with credible estimates from 85 t to 220 t.

[The rocket equation](the-rocket-equation.md) fixes the total reaching orbit at 296 to 298 t no matter which you believe. Every tonne of ship is a tonne that is not cargo, one for one. That is why the number matters and why no ratio substitutes for it.
