import numpy as np

from lorenzsw.lyapunov import estimate_lyapunov, predictability_horizon


def test_estimate_lyapunov_is_positive_for_exponential_separation():
    t = np.linspace(0.0, 4.0, 9)
    ensemble = np.zeros((4, t.size, 1), dtype=float)
    base = np.exp(0.4 * t)
    for m in range(ensemble.shape[0]):
        ensemble[m, :, 0] = base * (1.0 + 0.1 * m)

    lam, curve = estimate_lyapunov(ensemble, t, h_index=0)
    assert lam > 0.0
    assert curve.shape == (t.size,)


def test_predictability_horizon_raises_on_nonpositive_lambda():
    import pytest

    with pytest.raises(ValueError):
        predictability_horizon(0.0, delta_max=10.0, delta_x0=1.0)
