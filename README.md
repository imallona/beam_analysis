# beam_analysis

Figures for the beam manuscript. The library is in a separate repo
([beam](https://github.com/imallona/beam)); this repo only composes the figures
from it.

Each `figureN_*` module in `paper_figures/` has a `build()` returning a matplotlib
figure at the journal's size. The driver writes one vector PDF per figure (plus a
PNG preview) to `figures/`.

## Build

```
make setup      # create .venv, install beam from ../beam, install deps
make figures    # build all figures into figures/
make figure-2   # build one figure
```

Point setup at another beam checkout with `BEAM_SRC=/path/to/beam`. Without make:
`pip install -e ../beam` then `python make_paper_figures.py`.

Figures 4 and 5 fit R models (lme4, netmeta) and need an R toolchain; without it
they are skipped, not failed. The rest are pure Python. Runs are deterministic:
every `beam.rank` seeds at zero.

## Figures

- 1: schematic, drawn by hand, not built here.
- 2 (`figure2_duo`): Duo 2018 clustering, a stable leader over a fragile lower order.
- 3 (`figure3_domains`): M4 forecasting and GPTCelltype, variance re-partitioning across domains.
- 4 (`figure4_integration`): integration benchmarks disagree; a same-data contrast isolates the analyst (R).
- 5 (`figure5_attribution`): attribution synthesis and the blinding guard (R).
- 6 (`figure6_metrics`): the scIB metrics are not independent criteria.
