import numpy as np

from lorenzsw.forcing.lorenz_precip import lorenz63_precip_forcing
from lorenzsw.forcing.soc_flare import _generate_soc_flare_events, soc_flare_forcing


def test_soc_flare_forcing_is_non_negative_and_reproducible():
    t = np.linspace(0.0, 6.0 * 3600.0, 721)
    out1 = soc_flare_forcing(
        t,
        rate_per_day=20.0,
        alpha_powerlaw=1.8,
        P0_background=1.0,
        P0_peak_scale=40.0,
        seed=42,
    )
    out2 = soc_flare_forcing(
        t,
        rate_per_day=20.0,
        alpha_powerlaw=1.8,
        P0_background=1.0,
        P0_peak_scale=40.0,
        seed=42,
    )
    assert np.all(out1 >= 0.0)
    assert np.allclose(out1, out2)


def test_soc_flare_powerlaw_amplitudes_follow_requested_exponent():
    t = np.linspace(0.0, 40.0 * 86400.0, 2001)
    _, amplitudes = _generate_soc_flare_events(
        t,
        rate_per_day=250.0,
        alpha_powerlaw=1.9,
        P0_peak_scale=1.0,
        seed=7,
    )
    assert amplitudes.size > 1000
    amps = np.sort(amplitudes)
    ccdf = (amps.size - np.arange(amps.size)) / amps.size
    slope, _ = np.polyfit(np.log10(amps), np.log10(ccdf), 1)
    fitted_exponent = -slope
    assert np.isclose(fitted_exponent, 1.9, rtol=0.15)


def test_lorenz63_precip_forcing_is_bounded_and_non_negative():
    t = np.linspace(0.0, 3600.0, 601)
    out = lorenz63_precip_forcing(t, Q_mean_eV=1.0e3, kappa=0.6, seed=4)
    assert np.all(np.isfinite(out))
    assert np.all(out >= 0.0)
    assert out.max() < 6.0e3
    assert out.std() > 0.0
