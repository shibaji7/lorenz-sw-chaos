"""Diagnostic: renormalized (Benettin/Wolf-style) twin-experiment Lyapunov rate.

The naive twin experiment (estimate_lyapunov_paired) tracks one fixed initial
perturbation over the whole 24-hour window and fits a single slope. At this
model's parameters the per-altitude contraction is so strong (~285x per 60s
step near quasi-equilibrium) that the separation underflows to floating-point
noise within about 5 minutes -- long before the first SOC pulse arrives at
~4.7h. The fitted slope from that experiment is therefore dominated by ~350
flat noise-floor points, not a resolved rate, and cannot show whether the
system is transiently *less* contracting (or briefly expanding) during a
forcing pulse.

This script instead renormalizes every step (Benettin 1980 / Wolf et al.
1985): after each step, rescale the perturbed trajectory back to the
original small separation and record the log of that step's growth factor.
This is well-defined regardless of how fast the true contraction is, and
gives a *time-resolved local rate* rather than one number -- so pulse-timing
correlations are directly visible.

Usage:
    python scripts/diagnose_lyapunov_separation.py [output.png]
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lorenzsw.lyapunov import estimate_lyapunov_renormalized
from lorenzsw.model_params import load_model_params
from lorenzsw.plotting import format_axes, set_publication_style
from lorenzsw.scenarios import build_chaotic_forcing


def main(output_path: Path) -> None:
    set_publication_style("nature")
    params = load_model_params()

    # Lightweight: forcing callables + initial profile only, no ensemble run.
    scenario = build_chaotic_forcing(params)
    h_km, t_grid_s, n0 = scenario.h_km, scenario.t_grid_s, scenario.n0
    alt_index = int(np.argmin(np.abs(h_km - params["time_panel_altitude_km"])))
    dt_s = float(t_grid_s[1] - t_grid_s[0])

    lam_s_inv, times_renorm_s, log_growth = estimate_lyapunov_renormalized(
        n0=n0, t_grid_s=t_grid_s, h_km=h_km,
        P0_t=scenario.P0_t, Q0_t=scenario.Q0_t, precip_model=scenario.precip_model,
        h_m_km=params["h_m_km"], H_km=params["H_km"], chi_rad=0.0,
        alpha_cm3s=params["alpha_cm3s"], beta_s=params["beta_s"],
        h_index=alt_index, renorm_every=1,
    )
    print(f"Renormalized lambda_IC (time-averaged over {log_growth.size} steps): "
          f"{lam_s_inv:.4e} s^-1")
    print(f"Local rate range: [{(log_growth.min()/dt_s):.3e}, "
          f"{(log_growth.max()/dt_s):.3e}] s^-1")

    times_hr = t_grid_s / 3600.0
    times_renorm_hr = times_renorm_s / 3600.0
    P0_series = np.array([scenario.P0_t(t) for t in t_grid_s])
    local_rate_s_inv = log_growth / dt_s  # per-step log-growth converted to a rate

    fig, axes = plt.subplots(2, 1, figsize=(7.5, 6.0), sharex=True)

    ax = axes[0]
    ax.plot(times_hr, P0_series, color="tab:orange", linewidth=1.6)
    ax.set_ylabel(r"$P_0(t)$ [cm$^{-3}$ s$^{-1}$]")
    ax.set_title("SOC photoionization forcing (pulse timing reference)")
    format_axes(ax)

    ax = axes[1]
    ax.plot(times_renorm_hr, local_rate_s_inv, color="tab:green", linewidth=1.0)
    ax.axhline(lam_s_inv, color="0.3", linewidth=1.2, linestyle="--",
               label=rf"time-averaged $\lambda_{{IC}}$ = {lam_s_inv:.2e} s$^{{-1}}$")
    ax.axhline(0.0, color="0.7", linewidth=0.8, linestyle=":")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel(r"local rate [s$^{-1}$]")
    ax.set_title("Renormalized local contraction/expansion rate (per step)")
    ax.legend(frameon=False, fontsize=8)
    format_axes(ax)

    fig.suptitle("Renormalized twin-experiment: does the local rate change during SOC pulses?", y=1.0)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("figures/lyapunov_separation.png")
    main(out)
