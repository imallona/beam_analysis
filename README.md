# beam_analysis

Figures and numbers for the beam manuscript. The library is in a separate repository ([beam](https://github.com/imallona/beam)); this repository composes the figures from it and writes the values the text cites to `results/numbers.json`.

The manuscript figures come from the R backend: rbeam draws every panel with ggplot2 and patchwork, the same plots the beam HTML report shows. The numbers come from the beam Python package through reticulate; only the rendering is R. Each `figureN_*.R` module in `paper_figures_r/` exposes a `FIGUREN` list with `build()`; the driver writes one PDF per figure (plus a PNG preview) to `figures_r/`. The Python matplotlib backend under `paper_figures/` is a fallback (`make figures-python`, output in `figures/`); its layout is not kept in step with the R figures, but `make_paper_numbers.py` reads the cached runs from `paper_figures/_common.py`.

## Build

```
make setup            # clone beam at BEAM_REF (default v0.3.0) under build/ and install it into .venv
make r-setup          # install rbeam from the same checkout and check the R toolchain
make figures          # R backend, into figures_r/
make figure-2         # one figure; make figure-S1 for the supplementary one
make figure1          # the design schematic, with Graphviz
make numbers          # results/numbers.json
make check            # lint and parse the figure code
```

To work against a local checkout instead of the tag, set `BEAM_SRC=../beam`. To use the conda environment from `envs/figures-r.yml` instead of `.venv`, set `PY=$CONDA_PREFIX/bin/python` on every make call; the Makefile passes it to reticulate as `RETICULATE_PYTHON`. `.github/workflows/figures.yml` runs the same steps on push and uploads the figures and the numbers as one artifact; it fails when a value in `results/numbers.json` other than the software versions changes, so commit the regenerated file with the code that changed it.

The R backend needs R (>= 4.2) with reticulate (>= 1.40), ggplot2 and patchwork; `envs/figures-r.yml` is a conda recipe for the whole toolchain. Figures 4 and 5 fit R models (lme4, netmeta) and are skipped, not failed, when those are absent. Runs are deterministic: every `beam.rank` and `rank_sensitivity` seeds at zero.

Use reticulate 1.40 or newer. Earlier versions cannot convert numpy 2.x arrays and recurse until the R C stack overflows, which crashes every plot that reads a score matrix; rbeam warns at run time if it sees the bad pair. If you must stay on an older reticulate, pin numpy below 2 instead.

## Figures

- 1: schematic, `figure1/fig1_design.dot`, drawn with Graphviz (`make figure1`).
- 2 (`figure2_duo`): Duo 2018 clustering: scores, composite, rank spans, specification curve and rank variance decomposition.
- 3 (`figure3_domains`): M4 forecasting and GPTCelltype cell type annotation.
- 4 (`figure4_integration`): five integration methods in five benchmarks, with the pancreas contrast between Tran and scIB (needs R).
- 5 (`figure5_attribution`): the rank variance split into analyst choices, datasets and benchmark in three settings (needs R).
- 6 (`figure6_metrics`): correlation, reliability and dimensionality of the scIB metrics in OpenProblems.
- S1 (`figureS1_blinding`): the Duo ranking with the method names and after blinding and unblinding.
