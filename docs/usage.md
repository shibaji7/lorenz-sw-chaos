# Usage

## Environment

```bash
conda env create -f environment.yml
conda activate lorenzsw
```

## Tests

```bash
pytest
make test
make coverage
```

## Figures

```bash
python scripts/generate_all_figures.py
make figures
python scripts/plot_photoionization_term.py
python scripts/plot_precipitation_term.py
```

## Docs Site

```bash
mkdocs build
make docs
make site
```
