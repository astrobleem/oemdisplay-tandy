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


class FixedBounds(unittest.TestCase):
    def load_unit_module(self, name, path):
        if name == "hpb_fixed_base":
            self.assertEqual(path, ROOT / "src/tandysw/build.py")
            return SimpleNamespace(HERE=ROOT / "src/tandysw")
        return BUILDER["_load_module"](name, path)

    def test_exact_historical_builder_and_single_insertion(self):
        source = (ROOT / "src/tandysw/BUILD88.PY").read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), BUILDER["FIXED_SOURCE_SHA256"])
        adapted = BUILDER["adapt_fixed"](source)
        self.assertEqual(adapted.count(BUILDER["FIXED_INSERT"]), 1)
        self.assertEqual(adapted.replace(BUILDER["FIXED_INSERT"], b""), source)
        self.assertLess(adapted.index(BUILDER["FIXED_INSERT"]),
                        adapted.index(b'    ui_audit = {"profile": "stock"}'))
        for bad in (b"", source + b"; changed\r\n", adapted,
                    source.replace(b"\r\n", b"\n")):
            with self.assertRaisesRegex(ValueError, "exact historical"):
                BUILDER["adapt_fixed"](bad)

    def test_matching_baseline_and_global_restoration(self):
        stale = object()
        original_path = sys.path[:]
        function = BUILDER["fixed_builder"]
        with patch.dict(sys.modules, {"build": stale}):
            with patch.dict(function.__globals__, {"_load_module": self.load_unit_module}):
                module = function()
            self.assertIs(sys.modules["build"], stale)
        self.assertEqual(sys.path, original_path)
        self.assertEqual(module.HERE, ROOT / "src/tandysw")
        self.assertEqual(module.baseline.HERE, module.HERE)

    def test_exec_failure_restores_matching_context(self):
        stale = object()
        original_path = sys.path[:]
        function = BUILDER["fixed_builder"]

        def fail(*unused):
            self.assertIsNot(sys.modules["build"], stale)
            self.assertEqual(sys.path[0], str(ROOT / "src/tandysw"))
            raise RuntimeError("fixed exec failed")

        with patch.dict(sys.modules, {"build": stale}):
            with patch.dict(function.__globals__, {
                    "exec": fail, "_load_module": self.load_unit_module}):
                with self.assertRaisesRegex(RuntimeError, "fixed exec failed"):
                    function()
            self.assertIs(sys.modules["build"], stale)
        self.assertEqual(sys.path, original_path)

    def test_fixed_callback_order_and_duplicate_rejection(self):
        function = BUILDER["fixed_builder"]
        original_load = BUILDER["_load_module"]
        seen = []

        def load(name, path):
            if name in ("hpb_fixed_output", "hpb_fixed_text"):
                def port(*unused):
                    seen.append(name)
                    return {"changed": True}
                return SimpleNamespace(port=port)
            if name == "hpb_fixed_base":
                self.assertEqual(path, ROOT / "src/tandysw/build.py")
                return SimpleNamespace(HERE=ROOT / "src/tandysw")
            return original_load(name, path)

        with patch.dict(function.__globals__, {"_load_module": load}):
            module = function()
        module._fixed_bounds(Path("unused"), "320x200x16")
        self.assertEqual(seen, ["hpb_fixed_output", "hpb_fixed_text"])
        self.assertEqual(len(module.fixed_stages), 1)
        with self.assertRaisesRegex(ValueError, "one fixed"):
            module._fixed_bounds(Path("unused"), "320x200x16")
        self.assertEqual(len(seen), 2)

    def test_fixed_route_precedes_windows_import_and_restores_argv(self):
        function = BUILDER["main"]
        argv = ["BLDBNDS.PY", "--fixed", "--out=unused"]

        def stop():
            self.assertNotIn("--fixed", sys.argv)
            raise RuntimeError("fixed route reached")

        with patch.object(sys, "argv", argv):
            with patch.dict(function.__globals__, {
                    "fixed_builder": lambda: SimpleNamespace(main=stop)}):
                with patch.object(importlib.machinery.SourceFileLoader, "load_module",
                                  side_effect=AssertionError("Windows route imported")):
                    with self.assertRaisesRegex(RuntimeError, "fixed route reached"):
                        function()
            self.assertEqual(sys.argv, argv)

    def test_hpxy_does_not_enter_fixed_builder(self):
        function = BUILDER["build"]
        with patch.dict(function.__globals__, {
                "fixed_builder": lambda: self.fail("HPXY entered fixed route")}):
            seen, result = Bounds().pipeline()
        self.assertEqual(seen, ["XR", "DIB", "bounds"])

    def test_both_output_argument_spellings(self):
        self.assertEqual(BUILDER["output_path"](["--out", "unused"]),
                         BUILDER["output_path"](["--out=unused"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True,
                        help="Exact staged baseline TSOFT.ASM, not a driver binary")
    args = parser.parse_args()
    SOURCE = args.baseline.read_bytes()
    unittest.main(argv=[sys.argv[0]])
