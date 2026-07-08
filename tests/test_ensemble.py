import numpy as np

from lorenzsw.ensemble import run_deterministic, run_ensemble


def _zero_precipitation(h_km: np.ndarray, t_s: float) -> np.ndarray:
    return np.zeros_like(h_km)


def _zero_forcing(t_s: float) -> float:
    return 0.0


def test_deterministic_and_ensemble_match_when_sigma_zero():
    h = np.array([90.0])
    t_grid = np.array([0.0, 1.0, 2.0])
    n0 = np.array([10.0])
    det = run_deterministic(
        n0=n0,
        t_grid_s=t_grid,
        h_km=h,
        P0_t=_zero_forcing,
        Q0_t=_zero_forcing,
        precip_model=_zero_precipitation,
        h_m_km=90.0,
        H_km=6.0,
        chi_rad=0.0,
        alpha_cm3s=0.1,
        beta_s=0.0,
    )
    ens = run_ensemble(
        n0=n0,
        t_grid_s=t_grid,
        h_km=h,
        P0_t=_zero_forcing,
        Q0_t=_zero_forcing,
        precip_model=_zero_precipitation,
        h_m_km=90.0,
        H_km=6.0,
        chi_rad=0.0,
        alpha_cm3s=0.1,
        beta_s=0.0,
        sigma0=0.0,
        beta_g=0.0,
        P_max=1.0,
        n_members=4,
        seed=123,
    )
    assert np.allclose(ens[:, :, 0], det[:, 0])
    assert np.allclose(ens[0], ens[1])


def test_run_ensemble_returns_non_negative_values():
    h = np.array([90.0])
    t_grid = np.array([0.0, 0.5, 1.0])
    n0 = np.array([1.0])
    ens = run_ensemble(
        n0=n0,
        t_grid_s=t_grid,
        h_km=h,
        P0_t=_zero_forcing,
        Q0_t=_zero_forcing,
        precip_model=_zero_precipitation,
        h_m_km=90.0,
        H_km=6.0,
        chi_rad=0.0,
        alpha_cm3s=0.0,
        beta_s=0.0,
        sigma0=3.0,
        beta_g=0.0,
        P_max=1.0,
        n_members=8,
        seed=1,
    )
    assert np.all(ens >= 0.0)
