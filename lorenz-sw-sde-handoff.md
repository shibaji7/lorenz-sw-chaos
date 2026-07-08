# Handoff Spec: Chaotic/Stochastic Ionospheric Continuity-Equation Codebase

**Target agent:** Codex
**Originating idea:** Cowork session, "Perspective - SDE - Chaotic Models" project — companion codebase for the AGU Perspectives paper *"A Lorenz Moment for Space Weather"* (draft: `Draft/Chaotic_Model_Perspective.tex`, not included in this repo; all needed equations are reproduced self-contained below).
**Status:** approximation pending validation — this is a new, from-scratch repository. Nothing here has been run or numerically validated yet; treat all default parameter values as placeholders pending the author's review.

---

## 1. Objective

Create a new, self-contained Python repository that implements a deterministic ionospheric plasma-density continuity-equation solver, then extends it with a stochastic differential equation (SDE) formulation that treats photoionization and particle-precipitation forcing as chaotic/self-organized-critical processes rather than smooth deterministic inputs. The repository must produce runnable ensemble simulations, estimate a Lyapunov exponent and predictability horizon from those ensembles, approximate the long-term transfer operator via Dynamic Mode Decomposition (DMD), and generate the four illustrative figures needed for the paper (an SDE-ensemble-vs-deterministic plot and a transfer-operator/DMD plot are the priority two; a system schematic and an exceedance-probability plot are secondary). The codebase must be testable (pytest), documented (math description + usage doc), and set up as a GitHub repository with CI running the test suite on every push.

This closes the gap between the paper's mathematical framework (currently equations on paper only) and a working, inspectable numerical implementation the author can run, extend, and generate figures from.

---

## 2. Background / context

