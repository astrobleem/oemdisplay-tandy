#!/usr/bin/env python3
"""Host regression tests for T2RESV mutation acceptance; no emulator.

Usage: python3 -B src/tga2/T2RTEST.PY
Saved DOS results are checked as recorded, without claiming a guest rerun.
"""
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = importlib.machinery.SourceFileLoader(
    "t2resv_harness", str(HERE / "T2RESV.PY")).load_module()


def main():
    passed, failed = [], []

    def expect(label, got, want):
        ok = got == want
        print(("ok   " if ok else "FAIL ") + label)
        (passed if ok else failed).append(label)

    for name, expected in R.MUTATIONS.items():
        expect(name + ": expected names are unique",
               len(expected) == len(set(expected)), True)
        for label, failures, caught in (
                ("expected only", expected, True),
                ("missing expected", expected[:-1], False),
                ("extra unexpected", expected + ["unrelated failure"], False),
                ("no failures", [], False),
                ("duplicate expected", expected + [expected[0]], False)):
            expect(name + ": " + label,
                   R.mutation_caught(name, failures), caught)

    expect("no_gate: failure order does not matter",
           R.mutation_caught("no_gate", R.MUTATIONS["no_gate"][::-1]), True)
    saved = json.loads((HERE.parents[1] / "docs/tga2/T2RMUT.JSN").read_bytes())
    for name in R.MUTATIONS:
        expect(name + ": recorded DOS failures satisfy exact acceptance",
               R.mutation_caught(name, saved[name]["failed"]), True)

    print(f"T2RTEST: {len(passed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
