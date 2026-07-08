import numpy as np

from lorenzsw.precipitation import gaussian_precipitation


def test_gaussian_precipitation_peaks_at_center():
    h = np.array([80.0, 90.0, 100.0])
    out = gaussian_precipitation(h, 0.0, lambda t: 1.0e3, h_p_km=90.0, H_p_km=8.0)
    assert out[1] == out.max()


def test_gaussian_precipitation_integrates_to_q0_over_fine_grid():
    h = np.linspace(40.0, 140.0, 2001)
    q0 = 1.0e3
    out = gaussian_precipitation(h, 0.0, lambda t: q0, h_p_km=90.0, H_p_km=8.0)
    recovered = np.trapezoid(out, h) * 35.0
    assert np.isclose(recovered, q0, rtol=0.01)


def test_gaussian_precipitation_accepts_time_varying_peak_altitude():
    h = np.array([80.0, 90.0, 100.0])

    def h_p(t: float) -> float:
        return 80.0 + 5.0 * t

    out = gaussian_precipitation(h, 2.0, lambda t: 1.0e3, h_p_km=h_p, H_p_km=8.0)
    assert out[1] == out.max()
