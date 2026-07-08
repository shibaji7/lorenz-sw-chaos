# Portability to Other Models

This framework is not tied to one exact ionospheric state variable.

The code is organized around a generic pattern:

1. define a prognostic state
2. define deterministic source and loss terms
3. add stochastic forcing for unresolved variability
4. propagate an ensemble
5. summarize the result with probability and reduced-order diagnostics

That pattern can be ported to other space-physics or upper-atmosphere models.

## What carries over

The following pieces are reusable across problems:

- the idea of a deterministic core plus stochastic perturbations
- the ensemble workflow
- the use of exceedance probability and tail probability
- the plotting style and documentation structure
- the habit of keeping all tunable parameters in one JSON file

These are model-agnostic ideas. They do not depend on the ionosphere alone.
They are also consistent with the broader literature on stochastic
parameterization and uncertainty representation in geophysical modeling
[Berner et al. 2017](references.md#berner-2017).

## What must change

When moving to a different model, you must replace the physics-specific pieces:

- the state variable
  - electron density may become magnetic perturbation, neutral density, current
    density, temperature, or another prognostic quantity
- the source terms
  - Chapman and precipitation may be replaced by model-specific drivers
- the loss terms
  - recombination may be replaced by damping, diffusion, coupling, or transport
- the geometry
  - altitude-only models may become latitude-longitude-altitude, field-aligned,
    or along-track models
- the observables
  - thresholds and exceedance metrics should match the relevant application

## Example: a B-field model

If the goal is to model a magnetic perturbation `B`, the same workflow still
applies, but the right-hand side changes:

- the deterministic drift becomes the magnetic evolution law
- stochastic forcing represents unresolved driver variability
- the ensemble measures uncertainty in `B` rather than electron density

The plot logic would then ask questions like:

- how likely is a field perturbation to exceed a threshold?
- where are the strongest regions in space and time?
- how quickly does uncertainty spread under the chosen forcing?

## Example: a MAGE-type model

For a larger coupled model such as MAGE, the same philosophy still works.

What changes:

- the state vector is larger
- the forcing terms are more coupled
- the uncertainty may need to be injected into multiple modules
- the diagnostics may need to be shown on multiple coupled outputs

What stays the same:

- use ensembles to represent uncertainty
- compare deterministic and stochastic trajectories
- summarize tail risk with exceedance metrics
- keep the figure language simple enough for publication

This is the same reduced-order and ensemble logic commonly associated with DMD
and snapshot-based model reduction [Schmid 2010](references.md#schmid-2010),
[Tu et al. 2014](references.md#tu-2014).

## Example: SCUBAS or RAID-style workflows

If a related project uses a different forecasting pipeline, the porting strategy
is still similar:

- identify the main prognostic variable
- identify the dominant forcing and loss processes
- add a stochastic term only where the physics is unresolved or variable
- retain the same figure logic for spread, tail risk, and reduced-order modes

That is the key idea: do not port the exact equation blindly. Port the
workflow.

## Why the JSON parameter file matters

The shared parameter file makes the model easier to reuse because it separates:

- code
- physics choices
- plotting choices

That is useful when you want to swap a Chapman source term for another source
term, or change the stochastic strength without rewriting the scripts.

## Practical takeaway

If another model has:

- a state variable
- a source term
- a loss term
- uncertainty in the forcing

then this repository provides a reusable template for:

- deterministic vs stochastic comparison
- ensemble spread visualization
- exceedance and tail probability plots
- clean publication-style figure rendering
