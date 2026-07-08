"""Helpers for standalone source-term plotting scripts."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURES_DIR = REPO_ROOT / "docs" / "assets" / "figures"


def equilibrium_density(production: np.ndarray, alpha_cm3s: float, beta_s: float) -> np.ndarray:
    """Return the positive equilibrium density implied by a source term."""

    production = np.asarray(production, dtype=float)
    if alpha_cm3s < 0:
        raise ValueError("alpha_cm3s must be non-negative.")
    if beta_s < 0:
        raise ValueError("beta_s must be non-negative.")

    if alpha_cm3s == 0:
        if beta_s == 0:
            return np.zeros_like(production)
        return production / beta_s

    disc = beta_s**2 + 4.0 * alpha_cm3s * np.maximum(production, 0.0)
    return (-beta_s + np.sqrt(disc)) / (2.0 * alpha_cm3s)


def mirror_figure_to_docs(output_path: Path, docs_filename: str | None = None) -> Path:
    """Copy a figure into the docs asset tree for MkDocs rendering."""

    DOCS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    docs_path = DOCS_FIGURES_DIR / (docs_filename or output_path.name)
    shutil.copy2(output_path, docs_path)
    return docs_path
