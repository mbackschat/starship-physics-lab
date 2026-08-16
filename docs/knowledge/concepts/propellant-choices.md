---
type: Concept
title: Propellant choices
description: Kerolox, methalox and hydrolox, and why the most efficient one is not the usual answer.
tags: [physics, propellant, methalox, kerolox, hydrolox, specific-impulse]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 2.1
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-08-31

provenance: derived
---

# Propellant choices

Every engine in the library burns one of three combinations, and the trade between them is not the simple ranking that specific impulse alone suggests.

| Combination | Example | Isp, sea level | Isp, vacuum |
|---|---|---:|---:|
| Kerosene / LOX | [Merlin 1D](../engines/merlin-1d.md) | 283 s | 312 s |
| Methane / LOX | [Raptor 3](../engines/raptor-3.md) | 327 s | 350 s |
| Hydrogen / LOX | Vinci, [Ariane 6](../vehicles/ariane-6.md) upper | vacuum only | 457 s |

## Hydrogen wins on paper and loses on the pad

457 s against 283 s is an enormous margin, and every doubling of the mass ratio buys a hydrolox stage 3,106 m/s against a kerolox stage's 1,924 m/s.

Three things spoil it:

**Density.** Liquid hydrogen is extraordinarily light, so the tanks are enormous. Bigger tanks mean more structure, and structure is dry mass, which is the thing [the rocket equation](the-rocket-equation.md) punishes. A hydrolox stage often gives back in tank mass much of what it gained in efficiency.

**Temperature.** It boils at 20 K. Insulation, boil-off and ground handling all cost.

**Thrust density.** Hydrolox engines tend to produce less thrust for their size, which is awkward for a first stage that has to leave the ground at all.

So hydrogen is common on **upper stages**, where vacuum efficiency dominates and the stage is small, and rare on first stages.

## Why methane, which is neither best nor cheapest

Raptor's methalox sits between kerosene and hydrogen on efficiency and above kerosene on density. Two other properties decide it:

**It does not coke.** Kerosene leaves deposits that make an engine harder to reuse without refurbishment. Methane burns clean, which matters enormously for a vehicle intended to fly repeatedly.

**It can in principle be made on Mars**, from atmospheric CO₂ and subsurface water. Whether that ever happens, it shaped the choice.

Methane is a **reusability** decision more than an efficiency one, which is the same lesson as [staging](staging.md): the interesting trades are rarely the ones the headline number describes.

## The size of the prize, in context

Raptor beats Merlin by 16 % on sea-level Isp. [Falcon 9](../vehicles/falcon-9.md) still turns a higher fraction of its liftoff mass into payload than Starship claims to.

Specific impulse enters the rocket equation linearly; the mass ratio enters through a logarithm; and where the stages separate decides the mass ratios. **The engine matters least of the three**, which is not an argument against good engines, only against expecting them to settle the question.
