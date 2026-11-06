"""Focused host checks for the private HPXY bounds builder; no guest execution."""
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
BUILDER = runpy.run_path(str(Path(__file__).with_name("BLDBNDS.PY")))
BOUNDS = runpy.run_path(str(ROOT / "src/hpxydib/HPBOUNDS.PY"))
SOURCE = None
EXPECTED = "aacd9f95ab0263b1a66fbb38db35f50587c06e9b463146c7280f33a0d81e95f5"


class Bounds(unittest.TestCase):
    def test_exact_qualified_transform_and_inverse(self):
        self.assertTrue(BOUNDS["selftest"](SOURCE)["inverse"])
        self.assertEqual(hashlib.sha256(BOUNDS["transform"](SOURCE)).hexdigest(), EXPECTED)

    def test_port_changes_only_the_staged_wrapper(self):
        with tempfile.TemporaryDirectory() as name:
            renderer = Path(name)
            (renderer / "EGA").mkdir()
            target = renderer / "EGA/TSOFT.ASM"
            target.write_bytes(SOURCE)
            cursor = renderer / "EGA/TCURSOR.ASM"
            cursor.write_bytes(b"unchanged cursor\r\n")
            result = BOUNDS["port"](renderer)
            self.assertEqual(result["added_data_bytes"], 0)
            self.assertEqual(target.read_bytes(), BOUNDS["transform"](SOURCE))
            self.assertEqual(cursor.read_bytes(), b"unchanged cursor\r\n")

    def pipeline(self, fail=False, calls=1, batch=False):
        seen = []
        module = SimpleNamespace(patch=lambda *a, **kw: seen.append("XR"))
        dib = SimpleNamespace(patch=lambda *a: seen.append("DIB"))

        def port(*args):
            seen.append("bounds")
            if fail:
                raise ValueError("source rejected")
            return {"output_columns": True, "text_columns": True}

        def main():
            loaded = importlib.machinery.SourceFileLoader("xypatch", "unused").load_module()
            for _ in range(calls):
                loaded.patch(Path("unused"), batch=batch)

        with patch.object(importlib.machinery.SourceFileLoader, "load_module",
                          return_value=module) as original:
            try:
                result = BUILDER["build"](SimpleNamespace(main=main), dib,
                                          SimpleNamespace(port=port))
            finally:
                self.assertIs(importlib.machinery.SourceFileLoader.load_module, original)
        return seen, result

    def test_pipeline_order_and_loader_restoration(self):
        seen, result = self.pipeline()
        self.assertEqual(seen, ["XR", "DIB", "bounds"])
        self.assertTrue(result["output_columns"] and result["text_columns"])

    def test_source_failure_restores_loader(self):
        with self.assertRaisesRegex(ValueError, "source rejected"):
            self.pipeline(fail=True)

    def test_missing_duplicate_and_batched_stage_refused(self):
        with self.assertRaisesRegex(RuntimeError, "exactly once"):
            self.pipeline(calls=0)
        for options in ({"calls": 2}, {"batch": True}):
            with self.assertRaisesRegex(ValueError, "non-batched"):
                self.pipeline(**options)
        for arg in ("--batch", "--sync-output"):
            with patch.object(sys, "argv", ["BLDBNDS.PY", arg]):
                with self.assertRaisesRegex(ValueError, "original XY cursor"):
                    self.pipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True,
                        help="Exact staged baseline TSOFT.ASM, not a driver binary")
    args = parser.parse_args()
    SOURCE = args.baseline.read_bytes()
    unittest.main(argv=[sys.argv[0]])
