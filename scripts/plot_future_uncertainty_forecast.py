"""Plot diverging uncertainty in future electron density prediction."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from loguru import logger

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("/tmp") / "xdg-cache"))

Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lorenzsw._logging import configure_logging
from lorenzsw.ensemble import run_deterministic, run_ensemble
from lorenzsw.model_params import load_model_params
from lorenzsw.precipitation import gaussian_precipitation
from lorenzsw.plotting import format_axes, set_publication_style

set_publication_style("nature")


def _safe_positive(values: np.ndarray, floor: float = 1.0e-6) -> np.ndarray:
    values = np.nan_to_num(values, nan=floor, posinf=floor, neginf=floor)
    return np.clip(values, floor, None)


def _smooth_series(values: np.ndarray, window: int = 5) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if window <= 1 or values.size < window:
        return values
    kernel = np.ones(window, dtype=float) / window
    pad = window // 2
    padded = np.pad(values, pad_width=pad, mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating future uncertainty forecast at {}", output_path)
    if params is None:
        params = load_model_params()

    h_km = np.linspace(
        params["forecast_h_km_min"],
        params["forecast_h_km_max"],
        int(params["forecast_h_km_points"]),
    )
    t_grid_s = np.arange(0.0, params["forecast_t_end_s"] + params["forecast_t_step_s"], params["forecast_t_step_s"])
    n0 = np.full_like(h_km, params["forecast_n0_cm3"], dtype=float)

    P0_t = lambda t: params["forecast_P0_amp"] * (
        1.0 + params["P0_modulation"] * np.sin(2.0 * np.pi * t / params["P0_period_s"])
    )
    Q0_t = lambda t: params["forecast_Q0_amp"] * (
        1.0 + params["Q0_modulation"] * np.cos(2.0 * np.pi * t / params["Q0_period_s"])
    )
    precip_model = lambda h, t: gaussian_precipitation(
        h,
        t,
        Q0_t=Q0_t,
        h_p_km=lambda tau: params["h_m_km"] + params["precip_peak_offset_km"] * np.sin(2.0 * np.pi * tau / params["Q0_period_s"]),
        H_p_km=params["precip_H_p_km"],
    )

    deterministic = run_deterministic(
        n0=n0,
        t_grid_s=t_grid_s,
        h_km=h_km,
        P0_t=P0_t,
        Q0_t=Q0_t,
        precip_model=precip_model,
        h_m_km=params["h_m_km"],
        H_km=params["H_km"],
        chi_rad=0.0,
        alpha_cm3s=params["alpha_cm3s"],
        beta_s=params["beta_s"],
    )
    ensemble = run_ensemble(
        n0=n0,
        t_grid_s=t_grid_s,
        h_km=h_km,
        P0_t=P0_t,
        Q0_t=Q0_t,
        precip_model=precip_model,
        h_m_km=params["h_m_km"],
        H_km=params["H_km"],
        chi_rad=0.0,
        alpha_cm3s=params["alpha_cm3s"],
        beta_s=params["beta_s"],
        sigma0=params["forecast_sigma0"],
        beta_g=params["forecast_beta_g"],
        P_max=params["forecast_P_max"],
        n_members=int(params["forecast_n_members"]),
        seed=int(params["forecast_seed"]),
    )

    mean = _safe_positive(ensemble.mean(axis=0))
    lo = _safe_positive(np.percentile(ensemble, 10, axis=0))
    hi = _safe_positive(np.percentile(ensemble, 90, axis=0))
    alt_index = int(np.argmin(np.abs(h_km - params["forecast_altitude_km"])))
    times_hr = t_grid_s / 3600.0

    fig, ax = plt.subplots(
        figsize=(params["forecast_figure_width_in"], params["forecast_figure_height_in"]),
        constrained_layout=True,
    )

    mean_1d = _smooth_series(mean[:, alt_index])
    lo_1d = _smooth_series(lo[:, alt_index])
    hi_1d = _smooth_series(hi[:, alt_index])
    det_1d = _smooth_series(deterministic[:, alt_index])

    ax.fill_between(times_hr, lo_1d, hi_1d, color="tab:blue", alpha=0.22, label="10-90% band")
    ax.plot(times_hr, mean_1d, color="tab:blue", linewidth=2.3, label="ensemble mean")
    ax.plot(times_hr, det_1d, color="tab:red", linestyle="--", linewidth=2.0, label="deterministic")
    ax.set_xlabel("Forecast lead time [h]")
    ax.set_ylabel(r"$n$ at 90 km [cm$^{-3}$]")
    ax.set_title("Diverging forecast uncertainty")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_ylim(bottom=max(1.0e-4, 0.0))
    format_axes(ax)

    fig.suptitle("Future electron-density prediction with diverging uncertainty")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "figures" / "output",
        help="Directory where the PNG will be written.",
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="future_uncertainty_forecast.png",
        help="Output PNG filename.",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()
    output_path = args.output_dir / args.filename
    make_figure(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
