import numpy as np

from lorenzsw.sde import diffusion_term, euler_maruyama_step


def test_diffusion_term_matches_specification():
    n = np.array([4.0, 9.0])
    P_precip = np.array([2.0, 8.0])
    out = diffusion_term(n, P_precip, P_max=10.0, sigma0=2.0, beta_g=0.5)
    expected = 2.0 * (1.0 + 0.5 * P_precip / 10.0) * np.sqrt(n)
    assert np.allclose(out, expected)


def test_euler_maruyama_reflects_negative_values():
    rng = np.random.default_rng(0)
    n = np.array([1.0])
    drift = np.array([-10.0])
    diffusion = np.array([0.0])
    out = euler_maruyama_step(n, drift, diffusion, dt_s=0.2, rng=rng)
    assert np.allclose(out, np.array([1.0]))
