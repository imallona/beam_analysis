"""Figure 5: the attribution synthesis and the blinding guard.

Layout ``a | b``: the attribution progression on the left, the blinding
invariance on the right. Panel a puts analyst choice, data and benchmarker on
one rank-variance budget across three settings, and the analyst-choice share
rises as the data contribution is removed by design. Panel b shows that blinding
the method names leaves the Duo ranking identical, with the seal fingerprint as
the auditable record that the pipeline was fixed before the labels were revealed.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

import beam
from beam.blinding import blind
from beam.datasets import load_integration_benchmarks, load_pancreas_contrast
from beam.heterogeneity import RNotAvailableError, r_available, source_variance_decomposition
from beam.mcda import (
    attribution_synthesis,
    setting_from_rank_sensitivity,
    setting_from_same_data_contrast,
    setting_from_source_variance,
)
from beam.reporting.figures import attribution_progression_plot

from . import _common as C

PUBLISHED_BENCHMARKS = ("Tran", "scIB", "OpenProblems")


def _attribution_report():
    """The three-setting attribution: Duo, pooled cross-benchmark, same-data."""
    if not r_available():
        raise RNotAvailableError("Figure 5 attribution needs the R toolchain (lme4)")
    duo_setting = setting_from_rank_sensitivity(
        C.duo_rank_sensitivity(), "Duo\n(within benchmark)"
    )
    ib = load_integration_benchmarks()
    methods, datasets, benchmarks, scores = ib.mean_rank_records()
    source_variance = source_variance_decomposition(methods, datasets, benchmarks, scores)
    # No metric axis in the pooled mean-rank data, so the analyst-choice share is
    # not measurable and stays zero.
    pooled_setting = setting_from_source_variance(
        source_variance, 0.0, "pooled\n(cross-benchmark)"
    )
    pc = load_pancreas_contrast()
    same_data_setting = setting_from_same_data_contrast(
        {"Tran": pc.tran_mean_rank, "scIB": pc.scib_mean_rank}, "pancreas\n(same data)"
    )
    return attribution_synthesis([duo_setting, pooled_setting, same_data_setting])


def _blinding_panel(host) -> None:
    """Two rank columns, named and unblinded, with the seal fingerprint inset."""
    duo, run = C.duo_run()
    scores = beam.Scores(
        values=duo.tensor(C.DUO_METRICS),
        tool_names=tuple(duo.method_names),
        metric_ids=C.DUO_METRICS,
        dataset_names=duo.dataset_names,
        layout="long",
    )
    blinded, seal = blind(scores, seed=0)
    blinded_run = beam.rank(blinded, weights="equal", method="saw", seed=0, sensitivity=False)
    unblinded_names = list(seal.translate(blinded_run.tool_names))

    named_order = [run.tool_names[i] for i in np.argsort(run.result.ranks, kind="stable")]
    unblinded_order = [
        unblinded_names[i] for i in np.argsort(blinded_run.result.ranks, kind="stable")
    ]

    ax = host.subplots()
    ax.axis("off")
    n = len(named_order)
    ax.text(0.04, 1.0, "named", fontsize=7, fontweight="bold", va="bottom")
    ax.text(0.54, 1.0, "unblinded", fontsize=7, fontweight="bold", va="bottom")
    for rank, (named, unblinded) in enumerate(zip(named_order, unblinded_order, strict=True), 1):
        y = 1.0 - rank / (n + 1.0)
        agree = named == unblinded
        ax.text(0.04, y, f"{rank:>2}. {named}", fontsize=6, va="center", family="monospace")
        ax.text(0.54, y, f"{rank:>2}. {unblinded}", fontsize=6, va="center", family="monospace",
                color="#228833" if agree else "#cc3311")
    matches = sum(a == b for a, b in zip(named_order, unblinded_order, strict=True))
    seal_text = (
        f"orders identical: {matches}/{n}\n"
        f"seal sha256: {seal.fingerprint[:16]}...\nseed: {seal.seed}"
    )
    ax.text(0.04, -0.04, seal_text, fontsize=5.5, va="top", family="monospace",
            bbox={"boxstyle": "round", "fc": "#f0f0f0", "ec": "#888888"})


def build() -> Figure:
    report = _attribution_report()
    fig = C.figure(C.FULL_WIDTH_MM, 80.0)
    left, right = fig.subfigures(1, 2, width_ratios=[1.4, 1.0])
    attribution_progression_plot(report, host=left)
    C.panel_label(left, "a")
    _blinding_panel(right)
    C.panel_label(right, "b")
    return fig
