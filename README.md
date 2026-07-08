# lorenz-sw-chaos

[![Docs](https://img.shields.io/badge/docs-MkDocs-blue)](docs/index.md)

Scaffold for the chaotic/stochastic ionospheric continuity-equation codebase.

## Layout

- `src/lorenzsw/`: package source code
- `tests/`: pytest test modules
- `docs/`: math and usage documentation
- `scripts/`: command-line helpers
- `.github/workflows/ci.yml`: CI workflow
- `.github/workflows/docs.yml`: GitHub Pages deployment workflow for the docs site

## Environment

Create the environment from `environment.yml`:

```bash
conda env create -f environment.yml
conda activate lorenzsw
```

## Make Targets

```bash
make help
make test
make coverage
make figures
make docs
```

## Status

This repository now includes the core deterministic and stochastic model code,
paper figures, shared model parameters, and Markdown documentation for the
equations and figure interpretation.

## Online Docs

The docs site is built with MkDocs and is set up for GitHub Pages deployment.
After the workflow runs on the `main` branch, GitHub will publish the generated
`site/` directory as the public documentation site.

The repository also includes `readthedocs.yml` if you want to publish the same
site on Read the Docs.
