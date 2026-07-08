# Source-Term Figures

This page explains the individual source terms used by the model.

The two figures here separate the driving terms so a reader can see how each
one behaves before they are combined in the continuity equation.

## Chapman photoionization

![Chapman photoionization term](assets/figures/chapman_photoionization_term.png)

The Chapman source is the solar-production term.

What the panels show:

- left panel: the production rate as a function of altitude
- right panel: the equilibrium density implied by that source term when loss is
  included

How to read it:

- the peak location is controlled mainly by `h_m`
- the vertical width is controlled mainly by `H`
- the overall amplitude is controlled by `P_0(t)`
- the solar zenith-angle factor `chi` changes the asymmetry and effective
  intensity

Why it matters:

- this is the background ionization source
- it is the term that gives the ionosphere its broad vertical structure
- it tells you where the solar-driven electron production is strongest

The Chapman form is the classical ionospheric photoionization profile introduced
by Chapman [Chapman 1931](references.md#chapman-1931).

Physical interpretation:

- larger `P_0` means stronger solar ionization
- larger `H` spreads the layer vertically
- shifting `h_m` moves the peak altitude
- changing `chi` changes how strongly the solar beam penetrates the layer

The right panel is not a new physical law. It is the equilibrium state implied
by balancing that source against the loss model.

## Precipitation proxy

![Precipitation source term](assets/figures/precipitation_term.png)

The precipitation term is a localized Gaussian source.

What the panels show:

- left panel: the precipitation production rate as a function of altitude
- right panel: the equilibrium density implied by that source term when loss is
  included

How to read it:

- the peak altitude is controlled by `h_p`
- the vertical width is controlled by `H_p`
- the amplitude is controlled by `Q_0(t)`
- the normalization uses `\Delta\varepsilon_{\mathrm{ion}}` so the source can
  be interpreted as an ionization proxy

Why it matters:

- precipitation is often localized in altitude
- it can create narrow enhancements that do not look like the broader Chapman
  background
- it is one of the main reasons the total profile becomes more uncertain and
  more structured

This kind of localized forcing is part of modern particle-precipitation
modeling in space physics [McGranaghan et al. 2020](references.md#mcgranaghan-2020),
[Grandin et al. 2023](references.md#grandin-2023).

Physical interpretation:

- larger `Q_0` means stronger deposition
- larger `H_p` makes the forcing more spread out vertically
- moving `h_p` shifts the peak region of particle energy deposition

## Why these plots are useful

The full continuity equation combines these terms:

$$
\frac{\partial n}{\partial t}
= P_{\mathrm{solar}} + P_{\mathrm{precip}} - \alpha n^2 - \beta n
$$

The source-term figures show the inputs separately before they are coupled
together.

That matters because a reader can then distinguish:

- background solar creation
- localized particle deposition
- nonlinear loss
- the way those terms combine in the forecast

## Script links

- `scripts/plot_photoionization_term.py`
- `scripts/plot_precipitation_term.py`

These scripts also mirror their PNG outputs into `docs/assets/figures/` so the
same images can be embedded in the documentation site.
