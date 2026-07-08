# Chaos Model Details

This page is the deeper follow-on to [Space Weather Context](space_weather_context.md).
It is written for readers who want the mathematics behind the model after the
motivation has already been established.

## The dynamical picture

The basic idea is still simple: the model is a physical time-evolution law with
an added uncertainty term.

A compact way to write the model is as a nonlinear evolution law:

$$
\frac{d\mathbf{x}}{dt} = \mathbf{f}(\mathbf{x}, t),
$$

where `\mathbf{x}` is the state of the ionospheric model and `\mathbf{f}`
contains the forcing, loss, and coupling terms.

If the model is perturbed by unresolved variability, the evolution becomes a
stochastic differential equation:

$$
d\mathbf{x} = \mathbf{f}(\mathbf{x}, t)\,dt + \mathbf{G}(\mathbf{x}, t)\,d\mathbf{W}_t.
$$

Here `\mathbf{G}` controls the strength and direction of the stochastic
fluctuations, and `d\mathbf{W}_t` is a Wiener increment.

This is the mathematical core of the project:

- deterministic motion describes the mean physical tendency
- stochastic forcing describes unresolved variability
- ensembles reveal the spread created by both sensitivity and forcing

## What chaos means in this model

Chaos means that the deterministic flow has sensitivity to initial conditions.
If `\lambda_{\max} > 0`, then nearby trajectories separate roughly like

$$
\|\delta \mathbf{x}(t)\| \sim \|\delta \mathbf{x}(0)\| e^{\lambda_{\max} t}.
$$

This matters because the ionosphere is forced by intermittent processes that are
not fully known at the resolved scale. A small uncertainty in forcing can grow
into a meaningful forecast difference.

That is the same basic predictability issue that appears in atmosphere-ocean
coupled systems, geomagnetic dynamics, and flare-like threshold systems
[Lorenz 1963](references.md#lorenz-1963),
[Vassiliadis et al. 1990](references.md#vassiliadis-1990),
[Baker et al. 1990](references.md#baker-1990),
[Sharma 1995](references.md#sharma-1995).

## Attractor geometry

The long-time behavior of a nonlinear dissipative system often concentrates on
an attractor:

$$
\mathcal{A} = \bigcap_{t>0} \overline{\bigcup_{\tau>t}\phi_{\tau}(\mathcal{B})}.
$$

In plain language, the attractor is the set of states the system repeatedly
visits after transients die out.

Why this matters here:

- the system does not wander arbitrarily far
- the dynamics are constrained by forcing and dissipation
- the spread in forecasts is organized around a structured set of states

A strange attractor is not just a point or a smooth orbit. It can be folded,
stretchy, and geometrically complicated. That is why a system can look ordered
in the long run while still being hard to predict in detail.

## Transfer operators

The transfer-operator view is useful because it shifts the question from
individual trajectories to distributions.

If `\rho(x,t)` is a probability density over states, then a transfer operator
propagates densities:

$$
\rho_{t+\Delta t} = \mathcal{P}^{\Delta t}\rho_t.
$$

If `g(x,t)` is an observable, the Koopman operator propagates observables:

$$
g_{t+\Delta t} = \mathcal{K}^{\Delta t} g_t.
$$

These operators are not replacing the physics. They are summarizing the
evolution in a way that can expose coherent structures, decay rates, and
metastable regimes.

This is why DMD is useful in the repository:

- the spectrum shows dominant decay rates and oscillations
- the leading modes identify coherent vertical structure
- the reduced operator gives a compact description of ensemble evolution

The operator viewpoint is standard in reduced-order modeling and Koopman theory
[Mezić 2005](references.md#mezic-2005),
[Schmid 2010](references.md#schmid-2010),
[Tu et al. 2014](references.md#tu-2014).

## Why this is a good first chaos model for space weather

This project is intentionally not a full ionospheric forecasting system. It is a
first-pass chaos-informed space-weather model.

That is valuable because it gives you:

- a physical state equation
- a visible source-loss balance
- an explicit stochastic term
- an ensemble interpretation
- attractor and transfer-operator diagnostics

That combination is useful for teaching and for research because it keeps the
model small enough to understand, but still rich enough to show the core
ideas:

- sensitivity to perturbations
- regime structure
- forecast divergence
- tail risk
- operator-based compression

## Benefits relative to simpler alternatives

Compared with a purely deterministic model:

- the stochastic model shows uncertainty growth explicitly
- the ensemble shows a distribution of futures instead of one line

Compared with a Gaussian Process surrogate:

- the SDE keeps the physical time-evolution law in the foreground
- the GP is better for interpolation, but not as natural for explicit dynamics

Compared with perturbing inputs in a deterministic ensemble:

- the SDE can place uncertainty directly into the governing law
- this is useful when the unresolved variability acts continuously rather than
  only through initial conditions

## Limitations

This chaos framing has limitations:

- the attractor picture is approximate because the full ionosphere is far more
  complex
- the transfer-operator view is low-rank and finite-dimensional in practice
- the stochastic forcing is phenomenological, not a microscopic derivation
- the model is intended for insight, not operational replacement

That said, the payoff is clear: the model exposes how chaos, intermittency, and
uncertainty show up in a space-weather setting while still remaining
interpretable.

## Where this connects back to the rest of the docs

- [Space Weather Context](space_weather_context.md) explains why this framing is
  useful in space physics
- [Model Mathematics](math_description.md) gives the equations used by the code
- [Figure Notes](figure_notes.md) explains how the attractor, ensemble, and
  exceedance plots are read
