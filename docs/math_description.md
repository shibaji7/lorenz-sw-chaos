# Model Mathematics

This page is the equation reference for the repository. It collects the model
state, source terms, deterministic drift, stochastic forcing, ensemble
statistics, and reduced-order diagnostics used by the code.

For the broader motivation and modeling context, see
[Space Weather Context](space_weather_context.md). For figure-by-figure
interpretation, see [Figure Notes](figure_notes.md) and
[Claim Figure Set](claim_figure_notes.md).

## State and notation

The model state is the electron density profile

$$
n(h,t) \ge 0,
$$

where \(h\) is altitude and \(t\) is time.

On a discrete altitude grid \(h_i\), the numerical solver advances the vector

$$
\mathbf{n}(t) = \bigl(n(h_1,t), n(h_2,t), \dots, n(h_N,t)\bigr)^\mathsf{T}.
$$

The total production is the sum of a solar term and a precipitation term:

$$
P_{\mathrm{tot}}(h,t) = P_{\mathrm{solar}}(h,t) + P_{\mathrm{precip}}(h,t).
$$

The loss model is

$$
L(n) = \alpha n^2 + \beta n,
$$

with quadratic recombination coefficient \(\alpha\) and linear removal
coefficient \(\beta\).

## Chapman photoionization

The Chapman photoionization term is

$$
P_{\mathrm{solar}}(h,t)
= P_0(t)\exp\!\left(1 - z - \sec(\chi)\,e^{-z}\right),
$$

where

$$
z = \frac{h - h_m}{H}.
$$

Here:

- \(P_0(t)\) is the peak photoionization rate
- \(h_m\) is the Chapman layer peak altitude
- \(H\) is the Chapman scale height
- \(\chi\) is the solar zenith angle proxy

