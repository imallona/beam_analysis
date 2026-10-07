"""Compare two numbers.json files, leaving out the software versions.

    python tools/compare_numbers.py committed.json results/numbers.json

Floats are equal within a relative tolerance, because the mixed models and
the network meta-analysis give slightly different values with other versions
of R, lme4 or the linear algebra library. Every differing path is printed.
The exit status is 1 when there is one.
"""

import json
import math
import sys

RELATIVE_TOLERANCE = 1e-3
ABSOLUTE_TOLERANCE = 1e-6
IGNORED = ("software", "warnings")


def differences(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key in IGNORED:
                continue
            if key not in a or key not in b:
                yield f"{path}/{key}: only in one file"
            else:
                yield from differences(a[key], b[key], f"{path}/{key}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield f"{path}: length {len(a)} against {len(b)}"
        else:
            for i, (x, y) in enumerate(zip(a, b, strict=True)):
                yield from differences(x, y, f"{path}/{i}")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not math.isclose(a, b, rel_tol=RELATIVE_TOLERANCE, abs_tol=ABSOLUTE_TOLERANCE):
            yield f"{path}: {a} against {b}"
    elif a != b:
        yield f"{path}: {a!r} against {b!r}"


def main(committed_path, rebuilt_path):
    with open(committed_path, encoding="utf-8") as handle:
        committed = json.load(handle)
    with open(rebuilt_path, encoding="utf-8") as handle:
        rebuilt = json.load(handle)
    found = list(differences(committed, rebuilt))
    for line in found:
        print(line)
    print(f"{len(found)} difference(s)")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
