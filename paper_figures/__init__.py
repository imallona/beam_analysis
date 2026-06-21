"""Reproducible Genome Biology manuscript figures for beam.

Each ``figureN_*`` module exposes ``build()`` returning a sized
``matplotlib.figure.Figure``. The driver in ``scripts/make_paper_figures.py``
calls them and writes one vector PDF per figure into ``docs/paper/figures/``.
"""
