import numpy as np

from lorenzsw.chapman import chapman_production


def test_chapman_peak_matches_p0_at_vertical_incidence():
    h = np.array([90.0])
    p0 = lambda t: 3.25
    out = chapman_production(h, 0.0, p0, h_m_km=90.0, H_km=6.0, chi_rad=0.0)
    assert np.allclose(out, np.array([3.25]))


def test_chapman_is_maximum_at_peak_for_vertical_incidence():
    h = np.array([84.0, 90.0, 96.0])
    out = chapman_production(h, 0.0, lambda t: 2.0, h_m_km=90.0, H_km=6.0, chi_rad=0.0)
    assert out[1] == out.max()
