"""Figure 6: the scIB biological and batch metrics are not independent criteria.

Layout ``a | (b / c)``: the oriented metric correlation heatmap on the left, the
reliability-if-dropped bars over the dimensionality scree on the right. The
reading is that the bio/batch split is the right axis but its two sides differ:
the biological group is one reliable two-factor scale, the batch group a weaker
one-factor collection, so weighting the metrics as separate criteria double
counts. Pure Python; no R toolchain needed.
"""

from __future__ import annotations

from matplotlib.figure import Figure

from beam.reporting.figures import (
    dimensionality_scree_plot,
    metric_correlation_heatmap,
    reliability_if_dropped_plot,
)

from . import _common as C


def build() -> Figure:
    validity, reliability, dimensionality = C.openproblems_metric_quality()

    fig = C.figure(C.FULL_WIDTH_MM, 125.0)
    left, right = fig.subfigures(1, 2, width_ratios=[1.0, 1.05])

    metric_correlation_heatmap(validity, host=left, title="metric correlation")
    C.panel_label(left, "a")

    top, bottom = right.subfigures(2, 1, height_ratios=[1.0, 1.0])
    reliability_if_dropped_plot(reliability, host=top, title="reliability if dropped")
    C.panel_label(top, "b")
    dimensionality_scree_plot(dimensionality, host=bottom, title="dimensionality scree")
    C.panel_label(bottom, "c")
    return fig
