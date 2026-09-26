"""Write the values behind the figures to results/numbers.json.

    python make_paper_numbers.py

The figure code and this script read the same cached runs in
paper_figures/_common.py. The integration and attribution entries need R
(lme4, netmeta) and are left out when it is absent.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from importlib import metadata
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paper_figures import _common as C

OUTPUT = Path(__file__).resolve().parent / "results" / "numbers.json"
MAX_ARRAY_CELLS = 400


def plain(value):
    """Reduce a beam report to JSON types, leaving out large arrays."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        fields = {f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
        return {name: field for name, field in fields.items() if field is not None}
    if isinstance(value, np.ndarray):
        return value.tolist() if value.size <= MAX_ARRAY_CELLS else None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [plain(item) for item in value]
        return items if len(items) <= MAX_ARRAY_CELLS else None
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def names(indices, tool_names):
    return [tool_names[i] for i in indices]


def rank_sensitivity_summary(report):
    from beam.mcda import specification_curve

    curve = specification_curve(report)
    tools = report.tool_names
    return {
        "weightings": list(report.weightings),
        "aggregations": list(report.methods),
        "datasets": list(report.dataset_names),
        "n_combinations": report.n_combinations,
        "factor_shares": plain(report.factor_shares),
        "interaction_share": report.interaction_share,
        "headline_tool": tools[report.headline_tool],
        "headline_top_fraction": report.headline_top_fraction,
        "headline_rank_span": report.headline_rank_span,
        "most_frequent_top_tool": tools[curve.most_frequent_top_tool],
        "most_frequent_top_fraction": curve.most_frequent_top_fraction,
        "distinct_top_tools": names(curve.distinct_top_tools, tools),
    }


def critical_difference_summary(report):
    tools = report.tool_names
    return {
        "n_tools": report.n_tools,
        "n_datasets": report.n_datasets,
        "alpha": report.alpha,
        "friedman_statistic": report.friedman_statistic,
        "friedman_pvalue": report.friedman_pvalue,
        "critical_difference": report.critical_difference,
        "average_ranks": dict(zip(tools, plain(report.average_ranks), strict=True)),
        "cliques": [names(clique, tools) for clique in report.cliques],
    }


def duo_numbers():
    from beam.mcda import critical_difference

    duo, run = C.duo_run()
    ari = duo.tensor(("ari",))[:, :, 0]
    complete = ~np.isnan(ari).any(axis=0)
    nemenyi = critical_difference(ari[:, complete], "higher_is_better", tool_names=duo.method_names)
    return {
        "metrics": list(C.DUO_METRICS),
        "n_methods": len(duo.method_names),
        "n_datasets": len(duo.dataset_names),
        "top_tool": run.top_tool,
        "rank_sensitivity": rank_sensitivity_summary(C.duo_rank_sensitivity()),
        "ari_critical_difference": critical_difference_summary(nemenyi),
    }


def m4_numbers():
    from beam.datasets import load_m4

    from paper_figures.figure3_domains import _m4_rank_sensitivity

    m4 = load_m4()
    return {
        "metrics": list(m4.metric_ids),
        "n_methods": len(m4.method_names),
        "n_datasets": len(m4.frequency_names),
        "rank_sensitivity": rank_sensitivity_summary(_m4_rank_sensitivity()),
    }


def gptcelltype_numbers():
    from beam.datasets import load_gptcelltype
    from beam.mcda import critical_difference

    from paper_figures.figure3_domains import _GPT_HEAD

    gpt = load_gptcelltype()
    agreement = gpt.scores[[gpt.method_names.index(m) for m in _GPT_HEAD], :, 0]
    complete = ~np.isnan(agreement).any(axis=0)
    nemenyi = critical_difference(
        agreement[:, complete], "higher_is_better", tool_names=tuple(_GPT_HEAD)
    )
    mean_agreement = agreement[:, complete].mean(axis=1)
    return {
        "methods": list(_GPT_HEAD),
        "n_datasets": int(agreement.shape[1]),
        "n_complete_datasets": int(complete.sum()),
        "mean_agreement": dict(zip(_GPT_HEAD, plain(mean_agreement), strict=True)),
        "critical_difference": critical_difference_summary(nemenyi),
    }


def metric_set_numbers():
    validity, reliability, dimensionality = C.openproblems_metric_quality()
    return {
        "metrics": list(validity.metric_ids),
        "groups": dict(zip(validity.metric_ids, validity.groups, strict=True)),
        "n_observations": validity.n_observations,
        "mean_convergent": validity.mean_convergent,
        "mean_discriminant": validity.mean_discriminant,
        "convergent_by_group": plain(validity.convergent_by_group),
        "alpha_by_group": plain(reliability.alpha_by_group),
        "alpha_if_dropped": plain(reliability.alpha_if_dropped),
        "pc1_explained_by_group": plain(dimensionality.pc1_explained_by_group),
        "kaiser_components_by_group": plain(dimensionality.kaiser_components_by_group),
        "parallel_components_by_group": plain(dimensionality.parallel_components_by_group),
        "parallel_analysis": {"n_iter": dimensionality.n_iter, "seed": dimensionality.seed},
    }


def integration_numbers():
    from beam.datasets import load_integration_benchmarks, load_pancreas_contrast
    from beam.heterogeneity import network_meta_analysis

    from paper_figures import figure4_integration as F4

    benchmarks = load_integration_benchmarks()
    source_sets = {
        "three": F4.THREE_SOURCES,
        "four": F4.FOUR_SOURCES,
        "five": F4.FIVE_SOURCES,
    }
    return {
        "method_benchmark_share": {
            label: plain(F4._safe_share(benchmarks, keep)) for label, keep in source_sets.items()
        },
        "source_variance_five": plain(F4._source_variance(benchmarks, F4.FIVE_SOURCES)),
        "network_meta_analysis": plain(network_meta_analysis(*benchmarks.network_arms())),
        "pancreas_spearman": float(load_pancreas_contrast().spearman()),
    }


def attribution_numbers():
    from paper_figures.figure5_attribution import _attribution_report

    return plain(_attribution_report())


def software_versions():
    packages = ("beam", "numpy", "scipy", "pymcdm")
    versions = {name: metadata.version(name) for name in packages}
    versions["python"] = sys.version.split()[0]
    return versions


def main() -> int:
    from beam.heterogeneity import RNotAvailableError

    numbers = {
        "software": software_versions(),
        "duo": duo_numbers(),
        "m4": m4_numbers(),
        "gptcelltype": gptcelltype_numbers(),
        "metric_sets": metric_set_numbers(),
    }
    for key, build in (("integration", integration_numbers), ("attribution", attribution_numbers)):
        try:
            numbers[key] = build()
        except RNotAvailableError as exc:
            print(f"  {key}: skipped, needs R ({exc})")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(numbers, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
