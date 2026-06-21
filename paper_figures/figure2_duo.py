"""Figure 2: a stable leading method with a fragile lower order (Duo 2018).

Layout ``a / (b | c)``: the funky heatmap on top, the specification curve and
the rank-variance decomposition side by side below. The reading is that Seurat
holds the top across the analyst's choices while the lower order does not, and
that most of the rank movement is the dataset rather than the choices.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from beam.mcda import critical_difference, specification_curve
from beam.reporting import funky_heatmap_from_run
from beam.reporting.figures import specification_curve_plot

from . import _common as C


def _duo_cliques(duo):
    """Friedman-Nemenyi cliques on the ARI slice, as method-name groups."""
    ari = duo.tensor(("ari",))[:, :, 0]
    complete = ~np.isnan(ari).any(axis=0)
    cd = critical_difference(ari[:, complete], "higher_is_better", tool_names=duo.method_names)
    return tuple(tuple(duo.method_names[i] for i in clique) for clique in cd.cliques)


def build() -> Figure:
    duo, run = C.duo_run()
    rs = C.duo_rank_sensitivity()
    cliques = _duo_cliques(duo)
    curve = specification_curve(rs)

    fig = C.figure(C.FULL_WIDTH_MM, 195.0)
    top, bottom = fig.subfigures(2, 1, height_ratios=[1.35, 1.0])

    funky_heatmap_from_run(
        run,
        cliques=cliques,
        show_smaa=False,
        show_aggregation_consensus=True,
        host=top,
    )
    C.panel_label(top, "a")

    left, right = bottom.subfigures(1, 2, width_ratios=[2.0, 1.0])
    specification_curve_plot(curve, host=left)
    C.panel_label(left, "b")
    C.variance_bars(right, rs, title="rank-variance share")
    C.panel_label(right, "c")
    return fig