This is the classical Chapman functional form used to represent a broad solar
ionization layer [Chapman 1931](references.md#chapman-1931).

In the code, this is implemented in
`src/lorenzsw/chapman.py`.

## Precipitation proxy

The precipitation source is represented by a normalized Gaussian layer:

$$
P_{\mathrm{precip}}(h,t)
= \frac{Q_0(t)}{\Delta\varepsilon_{\mathrm{ion}}\sqrt{2\pi}\,H_p}
\exp\!\left[-\frac{(h-h_p(t))^2}{2H_p^2}\right].
$$

The symbols mean:

- \(Q_0(t)\) is the precipitation energy-flux proxy
- \(\Delta\varepsilon_{\mathrm{ion}}\) is the ionization-energy conversion scale
- \(h_p(t)\) is the precipitation peak altitude
- \(H_p\) is the precipitation width

This is a compact parameterization of localized particle deposition. It is not
a full microphysical precipitation model, but it gives a controlled source
shape with a clear center, width, and amplitude.

The normalization is chosen so the integral over altitude recovers the forcing
proxy up to the conversion factor:

$$
\int_{-\infty}^{\infty} P_{\mathrm{precip}}(h,t)\,dh
= \frac{Q_0(t)}{\Delta\varepsilon_{\mathrm{ion}}}.
$$

That normalization is what makes the term easy to compare across runs and easy
to tune in the figure scripts.

The implementation is in
`src/lorenzsw/precipitation.py`.

The precipitation figure notes use the same notation:

- \(Q_0\) controls the source strength
- \(h_p\) controls the peak altitude
- \(H_p\) controls the vertical width
- \(\Delta\varepsilon_{\mathrm{ion}}\) sets the conversion scale

## Deterministic continuity equation

The deterministic continuity equation used by the model is

$$
\frac{\partial n}{\partial t}
= P_{\mathrm{solar}} + P_{\mathrm{precip}} - \alpha n^2 - \beta n.
$$

Equivalently, the deterministic drift is

$$
f(n,t) = P_{\mathrm{solar}}(h,t) + P_{\mathrm{precip}}(h,t)
- \alpha n^2 - \beta n.
$$

Interpretation:

- \(P_{\mathrm{solar}}\) adds broad background ionization
- \(P_{\mathrm{precip}}\) adds localized particle-driven ionization
- \(\alpha n^2\) removes density through recombination
- \(\beta n\) removes density through first-order loss

This drift is implemented in
`src/lorenzsw/continuity.py`.

## Stochastic differential equation

The stochastic model adds multiplicative diffusion:

$$
dn = f(n,t)\,dt + g(n,t)\,dW_t.
$$

The diffusion amplitude is

$$
g(n,t)
= \sigma_0\left(1 + \beta_g \frac{P_{\mathrm{precip}}(h,t)}{P_{\max}}\right)\sqrt{\max(n,0)}.
$$

Here:

- \(\sigma_0\) sets the baseline stochastic strength
- \(\beta_g\) controls how strongly precipitation modulates the noise
- \(P_{\max}\) is the precipitation scale used for nondimensionalization

The square-root dependence makes the stochastic forcing density dependent, so
larger densities can carry larger fluctuations.

In the code, the Euler-Maruyama update uses one independent Gaussian increment
per altitude grid point:

$$
\Delta W_k \sim \mathcal{N}(0,\Delta t).
$$

The update is

$$
n_{k+1}
= \left|n_k + f(n_k,t_k)\Delta t + g(n_k,t_k)\Delta W_k\right|.
$$

The absolute value is the non-negativity safeguard used by the solver.

This is the main stochastic stepping rule in
`src/lorenzsw/sde.py`.

### Stable loss treatment

The repository also includes a semi-implicit alternative for the loss term:

$$
n_{k+1}^{\mathrm{det}}
= \frac{n_k + P_{\mathrm{tot}}(h,t_k)\Delta t}
{1 + \alpha n_k \Delta t + \beta \Delta t},
$$

followed by the same stochastic perturbation and reflection step:

$$
n_{k+1}
= \left|n_{k+1}^{\mathrm{det}} + g(n_k,t_k)\Delta W_k\right|.
$$

This IMEX-style update is useful when the explicit step is too stiff under
strong forcing, because it treats the quadratic and linear losses more
stably.

## Ensemble propagation

An ensemble is a collection of trajectories

$$
\left\{\mathbf{n}^{(m)}(t)\right\}_{m=1}^{M}.
$$

The ensemble mean is

$$
\bar{\mathbf{n}}(t) = \frac{1}{M}\sum_{m=1}^{M}\mathbf{n}^{(m)}(t),
$$

and the empirical spread is summarized by quantiles such as the 10th and 90th
percentiles:

$$
n_{0.1}(h,t), \qquad n_{0.9}(h,t).
$$

Those quantiles define the uncertainty bands in the forecast figures.

## Exceedance probability and tail risk

For a threshold \(n_*\) at altitude \(h\) and final time \(T\), the empirical
exceedance probability is

$$
\widehat{P}\!\left[n(h,T) > n_*\right]
= \frac{1}{M}\sum_{m=1}^{M}
\mathbf{1}\!\left(n^{(m)}(h,T) > n_*\right).
$$

The corresponding tail probability at a fixed altitude \(h_0\) is

$$
\widehat{P}\!\left[n(h_0,T) > n_*\right].
$$

An exceedance map is simply the same probability evaluated over a grid of
\((h,n_*)\) values. It answers:

- at this altitude, how likely is the density to exceed a given threshold?
- where in the profile does the rare-event risk concentrate?

That is why Figure 4 is organized as a map plus a 1D tail curve.

## Lyapunov exponent and predictability horizon

To estimate sensitivity to initial conditions, the code measures pairwise
separation in the ensemble at a selected altitude index \(j\):

$$
\delta(t_k)
= \frac{2}{M(M-1)}\sum_{m<\ell}
\left|n^{(m)}(h_j,t_k) - n^{(\ell)}(h_j,t_k)\right|.
$$

If the separation grows approximately exponentially, then

$$
\log \delta(t) \approx \lambda t + c.
$$

The fitted slope \(\lambda\) is the estimated Lyapunov exponent.

The corresponding predictability horizon is

$$
t_\ast
= \frac{1}{\lambda}\log\!\left(\frac{\Delta_{\max}}{\Delta_0}\right),
$$

where \(\Delta_0\) is an initial uncertainty scale and \(\Delta_{\max}\) is the
size of the tolerated forecast error.

These quantities are used in the claim version of Figure 2.

## Transfer operator and DMD

The transfer-operator view treats the evolution of a probability density
\(\rho\) over states rather than a single trajectory:

$$
\rho_{t+\Delta t} = \mathcal{P}^{\Delta t}\rho_t.
$$

Observable functions \(g\) evolve under the Koopman operator:

$$
g_{t+\Delta t} = \mathcal{K}^{\Delta t}g_t.
$$

Dynamic Mode Decomposition approximates these operators from snapshot data. If

$$
X = \begin{bmatrix} x_1 & x_2 & \cdots & x_{m-1} \end{bmatrix}, \qquad
X' = \begin{bmatrix} x_2 & x_3 & \cdots & x_m \end{bmatrix},
$$

then the reduced operator is

$$
\tilde{A} = U_r^\ast X' V_r \Sigma_r^{-1},
$$

where \(X = U\Sigma V^\ast\) is the truncated singular-value decomposition.
The DMD eigenvalues satisfy

$$
\tilde{A} w = \lambda w.
$$

The corresponding DMD modes are

$$
\Phi = X' V_r \Sigma_r^{-1} W.
$$

These are the equations behind Figure 3.

## Figure mapping

- Figure 1 is a conceptual schematic of the forcing-flow-observable pipeline
- Figure 2 compares deterministic and stochastic solutions
- Figure 3 shows low-rank transfer-operator structure
- Figure 4 shows exceedance probabilities and tail statistics
- Figure 5 shows Chapman photoionization and the equilibrium response
- Figure 6 shows the precipitation proxy and the equilibrium response

The forecast example in [Example Forecast](example_forecast.md) uses the same
model equations, but it presents the uncertainty growth directly at 90 km
altitude.
