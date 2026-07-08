"""DMD transfer-operator approximation."""

from __future__ import annotations

from typing import Optional

import numpy as np
from loguru import logger


logger.debug("Loaded transfer_operator module")


def dmd_transfer_operator(
    snapshots: np.ndarray,
    r: Optional[int] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Approximate the transfer operator with dynamic mode decomposition."""

    snapshots = np.asarray(snapshots, dtype=float)
    if snapshots.ndim != 2:
        raise ValueError("snapshots must have shape (n_features, n_time).")
    n_features, n_time = snapshots.shape
    if n_time < 2:
        raise ValueError("snapshots must contain at least two time slices.")

    X = snapshots[:, :-1]
    Xp = snapshots[:, 1:]
    U, s, Vh = np.linalg.svd(X, full_matrices=False)
    if r is None:
        tol = np.finfo(float).eps * max(X.shape) * (s[0] if s.size else 0.0)
        r_eff = int(np.sum(s > tol))
    else:
        if r < 1:
            raise ValueError("r must be at least 1 when provided.")
        r_eff = min(int(r), s.size)

    if r_eff < 1:
        raise ValueError("Unable to determine a valid reduced rank.")

    logger.info(
        "Computing DMD with {} features, {} snapshots, rank {}",
        n_features,
        n_time,
        r_eff,
    )
    U_r = U[:, :r_eff]
    s_r = s[:r_eff]
    Vh_r = Vh[:r_eff, :]
    S_inv = np.diag(1.0 / s_r)
    A_tilde = U_r.conj().T @ Xp @ Vh_r.conj().T @ S_inv
    eigenvalues, W = np.linalg.eig(A_tilde)
    modes = Xp @ Vh_r.conj().T @ S_inv @ W
    logger.debug("DMD eigenvalue magnitudes: {}", np.abs(eigenvalues))
    return eigenvalues, modes
