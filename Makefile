# Build the beam manuscript figures and the numbers behind them.
#
# beam is installed from BEAM_SRC. By default that is a checkout of the
# imallona/beam repository at BEAM_REF (a tag, a branch or a full commit hash),
# made under build/ in a directory named after the ref. Changing BEAM_REF makes
# a new checkout and reinstalls. Point BEAM_SRC at a local checkout to work
# against unreleased code (BEAM_SRC=../beam).
#
# The R backend draws the figures with rbeam, ggplot2 and patchwork and reads
# the numbers from the beam Python package through reticulate. It needs R 4.2 or
# newer with reticulate 1.40 or newer (see envs/figures-r.yml for the reason).
# Figures 4 and 5 and the integration numbers also need lme4 and netmeta.
#
# Python comes from a virtualenv under .venv unless PY names another
# interpreter, for example PY=$CONDA_PREFIX/bin/python inside the conda
# environment built from envs/figures-r.yml. PY has to be an absolute path or
# the venv path, because reticulate reads it as RETICULATE_PYTHON.

# The commit of imallona/beam#4, which has the plot functions the figures use.
# Move this to the release tag once that pull request is merged and tagged.
BEAM_REF ?= aa06a3c3e1ac9fe8ae958dd9fab3a4e20e10a271
BEAM_SRC ?= build/beam-$(BEAM_REF)
PYTHON ?= python3
RSCRIPT ?= Rscript
VENV := .venv
PY ?= $(VENV)/bin/python
STAMP := $(VENV)/.installed-$(notdir $(abspath $(BEAM_SRC)))
export RETICULATE_PYTHON := $(if $(filter /%,$(PY)),$(PY),$(abspath $(PY)))

.PHONY: help setup r-setup figures figures-python figure1 numbers check clean

help:
	@echo "make setup           install beam (from $(BEAM_SRC)) and the Python deps into $(PY)"
	@echo "make r-setup         install the rbeam R package and check the R toolchain"
	@echo "make figures         build all figures with the R backend into figures_r/"
	@echo "make figure-N        build one R figure, e.g. make figure-2 or make figure-S1"
	@echo "make figures-python  build all figures with the Python backend into figures/"
	@echo "make figure1         draw the design schematic with Graphviz"
	@echo "make numbers         write the values behind the figures to results/numbers.json"
	@echo "make check           lint and syntax-check the figure code (Python and R)"
	@echo "make clean           remove generated figures"
	@echo "Variables: BEAM_REF=$(BEAM_REF) BEAM_SRC=$(BEAM_SRC) PY=$(PY)"

$(BEAM_SRC):
	git init -q $@
	git -C $@ fetch -q --depth 1 https://github.com/imallona/beam $(BEAM_REF)
	git -C $@ checkout -q --detach FETCH_HEAD

$(STAMP): | $(BEAM_SRC)
	test "$(PY)" != "$(VENV)/bin/python" || $(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e $(BEAM_SRC)
	$(PY) -m pip install matplotlib numpy scipy ruff
	mkdir -p $(dir $@) && rm -f $(VENV)/.installed* && touch $@

setup: $(STAMP)

r-setup: $(STAMP)
	$(RSCRIPT) tools/setup_r.R "$(BEAM_SRC)"

figures: $(STAMP)
	$(RSCRIPT) make_paper_figures.R

figure-%: $(STAMP)
	$(RSCRIPT) make_paper_figures.R $*

figures-python: $(STAMP)
	$(PY) make_paper_figures.py

figure1:
	dot -Tpdf figure1/fig1_design.dot -o figure1/fig1_design.pdf

numbers: $(STAMP)
	$(PY) make_paper_numbers.py

check: $(STAMP)
	$(PY) -m ruff check .
	$(PY) -m py_compile paper_figures/*.py make_paper_figures.py make_paper_numbers.py tools/compare_numbers.py
	$(RSCRIPT) -e 'invisible(lapply(list.files("paper_figures_r", "[.]R$$", full.names=TRUE), parse)); invisible(parse("make_paper_figures.R")); cat("R syntax OK\n")'

clean:
	rm -f figures/*.pdf figures/*.png figures_r/*.pdf figures_r/*.png
