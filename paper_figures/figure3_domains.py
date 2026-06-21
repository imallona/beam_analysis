"""Figure 3: the rank-variance re-partitions across domains.

Layout ``(a1 | a2) / (b1 | b2)``: M4 forecasting on top, GPTCelltype
language-model cell typing below. Each domain pairs a rank-variance
decomposition (left) with the diagnostic that reads its separability (right).
The reading is that the order is stable to weighting and aggregation but moves
with which band or dataset is read.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from beam.datasets import load_gptcelltype, load_m4
from beam.mcda import (
    critical_difference,
    rank_sensitivity,
    registry_context,
    specification_curve,
)
from beam.reporting.figures import critical_difference_plot, specification_curve_plot

from . import _common as C

_CLASSICAL = {"CellMarker2.0", "SingleR", "ScType"}
_GPT_HEAD = ["GPT-4", "GPT-3.5", "CellMarker2.0", "SingleR", "ScType"]


def _m4_rank_sensitivity():
    """Rank-sensitivity over the M4 method by band by metric tensor."""
    m4 = load_m4()
    ctx = registry_context(list(m4.metric_ids), "saw")
    return rank_sensitivity(
        m4.tensor(),
        ctx.polarity,
        normalization=list(ctx.normalization),
        bounds=list(ctx.bounds),
        baselines=list(ctx.baselines),
        targets=list(ctx.targets),
        tool_names=m4.method_names,
        dataset_names=m4.frequency_names,
    )


def _gpt_composite_bar(host):
    """Mean annotation agreement per head method on the complete block.

    The five methods Hou and Ji compare directly, scored on the datasets where
    all five were run (the same block the critical-difference panel uses), so
    GPT-4 and the panel beside it read off one set of methods and datasets.
    """
    g = load_gptcelltype()
    idx = [g.method_names.index(m) for m in _GPT_HEAD]
    sub = g.scores[idx]
    complete = ~np.isnan(sub[:, :, 0]).any(axis=0)
    mean_agreement = sub[:, complete, 0].mean(axis=1)
    order = np.argsort(-mean_agreement)
    names = [_GPT_HEAD[i] for i in order]
    colors = ["#888888" if _GPT_HEAD[i] in _CLASSICAL else C.DATA_COLOR for i in order]
    ax = host.subplots()
    ax.bar(range(len(names)), mean_agreement[order], color=colors)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylabel("mean agreement (higher is better)")
    ax.set_title("composite score per method")


def _gpt_critical_difference(host):
    """Friedman-Nemenyi diagram on the complete five-method agreement block."""
    g = load_gptcelltype()
    idx = [g.method_names.index(m) for m in _GPT_HEAD]
    sub = g.scores[idx]
    complete = ~np.isnan(sub[:, :, 0]).any(axis=0)
    block = sub[:, complete, :]
    cd = critical_difference(block[:, :, 0], "higher_is_better", tool_names=tuple(_GPT_HEAD))
    critical_difference_plot(
        tuple(_GPT_HEAD), cd.average_ranks, cd.critical_difference, cd.cliques, host=host
    )


def build() -> Figure:
    rs_m4 = _m4_rank_sensitivity()
    curve = specification_curve(rs_m4)

    fig = C.figure(C.FULL_WIDTH_MM, 140.0)
    top, bottom = fig.subfigures(2, 1, height_ratios=[1.0, 1.0])

    a1, a2 = top.subfigures(1, 2, width_ratios=[1.0, 1.4])
    C.variance_bars(a1, rs_m4, title="M4 rank-variance share")
    C.panel_label(a1, "a")
    specification_curve_plot(curve, host=a2)

    b1, b2 = bottom.subfigures(1, 2, width_ratios=[1.0, 1.4])
    _gpt_composite_bar(b1)
    C.panel_label(b1, "b")
    _gpt_critical_difference(b2)
    return fig
