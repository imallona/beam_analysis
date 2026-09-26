"""Regenerate the beam manuscript figures into figures/.

Run from the repository root:

    python make_paper_figures.py            # all figures
    python make_paper_figures.py 2 6        # only figures 2 and 6

Each figure is a self-contained module under paper_figures/ exposing
build(). The figures are deterministic: every beam.rank call seeds at zero, and
the only randomness (SMAA, parallel analysis) is seeded inside beam. Figures 4
and 5 call the R toolchain (lme4, netmeta) through beam.heterogeneity; when R is
absent they are skipped with a message rather than failing the run.

Figure 1 is a Graphviz schematic (make figure1).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow running as a plain script (python make_paper_figures.py).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from paper_figures import _common as C

OUTPUT_DIR = Path(__file__).resolve().parent / "figures"

FIGURES = {
    2: ("paper_figures.figure2_duo", "figure2_duo.pdf"),
    3: ("paper_figures.figure3_domains", "figure3_domains.pdf"),
    4: ("paper_figures.figure4_integration", "figure4_integration.pdf"),
    5: ("paper_figures.figure5_attribution", "figure5_attribution.pdf"),
    6: ("paper_figures.figure6_metrics", "figure6_metrics.pdf"),
}


def _build_one(number: int, module_name: str, filename: str) -> str | None:
    import importlib

    from beam.heterogeneity import RNotAvailableError

    module = importlib.import_module(module_name)
    start = time.monotonic()
    try:
        fig = module.build()
    except RNotAvailableError as exc:
        print(f"  figure {number}: skipped, needs R ({exc})")
        return None
    path = OUTPUT_DIR / filename
    C.save_figure(fig, str(path))
    print(f"  figure {number}: {path} ({time.monotonic() - start:.1f}s)")
    return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the beam manuscript figures.")
    parser.add_argument(
        "figures",
        nargs="*",
        type=int,
        help="figure numbers to build (default: all available)",
    )
    args = parser.parse_args(argv)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    C.configure()

    wanted = args.figures or sorted(FIGURES)
    print(f"writing figures to {OUTPUT_DIR}")
    built = []
    for number in wanted:
        if number not in FIGURES:
            print(f"  figure {number}: no such figure", file=sys.stderr)
            continue
        module_name, filename = FIGURES[number]
        try:
            result = _build_one(number, module_name, filename)
        except ModuleNotFoundError:
            print(f"  figure {number}: module not present yet ({module_name})", file=sys.stderr)
            continue
        if result is not None:
            built.append(result)
    print(f"done: {len(built)} figure(s) written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
