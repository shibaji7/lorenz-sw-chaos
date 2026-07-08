"""Generate the paper figures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("/tmp") / "xdg-cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lorenzsw.figures.fig1_swmi_schematic import make_figure as make_fig1
from lorenzsw.figures.fig2_sde_ensemble import make_figure as make_fig2
from lorenzsw.figures.fig3_transfer_operator import make_figure as make_fig3
from lorenzsw.figures.fig4_exceedance import make_figure as make_fig4
from plot_chapman_precip_two_panel import make_figure as make_two_panel_figure
from plot_electron_density_profiles import make_figure
from plot_photoionization_term import make_figure as make_photoionization_figure
from plot_precipitation_term import make_figure as make_precipitation_figure
from _source_term_plot_utils import mirror_figure_to_docs
from lorenzsw.model_params import load_model_params
from lorenzsw._logging import configure_logging


def main() -> int:
    configure_logging()
    logger.info("Generating all figures")
    figures_dir = REPO_ROOT / "figures" / "output"
    params = load_model_params()
    make_fig1(figures_dir / "fig1_swmi_schematic.png", params)
    make_fig2(figures_dir / "fig2_sde_ensemble.png", params)
    make_fig3(figures_dir / "fig3_transfer_operator.png", params)
    make_fig4(figures_dir / "fig4_exceedance.png", params)
    make_figure(output_path=figures_dir / "electron_density_profiles.png", params=params)
    make_two_panel_figure(output_path=figures_dir / "chapman_precip_two_panel.png", params=params)
    make_photoionization_figure(output_path=figures_dir / "chapman_photoionization_term.png", params=params)
    make_precipitation_figure(output_path=figures_dir / "precipitation_term.png", params=params)
    for name in [
        "fig1_swmi_schematic.png",
        "fig2_sde_ensemble.png",
        "fig3_transfer_operator.png",
        "fig4_exceedance.png",
        "electron_density_profiles.png",
        "chapman_precip_two_panel.png",
        "chapman_photoionization_term.png",
        "precipitation_term.png",
        "future_uncertainty_forecast.png",
    ]:
        candidate = figures_dir / name
        if candidate.exists():
            mirror_figure_to_docs(candidate)
    logger.success("Figure generation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
