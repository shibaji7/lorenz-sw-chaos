# Model Mathematics

This page summarizes the equations used in the code. For a broader
undergraduate-to-graduate level explanation of why the model is structured this
way, see [Space Weather Context](space_weather_context.md).

The model evolves electron density `n(h,t)` with a continuity equation driven
by solar Chapman photoionization, a Gaussian precipitation proxy, and
multiplicative stochastic forcing.

## State and notation

Let

$$
n(h,t) \ge 0
$$

denote electron density at altitude `h` and time `t`.

The production terms are:

$$
P_{\mathrm{solar}}(h,t)
$$

for Chapman photoionization and

$$
P_{\mathrm{precip}}(h,t)
$$

for precipitation-driven ionization.

The loss model uses quadratic recombination and linear removal:

$$
\alpha n^2 + \beta n.
$$

## Chapman production

The Chapman profile implemented in `src/lorenzsw/chapman.py`
is

$$
P_{\mathrm{solar}}(h,t) = P_0(t)\exp\!\left(1 - z - \sec(\chi)\,e^{-z}\right)
$$

with

$$
z = \frac{h-h_m}{H}.
$$

Where:

- \(P_0(t)\) is the peak production rate
- \(h_m\) is the Chapman layer peak altitude
- \(H\) is the Chapman scale height
- \(\chi\) is the solar zenith angle proxy

This is the standard Chapman functional form used to create a compact ionization
layer with an asymmetric altitude profile [Chapman 1931](references.md#chapman-1931).

## Gaussian precipitation proxy

The precipitation forcing is implemented in `src/lorenzsw/precipitation.py`.

The code uses a normalized Gaussian profile:

$$
P_{\mathrm{precip}}(h,t)
= \frac{Q_0(t)}{\Delta\varepsilon_{\mathrm{ion}}\sqrt{2\pi}H_p}
\exp\!\left[-\frac{(h-h_p(t))^2}{2H_p^2}\right].
$$

In this notation:

- `Q_0(t)` is the precipitation energy proxy
- `\Delta\varepsilon_{\mathrm{ion}}` is the ionization energy per event
- `h_p(t)` is the precipitation peak altitude
- `H_p` is the precipitation width

This is the implementation of the precipitation parameterization used in the
figure scripts. It is a compact proxy, not a full first-principles precipitation
model. The Gaussian center `h_p(t)` says where the energetic deposition is most
strong, and the width `H_p` says how vertically spread out the forcing is.

The normalization is chosen so that the altitude integral recovers the input
precipitation proxy up to the chosen conversion factor. That makes the term easy
to tune and easy to compare across runs.

This is also why the form is useful in atmospheric sciences: it behaves like a
controlled source term with a physically interpretable center, width, and
amplitude. It is a teaching-friendly way to represent localized particle
precipitation without pretending the microphysics is fully resolved.

The individual Chapman and precipitation source terms are shown in
[Source Terms](source_terms.md). Those figures separate the raw production
terms from the density response, which is useful when you want to explain what
the terms themselves are doing before they are mixed into the full continuity
equation.

If you want to relate it to the more compact notation sometimes written in
notes, it is the same Gaussian idea:

$$
P_{\mathrm{precip}} \propto Q_0(t)\,\exp\!\left[-\frac{(h-h_p(t))^2}{2H_p^2}\right].
$$

The version above simply includes the normalization used by the code.

## Continuity equation

The deterministic drift follows

$$
\frac{\partial n}{\partial t}
= P_{\mathrm{solar}} + P_{\mathrm{precip}}
- \alpha n^2 - \beta n.
$$

This is the equation implemented in `src/lorenzsw/continuity.py`.

Interpretation:

- `P_{\mathrm{solar}}` creates background ionization
- `P_{\mathrm{precip}}` injects additional localized forcing
- `\alpha n^2` models loss by recombination
- `\beta n` models first-order removal

## Stochastic forcing

The multiplicative diffusion amplitude in `src/lorenzsw/sde.py`
is

$$
g(n,t)
= \sigma_0\left(1 + \beta_g \frac{P_{\mathrm{precip}}}{P_{\max}}\right)\sqrt{n}.
$$

The `\sqrt{n}` factor keeps the stochastic term density dependent, while the
precipitation-dependent multiplier increases variability under stronger
forcing.

This style of discretization is standard in stochastic differential equations
[Higham 2001](references.md#higham-2001), [Øksendal 2003](references.md#oksendal-2003).

The corresponding Euler-Maruyama step is

$$
n_{k+1} = \left|n_k + f(n_k,t_k)\Delta t + g(n_k,t_k)\Delta W_k\right|,
$$

where `\Delta W_k \sim \mathcal{N}(0,\Delta t)`.

The absolute value acts as a reflecting boundary so density remains
non-negative.

## Ensemble statistics

The ensemble solver in `src/lorenzsw/ensemble.py`
propagates many stochastic realizations from the same initial condition.

Given an ensemble `n^{(m)}(h,t)`, the exceedance probability for threshold
`n_*` is

$$
\Pr\{n(h,T) > n_*\}
$$

estimated numerically by the fraction of ensemble members above threshold.

That is the quantity shown in Figure 4.

An exceedance map is the same idea, but shown over both altitude and threshold:
it answers the question "for this altitude and this cutoff, what fraction of the
ensemble lies above the cutoff?"

## Transfer-operator compression

The DMD/transfer-operator diagnostics in Figure 3 approximate the ensemble
dynamics with a low-rank linear operator. The dominant modes represent coherent
temporal evolution patterns in the density snapshots, while smaller modes
capture residual structure [Schmid 2010](references.md#schmid-2010), [Tu et al. 2014](references.md#tu-2014).

The operator viewpoint also connects to Koopman-style spectral decompositions
[Mezić 2005](references.md#mezic-2005).

## Figure mapping

- Figure 1 is a conceptual schematic of the forcing-flow-observable pipeline
- Figure 2 compares deterministic and stochastic solutions
- Figure 3 shows low-rank transfer-operator structure
- Figure 4 shows exceedance probabilities and tail statistics
- Figure 5 shows Chapman photoionization and the equilibrium response
- Figure 6 shows the precipitation proxy and the equilibrium response

The forecast example in [Example Forecast](example_forecast.md) uses the same
equations, but it presents the uncertainty growth directly at 90 km altitude.
