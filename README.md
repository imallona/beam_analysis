# beam_analysis

Figures for the beam manuscript. The library is in a separate repo ([beam](https://github.com/imallona/beam)); this repo composes the figures from it.

The default backend is R: rbeam draws every panel with ggplot2 and patchwork, the same plots the beam HTML report shows. The numbers come from the beam Python package through reticulate; only the rendering is R. Each `figureN_*.R` module in `paper_figures_r/` exposes a `FIGUREN` list with `build()`; the driver writes one PDF per figure (plus a PNG preview) to `figures_r/`. The Python matplotlib backend under `paper_figures/` stays available (`make figures-python`, output in `figures/`).

## Build

```
make setup            # create .venv, install beam from ../beam and Python deps
make r-setup          # install rbeam and the R toolchain, and check versions
make figures          # R backend, into figures_r/
make figure-2         # one figure
make figures-python   # Python backend, into figures/
```

Point setup at another beam checkout with `BEAM_SRC=/path/to/beam`. Without make: `Rscript make_paper_figures.R` after `pip install -e ../beam` and `R CMD INSTALL ../beam/r/beam`. The Makefile points `RETICULATE_PYTHON` at `.venv`; otherwise set it yourself or let `common.R` find the sibling `.venv`.

The R backend needs R (>= 4.2) with reticulate (>= 1.40), ggplot2 and patchwork; `envs/figures-r.yml` is a conda recipe for the whole toolchain. Figures 4 and 5 fit R models (lme4, netmeta) and are skipped, not failed, when those are absent. Runs are deterministic: every `beam.rank` and `rank_sensitivity` seeds at zero.

Use reticulate 1.40 or newer. Earlier versions cannot convert numpy 2.x arrays and recurse until the R C stack overflows, which crashes every plot that reads a score matrix; rbeam warns at run time if it sees the bad pair. If you must stay on an older reticulate, pin numpy below 2 instead.

## Figures

- 1: schematic, `figure1/fig1_design.dot`, drawn with Graphviz (`make figure1`).
- 2 (`figure2_duo`): Duo 2018 clustering, a stable leader over an unstable lower order; the funky heatmap draws the Friedman-Nemenyi cliques as brackets.
- 3 (`figure3_domains`): M4 forecasting and GPTCelltype, variance re-partitioning across domains.
- 4 (`figure4_integration`): integration benchmarks disagree; a same-data contrast separates the analyst's choices from the data (needs R).
- 5 (`figure5_attribution`): attribution synthesis and the blinding check (needs R).
- 6 (`figure6_metrics`): the scIB metrics are not independent criteria.
