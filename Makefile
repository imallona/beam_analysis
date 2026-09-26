# Build the beam manuscript figures. The default backend is R: rbeam draws the
# panels natively with ggplot2 and patchwork. The Python matplotlib backend is
# kept as a second option. Both read the numbers from the beam Python package;
# only the rendering differs.
#
# The R backend needs R (>= 4.2) with reticulate (>= 1.40; see envs/figures-r.yml
# for why the version matters), ggplot2, patchwork and the rbeam package from
# $(BEAM_SRC)/r/beam. Figures 4 and 5 also need lme4 and netmeta. `make r-setup`
# installs and checks all of it. beam is installed editable from a sibling
# checkout; override its location with BEAM_SRC=/path/to/beam.

PYTHON ?= python3
BEAM_SRC ?= ../beam
RSCRIPT ?= Rscript
VENV := .venv
PY := $(VENV)/bin/python
# The R backend calls this Python through reticulate.
export RETICULATE_PYTHON := $(abspath $(PY))

.PHONY: help setup r-setup figures figures-python figure1 numbers check clean

help:
	@echo "make setup           create $(VENV) and install beam (from $(BEAM_SRC)) and Python deps"
	@echo "make r-setup         install the rbeam R package and check the R toolchain"
	@echo "make figures         build all figures with the R backend into figures_r/"
	@echo "make figure-N        build one R figure, e.g. make figure-2"
	@echo "make figures-python  build all figures with the Python backend into figures/"
	@echo "make figure1         draw the design schematic with Graphviz"
	@echo "make numbers         write the values behind the figures to results/numbers.json"
	@echo "make check           lint and syntax-check the figure code (Python and R)"
	@echo "make clean           remove generated figures"

$(VENV)/.installed:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e $(BEAM_SRC)
	$(PY) -m pip install matplotlib numpy scipy ruff
	touch $@

setup: $(VENV)/.installed

r-setup: $(VENV)/.installed
	$(RSCRIPT) tools/setup_r.R "$(BEAM_SRC)"

figures: $(VENV)/.installed
	$(RSCRIPT) make_paper_figures.R

figure-%: $(VENV)/.installed
	$(RSCRIPT) make_paper_figures.R $*

figures-python: $(VENV)/.installed
	$(PY) make_paper_figures.py

figure1:
	dot -Tpdf figure1/fig1_design.dot -o figure1/fig1_design.pdf

numbers: $(VENV)/.installed
	$(PY) make_paper_numbers.py

check: $(VENV)/.installed
	$(PY) -m ruff check .
	$(PY) -m py_compile paper_figures/*.py make_paper_figures.py make_paper_numbers.py
	$(RSCRIPT) -e 'invisible(lapply(list.files("paper_figures_r", "\\.R$$", full.names=TRUE), parse)); parse("make_paper_figures.R"); cat("R syntax OK\n")'

clean:
	rm -f figures/*.pdf figures/*.png figures_r/*.pdf figures_r/*.png
