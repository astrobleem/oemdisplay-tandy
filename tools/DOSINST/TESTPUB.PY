"""Native rc.8 archive closure and qualification-gate regression checks."""
import copy
import importlib.machinery
import json
import io
import zipfile
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

M = importlib.machinery.SourceFileLoader("native_rc8_publish", str(Path(__file__).with_name("RCPUB.PY"))).load_module()
COMMIT = "0123456789abcdef0123456789abcdef01234567"

class NativePublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entries = M.collect()
        self.archive = M.pub.zip_bytes(self.entries)
        self.qual = {"status": "PASS_NATIVE_AND_HOST", "physical_test": False,
                     "public_assets": {"WINXT.ZIP": M.pub.identity(self.archive),
                     "WINXT.EXE": M.pub.identity(self.entries["PREPXR.EXE"] + self.archive)},
                     "cold": {"complete": True, "owned_stopped": True, "lease_released": True}}
        for mode, count in (("fresh", 367), ("update", 80)):
            self.qual[mode] = {"complete": True, "owned_stopped": True, "lease_released": True,
                              "prepared_comparison": {"count": count, "different": []}}
        self.qual["input_validation"] = {
            "helper": M.pub.identity(self.entries["PREPXR.EXE"]),
            "native_corruption": copy.deepcopy(self.qual["cold"]),
            "native_valid_inputs": copy.deepcopy(self.qual["fresh"])}
        self.receipt = self.root / "docs/QUAL/DOSINST/RC8.JSN"
        self.receipt.parent.mkdir(parents=True)

    def run_build(self, output, verify=False):
        self.receipt.write_text(json.dumps(self.qual), encoding="ascii")
        with patch.object(M, "REPO", self.root), patch.object(M, "collect", return_value=self.entries):
            return M.build(output, COMMIT, verify)

    def test_closed_native_archive(self):
        self.assertEqual(len(self.entries), 53)
        self.assertFalse(any(n.endswith(".PY") for n in self.entries))
        self.assertEqual(M.pub.identity(self.entries["PAYLOAD/CGA.GR2"]), {"bytes": 2104, "sha256": "1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067"})
        M.pub.check_zip(self.archive, self.entries, "native")
        self.assertEqual(self.archive, M.pub.zip_bytes(self.entries))

    def test_recipe_uses_bundled_grabber_for_both_output_trees(self):
        import re
        rows = re.findall(r'\{"([^"\n]+)","([^"\n]+)",(\d+)UL,(\d+)\}',
                          (M.HERE / "XRFILES.H").read_text())
        grabbers = [(path, source, int(size), int(kind))
                    for path, source, size, kind in rows if source == "CGA.GR2"]
        self.assertEqual(len(grabbers), 3)
        self.assertTrue(all(size == 2104 and kind == 0 for _, _, size, kind in grabbers))
        for _, source, size, _ in grabbers:
            self.assertEqual(len(self.entries["PAYLOAD/" + source]), size)

    def test_windows_crc_inventory_matches_qualified_inputs(self):
        recipe = (M.HERE / "XRFILES.H").read_text()
        header = (M.HERE / "XRINPUT.H").read_text()
        pins = json.loads((M.HERE / "XRINPUT.JSN").read_bytes())
        qualified = {r["path"]: r for r in json.loads((M.HERE.parent / "XR1PACK/INPUTS.JSN").read_bytes())["files"]}
        self.assertEqual(len(pins), 284)
        M.check_inputs(recipe, header, pins, qualified)
        changed = copy.deepcopy(pins)
        changed["W30/123.PIF"]["crc32"] = "00000000"
        with self.assertRaises(ValueError):
            M.check_inputs(recipe, header, changed, qualified)
        changed = copy.deepcopy(pins)
        changed["W30/123.PIF"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            M.check_inputs(recipe, header, changed, qualified)
        with self.assertRaises(ValueError):
            M.check_inputs(recipe, header.replace("W30\\\\123.PIF", "wrong", 1), pins, qualified)

    def test_verified_assets_and_overlay(self):
        output = self.root / "release"
        first = self.run_build(output)
        self.assertEqual(first, self.run_build(output, True))
        self.assertEqual(set(p.name for p in output.iterdir()), set(M.ASSETS))
        self.assertEqual((output / "WINXT.EXE").read_bytes(), self.entries["PREPXR.EXE"] + self.archive)

    def test_download_zip_extracts_the_qualified_ready_to_run_exe(self):
        output = self.root / "wrapped"
        self.run_build(output)
        body = (output / "WINXTDOS.ZIP").read_bytes()
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            self.assertEqual(zf.namelist(), ["README.TXT", "WINXT.EXE"])
            self.assertIsNone(zf.testzip())
            self.assertEqual(zf.read("WINXT.EXE"), (output / "WINXT.EXE").read_bytes())
            self.assertEqual(zf.read("WINXT.EXE"), self.entries["PREPXR.EXE"] + self.archive)
            self.assertEqual(zf.read("README.TXT"), (M.HERE / "WRAP.TXT").read_bytes())
            self.assertNotIn("PREPXR", zf.read("README.TXT").decode("ascii"))
            self.assertNotIn(b"\r\r\n", zf.read("README.TXT"))
            self.assertNotIn(b"\n", zf.read("README.TXT").replace(b"\r\n", b""))
        report = json.loads((output / "RELEASE.JSON").read_bytes())
        self.assertEqual(report["download_archive"]["executable"], M.pub.identity((output / "WINXT.EXE").read_bytes()))
        self.assertEqual(report["download_archive"]["sha256"], M.pub.identity(body)["sha256"])
        self.assertEqual(body, M.download_zip((output / "WINXT.EXE").read_bytes()))
        # Reject either altered delivery member and altered outer metadata on verification.
        for member in ("WINXT.EXE", "README.TXT"):
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                entries = {name: zf.read(name) for name in zf.namelist()}
            entries[member] += b"changed"
            (output / "WINXTDOS.ZIP").write_bytes(M.pub.zip_bytes(entries))
            with self.assertRaises(ValueError):
                self.run_build(output, True)
        (output / "WINXTDOS.ZIP").write_bytes(body + b"changed")
        with self.assertRaises(ValueError):
            self.run_build(output, True)

    def test_wrong_or_incomplete_native_result_refused_before_output(self):
        original = copy.deepcopy(self.qual)
        for mutate in (lambda q: q["fresh"].update(complete=False),
                       lambda q: q["fresh"].update(error="Setup did not finish"),
                       lambda q: q["update"].update(lease_released=False),
                       lambda q: q["cold"].update(owned_stopped=False),
                       lambda q: q["update"]["prepared_comparison"].update(different=["WINXT/HPXY.DRV"]),
                       lambda q: q["fresh"]["prepared_comparison"].update(count=366),
                       lambda q: q["input_validation"]["helper"].update(sha256="0" * 64),
                       lambda q: q["input_validation"]["native_corruption"].update(complete=False),
                       lambda q: q["input_validation"]["native_valid_inputs"].update(error="CRC did not finish")):
            self.qual = copy.deepcopy(original)
            mutate(self.qual)
            output = self.root / "refused"
            with self.assertRaises(ValueError):
                self.run_build(output)
            self.assertFalse(output.exists())

    def test_changed_qualified_container_refused(self):
        self.qual["public_assets"]["WINXT.ZIP"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.run_build(self.root / "bad")

    def test_extra_or_modified_asset_refused(self):
        output = self.root / "release"
        self.run_build(output)
        (output / "EXTRA.TXT").write_bytes(b"extra")
        with self.assertRaises(ValueError):
            self.run_build(output, True)
        (output / "EXTRA.TXT").unlink()
        (output / "WINXT.EXE").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.run_build(output, True)

if __name__ == "__main__":
    unittest.main()
