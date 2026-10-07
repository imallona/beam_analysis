# Changelog

## [Unreleased]

- migrate to R plots instead of pythons, but keeping them too
- `make numbers` writes the values behind the figures to `results/numbers.json`
- `make figure1` draws the design schematic
- beam is installed from `BEAM_REF` (a tag, a branch or a commit) unless `BEAM_SRC` points at a checkout
- `make numbers` also writes the fit flags of the three and four benchmark models, the pancreas test, the blinding check and the beam git describe
- figure 5 keeps the attribution bars; the blinding check is supplementary figure S1
- figure 3 has one tag per panel, figure 4 draws the pancreas ranks as dots, figure 2 has a key for the circle size
- `.github/workflows/figures.yml` builds the figures and numbers on push
- a figure that fails to build fails `make figures`; `tools/compare_numbers.py` compares two numbers files with a tolerance
- beam pinned to v0.3.1
