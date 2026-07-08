import numpy as np

from lorenzsw.continuity import continuity_drift


def test_continuity_drift_reduces_to_quadratic_loss():
    n = np.array([1.0, 2.0, 3.0])
    out = continuity_drift(n, np.zeros_like(n), np.zeros_like(n), alpha_cm3s=0.5, beta_s=0.0)
    assert np.allclose(out, -0.5 * n**2)


def test_quadratic_loss_matches_closed_form_under_euler_integration():
    alpha = 0.1
    n0 = 2.0
    dt = 1e-4
    t_final = 0.1
    n = np.array([n0], dtype=float)
    t = 0.0
    while t < t_final:
        drift = continuity_drift(n, np.zeros_like(n), np.zeros_like(n), alpha_cm3s=alpha, beta_s=0.0)
        n = n + drift * dt
        t += dt

    exact = n0 / (1.0 + alpha * n0 * t_final)
    assert np.isclose(n[0], exact, rtol=5e-3, atol=5e-4)
