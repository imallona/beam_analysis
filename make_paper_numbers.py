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

from beam.datasets import load_pancreas_contrast
from paper_figures import _common as C
from paper_figures import figure4_integration as F4

OUTPUT = Path(__file__).resolve().parent / "results" / "numbers.json"
MAX_ARRAY_CELLS = 400


def plain(value):
    """Reduce a beam report to JSON types, leaving out large arrays.

    Floats are rounded to six significant digits so that reruns on other
    machines reproduce the file exactly.
    """
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
    if isinstance(value, float):
        return float(f"{value:.6g}") if np.isfinite(value) else None
    return value


def names(indices, tool_names):
    return [tool_names[i] for i in indices]


def rank_sensitivity_summary(report):
    from beam.mcda import specification_curve

    curve = specification_curve(report)
    tools = report.tool_names
    headline_ranks = [spec.ranks[report.headline_tool] for spec in curve.specifications]
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
        "headline_best_rank": min(headline_ranks),
        "headline_worst_rank": max(headline_ranks),
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


def aggregation_max_rank_span(run):
    """Largest difference between the best and worst rank of a method over the aggregations."""
    from beam.mcda import aggregation_agreement

    context = run.context
    report = aggregation_agreement(
        run.matrix,
        context.polarity,
        normalization=list(context.normalization),
        bounds=list(context.bounds),
        baselines=list(context.baselines),
        targets=list(context.targets),
    )
    return int(np.max(np.asarray(report.rank_high) - np.asarray(report.rank_low)))


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
        "leave_one_dataset_out_max_rank_shift": run.leave_one_dataset_out.max_rank_shift,
        "aggregation_max_rank_span": aggregation_max_rank_span(run),
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
        "n_methods": validity.n_observations // 6,
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


def source_variance_fit(benchmarks, keep):
    """The fit on a benchmark subset, reduced to what the text reports."""
    from beam.heterogeneity import RExecutionError

    try:
        report = F4._source_variance(benchmarks, keep)
    except (RExecutionError, ValueError) as exc:
        return {"error": str(exc)}
    return {
        "method_benchmark_share": report.method_benchmark_share,
        "variance_components": plain(report.variance_components),
        "singular": report.singular,
        "n_obs": report.n_obs,
        "n_datasets": report.n_datasets,
        "n_benchmarks": report.n_benchmarks,
        "warnings": list(report.warnings),
    }


def pancreas_numbers():
    from scipy.stats import spearmanr

    pc = load_pancreas_contrast()
    test = spearmanr(pc.tran_mean_rank, pc.scib_mean_rank)
    tran_top, scib_top = pc.top_method()
    return {
        "methods": list(pc.methods),
        "metrics": list(pc.metrics),
        "n_methods": len(pc.methods),
        "spearman": float(test.correlation),
        "spearman_pvalue": float(test.pvalue),
        "tran_mean_rank": dict(zip(pc.methods, plain(pc.tran_mean_rank), strict=True)),
        "scib_mean_rank": dict(zip(pc.methods, plain(pc.scib_mean_rank), strict=True)),
        "top_method": {"Tran": tran_top, "scIB": scib_top},
    }


def integration_numbers():
    from beam.datasets import load_integration_benchmarks
    from beam.heterogeneity import network_meta_analysis

    benchmarks = load_integration_benchmarks()
    source_sets = {
        "three": F4.THREE_SOURCES,
        "four": F4.FOUR_SOURCES,
        "five": F4.FIVE_SOURCES,
    }
    fits = {label: source_variance_fit(benchmarks, keep) for label, keep in source_sets.items()}
    arms = benchmarks.network_arms()
    return {
        "n_records": len(benchmarks.rank),
        "benchmarks": sorted(set(benchmarks.benchmark)),
        "method_benchmark_share": {
            label: fit.get("method_benchmark_share", float("nan")) for label, fit in fits.items()
        },
        "source_variance_fits": fits,
        "source_variance_five": plain(F4._source_variance(benchmarks, F4.FIVE_SOURCES)),
        "network_arms": {"n_arms": len(arms[0]), "n_studies": len(set(arms[1]))},
        "network_meta_analysis": plain(network_meta_analysis(*arms)),
        "pancreas": pancreas_numbers(),
    }


def attribution_numbers():
    from paper_figures.figure5_attribution import _attribution_report

    return plain(_attribution_report())


def blinding_numbers():
    """The blinded Duo run against the named one, with the seal fingerprint."""
    import beam
    from beam.blinding import blind

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
    unblinded = list(seal.translate(blinded_run.tool_names))
    named_order = [run.tool_names[i] for i in np.argsort(run.result.ranks, kind="stable")]
    unblinded_order = [unblinded[i] for i in np.argsort(blinded_run.result.ranks, kind="stable")]
    identical = sum(a == b for a, b in zip(named_order, unblinded_order, strict=True))
    return {
        "n_methods": len(named_order),
        "identical_positions": identical,
        "named_order": named_order,
        "unblinded_order": unblinded_order,
        "seal_sha256_prefix": seal.fingerprint[:16],
        "seed": seal.seed,
    }


def beam_commit():
    import subprocess

    import beam

    source = Path(beam.__file__).resolve().parent
    describe = subprocess.run(
        ["git", "-C", str(source), "describe", "--tags", "--always", "--dirty"],
        capture_output=True,
        text=True,
        check=False,
    )
    return describe.stdout.strip() or None


def r_versions():
    import subprocess

    code = (
        'cat(R.version$major, ".", R.version$minor, "\\n", sep = "");'
        'for (p in c("lme4", "netmeta", "meta"))'
        ' cat(p, as.character(packageVersion(p)), "\\n")'
    )
    result = subprocess.run(["Rscript", "-e", code], capture_output=True, text=True, check=False)
    lines = result.stdout.split("\n")
    if result.returncode != 0 or not lines[0]:
        return {}
    versions = {"R": lines[0]}
    versions.update(dict(line.split() for line in lines[1:] if line.strip()))
    return versions


def software_versions():
    packages = ("beam", "numpy", "scipy", "pymcdm")
    versions = {name: metadata.version(name) for name in packages}
    versions["python"] = sys.version.split()[0]
    versions["beam_commit"] = beam_commit()
    versions.update(r_versions())
    return versions


def main() -> int:
    from beam.heterogeneity import RNotAvailableError

    numbers = {
        "software": software_versions(),
        "duo": duo_numbers(),
        "m4": m4_numbers(),
        "gptcelltype": gptcelltype_numbers(),
        "metric_sets": metric_set_numbers(),
        "blinding": blinding_numbers(),
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