### 2.1 Scientific framing (for context only — do not re-derive)
The paper argues that model–data mismatch in physics-based space weather models is often the expected signature of deterministic chaos rather than missing physics. It illustrates this with a single system: the ionospheric plasma-density continuity equation, in which both production terms (photoionization, particle precipitation) carry independently documented chaotic/self-organized-critical (SOC) statistics. The codebase should treat this continuity equation as the one physical system to implement — do not add other illustrative systems (e.g., no submarine cable / geoelectric field model; that was deliberately removed from the paper's scope).

### 2.2 Repository scaffold
Create a new directory and initialize it as follows. Repo name and GitHub org are placeholders — see §10 "Open questions" before pushing a remote.

```
lorenz-sw-chaos/                      # repo root — placeholder name, confirm before remote push
├── README.md
├── environment.yml
├── pyproject.toml
├── .gitignore
├── src/
│   └── lorenzsw/
│       ├── __init__.py
│       ├── chapman.py                # Eq. 2 — photoionization production
│       ├── precipitation.py          # Eq. NEW-A — precipitation production (+ swappable interface)
│       ├── continuity.py             # Eq. 1 (drift only) — deterministic RHS, loss terms
│       ├── sde.py                    # Eq. 3, 4 — diffusion term + Euler–Maruyama integrator
│       ├── forcing/
│       │   ├── __init__.py
│       │   ├── soc_flare.py          # synthetic P0(t): SOC/power-law flare pulse train
│       │   ├── lorenz_precip.py      # synthetic Q0(t): Lorenz-63-driven precipitation proxy
│       │   └── omni_loader.py        # OPTIONAL real-data loader (SYM-H/AE), network-optional
│       ├── ensemble.py               # N-member ensemble propagation + Siegert et al. calibration
│       ├── lyapunov.py               # Eq. 5, 6 — Lyapunov exponent + predictability horizon
│       ├── transfer_operator.py      # Eq. 7, 8 — DMD approximation of transfer operator
│       └── figures/
│           ├── __init__.py
│           ├── fig1_swmi_schematic.py
│           ├── fig2_sde_ensemble.py
│           ├── fig3_transfer_operator.py
│           └── fig4_exceedance.py
├── scripts/
│   └── generate_all_figures.py       # runs fig1-4 scripts, saves to figures/output/
├── tests/
│   ├── test_chapman.py
│   ├── test_precipitation.py
│   ├── test_continuity.py
│   ├── test_sde.py
│   ├── test_forcing.py
│   ├── test_ensemble.py
│   ├── test_lyapunov.py
│   └── test_transfer_operator.py
├── docs/
│   ├── math_description.md           # equations 1-8 + NEW-A, mirrors §6 below, with citations
│   └── usage.md                      # how to run sims, generate figures, run tests
└── .github/
    └── workflows/
        └── ci.yml                    # pytest on push/PR to main
```

### 2.3 Environment setup (exact commands Codex should run)

```bash
conda create -n lorenzsw python=3.11 -y
conda activate lorenzsw
conda install -n lorenzsw -c conda-forge numpy scipy matplotlib pandas pytest -y
pip install pydmd nolds requests
```

`environment.yml` (create this file verbatim, then prefer `conda env create -f environment.yml` for reproducibility over the manual commands above):

```yaml
name: lorenzsw
channels:
  - conda-forge
dependencies:
  - python=3.11
  - numpy
  - scipy
  - matplotlib
  - pandas
  - pytest
  - pip
  - pip:
      - pydmd
      - nolds
      - requests
```

Note on dependency choice: the paper text mentions `sdeint` as an example available library, but this repo should hand-roll the Euler–Maruyama integrator directly per Eq. 4 (see `sde.py`) rather than depend on `sdeint`, because the state here is a vector over an altitude grid with altitude- and time-dependent drift/diffusion, which is simpler to keep transparent and testable as a small custom function than to fit into a generic SDE-library API. Do not add `sdeint` as a dependency unless a specific need arises.

---

## 3. Inputs

| Name | Type/shape | Units | Source |
|---|---|---|---|
| `h_km` | `np.ndarray`, shape `(Nh,)` | km | caller-provided altitude grid, e.g. `np.arange(60, 96, 1.0)` for D-region |
| `t_grid_s` | `np.ndarray`, shape `(Nt,)` | s (seconds since simulation start) | caller-provided, e.g. `np.arange(0, 6*3600, 10.0)` for a 6-hour run at 10 s steps |
| `n0` | `np.ndarray`, shape `(Nh,)` | cm⁻³ | initial plasma density profile, caller-provided or generated via a quiet-time deterministic run |
| `P0_t` | `Callable[[float], float]` | cm⁻³ s⁻¹ (peak production rate at zenith) | from `forcing.soc_flare` or `forcing.omni_loader` |
| `Q0_t` | `Callable[[float], float]` | eV cm⁻² s⁻¹ (precipitating energy flux) | from `forcing.lorenz_precip` or `forcing.omni_loader` |
| `chi_rad` | `float` or `Callable[[float], float]` | radians | solar zenith angle, caller-provided (can be constant for a first pass) |
| `h_m_km`, `H_km` | `float` | km | Chapman layer peak altitude and neutral scale height, caller-provided (D-region defaults: `h_m_km≈90`, `H_km≈6`; flag as placeholder, see §10) |
| `h_p_km`, `H_p_km` | `float` | km | precipitation layer peak altitude and width, caller-provided (defaults `h_p_km≈90`, `H_p_km≈8`; placeholder, see §10) |
| `alpha_cm3s`, `beta_s` | `float` | cm³ s⁻¹, s⁻¹ | quadratic recombination and linear attachment loss coefficients, caller-provided (placeholders, see §10) |
| `sigma0`, `beta_g`, `P_max` | `float` | matches `g(n,t)` units (see §6) | diffusion-term parameters, caller-provided |
| `n_members` | `int` | — | ensemble size, default 500 per paper |
| `seed` | `int` | — | RNG seed for reproducibility |

---

## 4. Outputs

| Name | Type/shape | Units | Notes |
|---|---|---|---|
| `ensemble` | `np.ndarray`, shape `(n_members, Nt, Nh)` | cm⁻³ | full ensemble of density trajectories |
| `n_deterministic` | `np.ndarray`, shape `(Nt, Nh)` | cm⁻³ | single noise-free run for comparison |
| `lambda_hat` | `float` | s⁻¹ | estimated Lyapunov exponent |
| `t_star_s` | `float` | s | predictability horizon |
| `dmd_eigenvalues` | `np.ndarray` (complex), shape `(r,)` | dimensionless | DMD spectrum |
| `dmd_modes` | `np.ndarray` (complex), shape `(n_features, r)` | — | DMD spatial modes |
| figure PNGs | files under `figures/output/` | — | `fig1_swmi_schematic.png`, `fig2_sde_ensemble.png`, `fig3_transfer_operator.png`, `fig4_exceedance.png` |

---

## 5. Function / module signatures

Illustrative only — Codex implements the bodies. Keep names, argument order, units, and shapes as specified; if a change is genuinely needed, flag it rather than silently diverging.

```python
# chapman.py
def chapman_production(h_km: np.ndarray, t_s: float, P0_t: Callable[[float], float],
                        h_m_km: float, H_km: float, chi_rad: float) -> np.ndarray:
    """Eq. 2 — Chapman photoionization production rate P_solar(h,t).
    Returns production rate [cm^-3 s^-1], shape (Nh,).
    """

# precipitation.py
class PrecipitationModel(Protocol):
    def __call__(self, h_km: np.ndarray, t_s: float) -> np.ndarray:
        """Returns production rate [cm^-3 s^-1], shape (Nh,)."""

def gaussian_precipitation(h_km: np.ndarray, t_s: float, Q0_t: Callable[[float], float],
                            h_p_km: float, H_p_km: float,
                            delta_eps_ion_eV: float = 35.0) -> np.ndarray:
    """Eq. NEW-A — Gaussian-layer precipitation production P_precip(h,t).
    Implements the PrecipitationModel protocol.
    """

# continuity.py
def continuity_drift(n: np.ndarray, P_solar: np.ndarray, P_precip: np.ndarray,
                      alpha_cm3s: float, beta_s: float) -> np.ndarray:
    """Deterministic drift f(n,t) = P_solar + P_precip - alpha*n^2 - beta*n.
    Returns [cm^-3 s^-1], shape (Nh,).
    """

# sde.py
def diffusion_term(n: np.ndarray, P_precip: np.ndarray, P_max: float,
                    sigma0: float, beta_g: float) -> np.ndarray:
    """Eq. 3 — g(n,t). Returns shape (Nh,), units such that g*dW has units of n (cm^-3)."""

def euler_maruyama_step(n: np.ndarray, drift: np.ndarray, diffusion: np.ndarray,
                         dt_s: float, rng: np.random.Generator) -> np.ndarray:
    """Eq. 4 — one EM step. Returns n_{k+1}, shape (Nh,). Must not silently allow n<0
    (see acceptance criteria and open question in Sec. 10 on positivity)."""

# ensemble.py
def run_ensemble(n0: np.ndarray, t_grid_s: np.ndarray, h_km: np.ndarray,
                  P0_t: Callable[[float], float], Q0_t: Callable[[float], float],
                  precip_model: PrecipitationModel,
                  h_m_km: float, H_km: float, chi_rad: float,
                  alpha_cm3s: float, beta_s: float,
                  sigma0: float, beta_g: float, P_max: float,
                  n_members: int = 500, seed: int = 0) -> np.ndarray:
    """Returns ensemble, shape (n_members, Nt, Nh)."""

def run_deterministic(n0: np.ndarray, t_grid_s: np.ndarray, h_km: np.ndarray,
                       P0_t: Callable, Q0_t: Callable, precip_model: PrecipitationModel,
                       h_m_km: float, H_km: float, chi_rad: float,
                       alpha_cm3s: float, beta_s: float) -> np.ndarray:
    """Single noise-free run (sigma0=0 equivalent), shape (Nt, Nh)."""

def calibrate_drift_diffusion(n_hist: np.ndarray, dt_s: float,
                               n_bins: int = 30) -> tuple[Callable[[float], float], Callable[[float], float]]:
    """Siegert et al. (1998)-style calibration of f_hat(n), g_hat(n) from a 1D historical or
    synthetic density time series n_hist, shape (Nt,). Returns (f_hat, g_hat)."""

# forcing/soc_flare.py
def soc_flare_forcing(t_grid_s: np.ndarray, rate_per_day: float, alpha_powerlaw: float,
                       P0_background: float, P0_peak_scale: float,
                       seed: int = 0) -> np.ndarray:
    """Synthetic P0(t): background level plus a power-law-distributed pulse train
    (occurrence times ~ Poisson process, pulse sizes ~ power law with exponent
    alpha_powerlaw, exponential pulse decay). Returns [cm^-3 s^-1], shape (Nt,)."""

# forcing/lorenz_precip.py
def lorenz63_precip_forcing(t_grid_s: np.ndarray, sigma: float = 10.0, rho: float = 28.0,
                             beta: float = 8/3, Q_mean_eV: float = 1.0e3,
                             kappa: float = 0.5, seed: int = 0) -> np.ndarray:
    """Synthetic Q0(t): integrates the Lorenz-63 system and rescales its x-component to a
    non-negative energy flux via Q0(t) = max(0, Q_mean*(1 + kappa*x(t)/x_std)).
    Returns [eV cm^-2 s^-1], shape (Nt,)."""

# forcing/omni_loader.py  (OPTIONAL, network-dependent)
def load_omni_index(start_iso: str, end_iso: str, index: str = "SYM_H",
                     cache_dir: Optional[str] = None) -> "pd.DataFrame":
    """Fetches OMNI low-res index data via omniweb ASCII interface. Must degrade gracefully
    (raise a clearly-named exception, e.g. OmniUnavailableError) if network access is not
    available in the execution environment; tests exercising this must be skippable."""

# lyapunov.py
def estimate_lyapunov(ensemble: np.ndarray, t_grid_s: np.ndarray,
                       h_index: int = 0) -> tuple[float, np.ndarray]:
    """Eq. 5 — estimate lambda [s^-1] from ensemble pairwise divergence at altitude index
    h_index. Returns (lambda_hat, mean_log_divergence_curve[shape (Nt,)])."""

def predictability_horizon(lambda_s_inv: float, delta_max: float, delta_x0: float) -> float:
    """Eq. 6 — t* [s]. Must raise ValueError if lambda_s_inv <= 0."""

# transfer_operator.py
def dmd_transfer_operator(snapshots: np.ndarray, r: Optional[int] = None
                           ) -> tuple[np.ndarray, np.ndarray]:
    """Eq. 7-8 — DMD approximation. snapshots shape (n_features, n_time), built by flattening
    ensemble members and/or altitude levels into n_features. Returns (eigenvalues (r,),
    modes (n_features, r))."""
```

---

## 6. Algorithm / math description

All equations below are reproduced from the paper draft (equation numbers `sde_continuity`, `chapman`, `diffusion`, `euler_maruyama`, `lyapunov`, `tstar`, `transfer_op`, `dmd`), plus one new equation (`NEW-A`) agreed in this handoff for the precipitation term, which does not yet appear in the paper draft.

**Eq. 1 (SDE, continuity equation).**
`dn = [P_solar(h,t) + P_precip(h,t) - alpha*n^2 - beta*n] dt + g(n,t) dW_t`
State variable `n` = plasma density at altitude `h`. Implemented as drift (`continuity.py`) + diffusion (`sde.py`) + EM integration (`sde.py`).

**Eq. 2 (Chapman photoionization).**
`P_solar(h,t) = P0(t) * exp(1 - (h-h_m)/H - sec(chi) * exp(-(h-h_m)/H))`
`P0(t)` is the time-varying peak production rate driven by solar EUV/X-ray flux; its chaotic/SOC character comes from flare-occurrence statistics (Lu & Hamilton 1991). Implemented in `chapman.py`.

**Eq. NEW-A (Gaussian precipitation production — new, agreed this session).**
`P_precip(h,t) = Q0(t) / (delta_eps_ion * sqrt(2*pi) * H_p) * exp(-(h - h_p)^2 / (2*H_p^2))`
`Q0(t)` is the time-varying precipitating energy flux; its chaotic character comes from wave-particle resonance-overlap dynamics (Ukhorskiy & Sitnov 2013). `delta_eps_ion ≈ 35 eV` is the mean energy per ion pair (standard value, Rees 1989). This is a simplified stand-in for the more rigorous Fang et al. (2010) semi-empirical parameterization; implement behind the `PrecipitationModel` protocol so a `FangPrecipitationModel` can be added later without touching calling code. Implemented in `precipitation.py`.

**Eq. 3 (storm-phase diffusion).**
`g(n,t) = sigma0 * (1 + beta_g * P_precip/P_max) * sqrt(n)`
Diffusion amplitude scales with both the local precipitation forcing level and `sqrt(n)` (multiplicative-noise convention, consistent with counting-statistics-like fluctuations in density). Implemented in `sde.py`.

**Eq. 4 (Euler–Maruyama).**
`n_{k+1} = n_k + f(n_k,t_k)*dt + g(n_k,t_k)*dW_k`, `dW_k ~ N(0, dt)`, drawn independently each step (Higham 2001). Implemented in `sde.py`.

**Eq. 5 (Lyapunov exponent).**
`lambda = lim_{t->inf} (1/t) * ln(||delta_n(t)|| / ||delta_n_0||)`
Estimate via ensemble divergence: seed pairs of realizations with a small perturbation `delta_n_0` in initial density, track `||delta_n(t)||` across the ensemble, fit the log-linear slope. Implemented in `lyapunov.py`.

**Eq. 6 (predictability horizon).**
`t* = (1/lambda) * ln(delta_max / ||delta_x_0||)`
Implemented in `lyapunov.py`.

**Eq. 7 (Perron–Frobenius transfer operator).**
`P(n, t+tau) = L_tau * P(n,t)` — linear evolution of the probability density even though the underlying dynamics are nonlinear. Not solved in closed form; approximated numerically via DMD (Eq. 8).

**Eq. 8 (DMD approximation).**
`A = X' * X^dagger`, `A*Phi = Phi*Lambda`
`X`, `X'` are data matrices of consecutive ensemble snapshots (`X'` is `X` shifted one time step). `X^dagger` is the Moore–Penrose pseudoinverse. Use `pydmd` or a direct SVD-based implementation; either is acceptable, but the eigenvalue-classification logic (decay/persistent/growth, see Fig. 3 below) must be explicit application code, not hidden inside a third-party call. Implemented in `transfer_operator.py`.

### 6.1 Synthetic forcing generators (both required per this handoff)

**SOC flare generator (`soc_flare_forcing`).** Simplified stand-in for a full Lu & Hamilton (1991) cellular-automaton avalanche model: generate flare occurrence times as a Poisson process at `rate_per_day`, draw pulse sizes from a power-law distribution with exponent `alpha_powerlaw`, and construct `P0(t)` as a background level plus a superposition of exponentially-decaying pulses at those occurrence times. This is a deliberate simplification (documented in §10) — the full 2D avalanche automaton is out of scope for this handoff but may be added later as `forcing/soc_flare_ca.py` behind the same interface (a plain `Callable[[float], float]` or precomputed array, so swapping generators requires no changes to `chapman.py` or `ensemble.py`).

**Lorenz-63 precipitation generator (`lorenz63_precip_forcing`).** Integrate the standard Lorenz-63 system (`sigma=10, rho=28, beta=8/3` defaults, chaotic regime) via `scipy.integrate.solve_ivp`, then map the `x` component to a non-negative energy flux via `Q0(t) = max(0, Q_mean*(1 + kappa*x(t)/std(x)))`. This is the same physical intuition described in the paper (precipitation forcing inheriting chaotic dynamics from resonance-overlap processes), realized here as a self-contained proxy generator rather than a first-principles particle-transport model — document this as a proxy, not a validated precipitation model.

### 6.2 Real-data path (optional module, per this handoff's answer)

`forcing/omni_loader.py` should provide a best-effort loader for OMNI SYM-H/AE index data (for later calibration of `calibrate_drift_diffusion` against real storms, per Siegert et al. 1998). This module and its tests must not block the rest of the test suite if network access is unavailable in Codex's execution sandbox — wrap network calls so failures raise a distinct, catchable exception and mark its tests with `pytest.mark.skipif` on a connectivity check.

---

## 7. What NOT to change

- Do not introduce SCUBAS, RAID, or any submarine-cable/geoelectric-field model into this repository — the paper deliberately scoped down to the single continuity-equation illustration; this codebase should match that scope.
- Do not replace the hand-rolled Euler–Maruyama integrator (`sde.py`) with a third-party SDE library without flagging it first — see the dependency note in §2.3.
- Do not change the physical form of Eq. 1–8 as written above without flagging the change back to the user; if a numerical necessity requires a modification (e.g., a stability fix), document it explicitly in `docs/math_description.md` as a deviation, not silently.
- Do not commit real OMNI data files to the repository; `omni_loader.py` should fetch-and-cache to a gitignored local directory only.

---

## 8. Acceptance criteria

- `chapman_production(h=h_m_km, t, P0_t, ...)` with `chi_rad=0` returns `P0_t(t)` (the Chapman function evaluates to 1 at its own peak under vertical incidence) — exact match within floating-point tolerance.
- `gaussian_precipitation` peaks at `h=h_p_km`; numerically integrating the returned profile over `h_km` and multiplying by `delta_eps_ion_eV` approximately recovers `Q0_t(t)` (within ~5% for a sufficiently fine/wide altitude grid) — this is an energy-conservation sanity check.
- With `sigma0=0`, `run_ensemble(...)` collapses (all members identical) and exactly matches `run_deterministic(...)` within numerical tolerance — this is the critical "reduces to the deterministic case" check requested for any stochastic extension.
- `continuity_drift` with `P_solar=P_precip=0` and `beta_s=0` reduces to `-alpha*n^2`; verify against the closed-form solution `n(t) = n0 / (1 + alpha*n0*t)` for a single-altitude test case, matching within integration tolerance.
- `run_ensemble` output must remain non-negative; if the plain Euler–Maruyama scheme with `sqrt(n)` diffusion produces negative values in testing, do not silently clip — flag this back per §10 and propose either a reflecting boundary or a log-density transform, then implement whichever the user selects.
- `soc_flare_forcing`: the empirical complementary CDF of generated pulse sizes should follow a power law with fitted exponent within ~15% of the input `alpha_powerlaw` (regression test over a long synthetic run, e.g. 5000+ pulses).
- `lorenz63_precip_forcing`: output must be non-negative everywhere (post-clipping) and should visibly exhibit aperiodic, bounded fluctuation (sanity check: no NaNs/Infs, values bounded within a documented multiple of `Q_mean_eV`).
- `estimate_lyapunov` run on the full synthetic ensemble (both chaotic forcings enabled) must return `lambda_hat > 0`. No claim is made that it must match a specific real-world value — this is a synthetic-system sanity check, not a validation against observations.
- `predictability_horizon` raises `ValueError` for `lambda_s_inv <= 0`.
- `dmd_transfer_operator` returns eigenvalues and modes with consistent shapes (`eigenvalues.shape == (r,)`, `modes.shape == (n_features, r)`); include a test that a purely decaying synthetic input (e.g., exponential relaxation toward equilibrium, no forcing) yields eigenvalues with `|Lambda| < 1`.
- `scripts/generate_all_figures.py` runs end-to-end without error on a fresh environment and produces four non-empty PNG files under `figures/output/`.
- All tests pass under `pytest` in the `lorenzsw` conda environment, and the GitHub Actions CI workflow reproduces this (see §10 for remote/CI setup confirmation needed).

---

## 9. Source material

- Lorenz, E. N. (1963), *Deterministic Nonperiodic Flow*, J. Atmos. Sci., 20, 130–141, doi:10.1175/1520-0469(1963)020<0130:DNF>2.0.CO;2 — foundational chaos/predictability-horizon framing (Eq. 5–6 motivation).
- Vassiliadis, D. et al. (1990); Baker, D. N. et al. (1990), *Geophys. Res. Lett.*, 17 — empirical low-dimensional chaos in AE/Dst, general motivation, not directly coded.
- Chapman, S. C. et al. (1998); Consolini, G. (1997); Bak, P. et al. (1987) — SOC/power-law substorm statistics, motivates `soc_flare_forcing`.
- Lu, E. T. & Hamilton, R. J. (1991), *Avalanches and the distribution of solar flares*, ApJ, 380, L89–L92, doi:10.1086/186180 — physical justification for treating `P0(t)` as power-law/SOC; basis (simplified) for `soc_flare_forcing`.
- Ukhorskiy, A. Y. & Sitnov, M. I. (2013), *Dynamics of Radiation Belt Particles*, Space Sci. Rev., 179, 545–578, doi:10.1007/s11214-012-9938-5 — Chirikov resonance-overlap justification for treating precipitation forcing as chaotic; motivates `lorenz63_precip_forcing` as a proxy (not a first-principles implementation of this paper's physics).
- Rees, M. H. (1989), *Physics and Chemistry of the Upper Atmosphere*, Cambridge Univ. Press — source of the `delta_eps_ion ≈ 35 eV` constant and the general basis for Gaussian-shaped precipitation ionization layers.
- Fang, X. et al. (2010), *Parameterization of monoenergetic electron impact ionization*, Geophys. Res. Lett., 37, L22106, doi:10.1029/2010GL045406 — the more rigorous precipitation-ionization parameterization that `PrecipitationModel` should be able to accommodate later (not implemented in this handoff).
- Siegert, S., Friedrich, R., & Peinke, J. (1998), *Analysis of data sets of stochastic systems*, Phys. Lett. A, 243, 275–280, doi:10.1016/S0375-9601(98)00283-7 — basis for `calibrate_drift_diffusion`.
- Higham, D. J. (2001), *An algorithmic introduction to numerical simulation of stochastic differential equations*, SIAM Rev., 43, 525–546, doi:10.1137/S0036144500378302 — Euler–Maruyama scheme (Eq. 4).
- Øksendal, B. (2003), *Stochastic Differential Equations*, 6th ed., Springer — general SDE formalism background.
- Paper draft equations 1–8 (this session's Cowork conversation; reproduced self-contained in §6 above — the coding agent does not need the `.tex` file itself).

---

## 10. Open questions / known approximations

Flag all of these back to the user (Shibaji) rather than resolving silently:

1. **Repository name and GitHub destination.** This handoff uses the placeholder `lorenz-sw-chaos` under a placeholder account/org. Confirm the exact repo name, visibility (public/private), and target GitHub account/org before running `gh repo create` or `git push` to a remote. If the `gh` CLI is not authenticated in the execution environment, stop after the local `git init` + first commit and report that the remote step needs to be completed manually or with credentials supplied.
2. **Physical unit/parameter defaults are placeholders.** `alpha_cm3s`, `beta_s`, `h_m_km`, `H_km`, `h_p_km`, `H_p_km`, `sigma0`, `beta_g`, and the density unit convention (`cm^-3` chosen here as the ionospheric-physics convention) have not been confirmed against any specific reference profile or event by the author. Implement them as named, clearly-documented default parameters (not hard-coded magic numbers), and flag in `docs/math_description.md` that these need literature- or data-based tuning before any run is treated as physically realistic.
3. **`h_p(t)` vs. characteristic precipitation energy.** The Gaussian precipitation model currently treats `h_p_km` as a constant (or a simple, undocumented function of a characteristic energy `E0(t)`, if implemented). The physically correct altitude-energy relationship (as in Fang et al. 2010's range-energy formulation) is not implemented here — flag this as a known simplification.
4. **Positivity of `n` under the Euler–Maruyama scheme.** The `sqrt(n)` diffusion term does not guarantee non-negative density under plain EM stepping. Do not silently clip negative values to zero without flagging — implement a documented handling strategy (reflecting boundary or log-density transform are the two standard options) and ask the user which they prefer if both are viable.
5. **`soc_flare_forcing` is a simplified proxy**, not the full Lu & Hamilton (1991) 2D cellular-automaton avalanche model. It reproduces the power-law occurrence statistic but not the full spatial avalanche dynamics. Flag this as an intentional scope reduction for this handoff, with the CA version noted as a possible future addition.
6. **`lorenz63_precip_forcing` is a thematic/illustrative proxy**, not a first-principles model of resonance-overlap-driven precipitation. This mirrors language originally considered for the paper itself and is a deliberate modeling choice for generating illustrative chaotic figures, not a claim of physical derivation from Ukhorskiy & Sitnov (2013).
7. **OMNI real-data loader is best-effort and may not be exercised** if Codex's execution environment lacks network access. Confirm whether Codex's sandbox has outbound internet access before relying on this path for anything beyond a stub + skip-marked test.
8. **Fig. 1 (SW-M-I schematic)** is largely illustrative/non-data-driven (an annotated diagram, not a simulation output) — lowest implementation priority of the four figures. Confirm whether the author wants this generated programmatically (e.g., matplotlib shapes/annotations) or left as a placeholder for manual diagram creation (e.g., in the earlier LaTeX/figure-caption work already done for the paper).

---

**Target-agent note:** this spec is written for **Codex**. Keep PRs/commits scoped per module (e.g., one commit for `chapman.py` + `test_chapman.py`, not one giant commit for the whole repo) so the author can review incrementally. Do not mark any task "done" if tests are failing or if any of the eight open questions above were resolved by guessing rather than by asking.
