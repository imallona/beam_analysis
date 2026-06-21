# Build the beam manuscript figures. Requires Python 3.10+ and, for figures 4 and
# 5, an R toolchain with lme4 and netmeta (see README). beam is installed editable
# from a sibling checkout; override its location with BEAM_SRC=/path/to/beam.

PYTHON ?= python3
BEAM_SRC ?= ../beam
VENV := .venv
PY := $(VENV)/bin/python

.PHONY: help setup figures check clean

help:
	@echo "make setup     create $(VENV) and install beam (from $(BEAM_SRC)) and deps"
	@echo "make figures   build all figures into figures/"
	@echo "make figure-N  build one figure, e.g. make figure-2"
	@echo "make check     lint and syntax-check the figure code"
	@echo "make clean     remove generated figures"

$(VENV)/.installed:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e $(BEAM_SRC)
	$(PY) -m pip install matplotlib numpy scipy ruff
	touch $@

setup: $(VENV)/.installed

figures: $(VENV)/.installed
	$(PY) make_paper_figures.py

figure-%: $(VENV)/.installed
	$(PY) make_paper_figures.py $*

check: $(VENV)/.installed
	$(PY) -m ruff check .
	$(PY) -m py_compile paper_figures/*.py make_paper_figures.py

clean:
	rm -f figures/*.pdf figures/*.png
