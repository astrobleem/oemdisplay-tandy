"""Host-only preparation boundary tests; synthetic media, no Microsoft files."""
import copy
import importlib.machinery
from pathlib import Path
import struct
import tempfile
import unittest

M = importlib.machinery.SourceFileLoader("xr1prepare", str(Path(__file__).with_name("PREPARE.PY"))).load_module()


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="xr1-prepare-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.media, self.components, self.drivers = [self.root / x for x in ("MEDIA", "PAYLOAD", "DRIVERS")]
        for p in (self.media, self.components, self.drivers):
            p.mkdir()
        self.original = b"one\r\n\xa3 owner bytes\r\n"
        self.modified = b"one\r\nproject row\r\n\xa3 owner bytes\r\n"
        self.cnf = b"owned-loader"
        self.logo = b"project-logo"
        for name, data in (("SETUP.INF", self.original), ("WIN.CNF", self.cnf), ("ZERO.TXT", b"")):
            (self.media / name).write_bytes(data)
        (self.components / "XTLOGO.LGO").write_bytes(self.logo)
        (self.components / "APP.EXE").write_bytes(b"project-app")
        (self.drivers / "HPXY.DRV").write_bytes(b"adapted-driver")
        outputs = {
            "W30/ZERO.TXT": (b"", "windows"),
            "WINXT/APP.EXE": (b"project-app", "components"),
            "WINXT/HPXY.DRV": (b"adapted-driver", "drivers"),
            "WINXT/SETUP.INF": (self.modified, "generated"),
            "WINXT/CNF.PIN": (self.cnf, "generated"),
            "WINXT/XTTEST.COM": (self.cnf + self.logo, "generated"),
        }
        self.manifest = {
            "schema": 1, "profile": "XR1",
            "files": [{"path": n, "origin": origin, **M.identity(data)} for n, (data, origin) in outputs.items()],
            "output_counts": {"fresh": 6, "update": 5},
            "win_cnf": M.identity(self.cnf), "xtlogo": M.identity(self.logo),
            "setup_recipe": {
                "input": M.identity(self.original), "output": M.identity(self.modified),
                "operations": [{"copy": [0, 5]}, {"insert": "project row\r\n"}, {"copy": [5, len(self.original)]}],
            },
        }

    def run_prepare(self, mode="fresh", output=None):
        return M.prepare(self.media, self.components, self.drivers, output or self.root / "OUT", mode, self.manifest)

    def refused_without_output(self, mode="fresh"):
        with self.assertRaises((M.Refused, OSError, KeyError)):
            self.run_prepare(mode)
        self.assertFalse((self.root / "OUT").exists())

    def test_fresh_preserves_inputs_and_generates_exact_owned_files(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for root in (self.media, self.components, self.drivers) for p in root.iterdir()}
        result = self.run_prepare()
        self.assertEqual(len(result["files"]), 6)
        self.assertEqual((self.root / "OUT/DOS-CROOT/WINXT/XTTEST.COM").read_bytes(), self.cnf + self.logo)
        self.assertEqual((self.root / "OUT/DOS-CROOT/WINXT/SETUP.INF").read_bytes(), self.modified)
        self.assertFalse(result["redistributable_output"])
        self.assertFalse(result["new_native_test"])
        for name, data in before.items():
            self.assertEqual((self.root / name).read_bytes(), data)

    def test_update_omits_setup_media(self):
        result = self.run_prepare("update")
        self.assertEqual(len(result["files"]), 5)
        self.assertFalse((self.root / "OUT/DOS-CROOT/W30").exists())

    def test_update_does_not_require_fresh_media(self):
        (self.media / "ZERO.TXT").unlink()
        self.assertEqual(self.run_prepare("update")["status"], "PASS_HOST_XR1_PREPARATION")

    def test_missing_windows_input_refused(self):
        (self.media / "WIN.CNF").unlink()
        self.refused_without_output()

    def test_wrong_loader_refused(self):
        (self.media / "WIN.CNF").write_bytes(b"wrong-loader")
        self.refused_without_output()

    def test_same_size_driver_corruption_refused(self):
        (self.drivers / "HPXY.DRV").write_bytes(b"adapted-driveX")
        self.refused_without_output()

    def test_wrong_component_refused(self):
        (self.components / "APP.EXE").write_bytes(b"other-app")
        self.refused_without_output()

    def test_modified_setup_source_refused(self):
        (self.media / "SETUP.INF").write_bytes(self.modified)
        self.refused_without_output()

    def test_wrong_setup_copy_range_refused(self):
        self.manifest["setup_recipe"]["operations"][0] = {"copy": [-1, 5]}
        self.refused_without_output()

    def test_backward_setup_copy_refused(self):
        self.manifest["setup_recipe"]["operations"][-1] = {"copy": [0, 5]}
        self.refused_without_output()

    def test_wrong_generated_hash_refused(self):
        self.manifest["setup_recipe"]["output"]["sha256"] = "0" * 64
        self.refused_without_output()

    def test_text_after_first_of_multiple_dos_eof_markers_refused(self):
        bad = b"header\r\n\x1a\r\n; misplaced padding\r\n\x1a\r\n"
        recipe = {"input": M.identity(self.original), "output": M.identity(bad),
                  "operations": [{"insert": bad.decode("ascii")}]}
        with self.assertRaisesRegex(M.Refused, "follows DOS EOF"):
            M.setup_inf(self.original, recipe)

    def test_padding_before_all_dos_eof_markers_accepted(self):
        good = b"header\r\n; inert padding\r\nswe = example\r\n" + b"\x1a\r\n" * 7
        recipe = {"input": M.identity(self.original), "output": M.identity(good),
                  "operations": [{"insert": good.decode("ascii")}]}
        self.assertEqual(M.setup_inf(self.original, recipe), good)

    def test_manifest_traversal_refused(self):
        self.manifest["files"][0]["path"] = "../ESCAPE.TXT"
        self.refused_without_output()

    def test_manifest_absolute_path_refused(self):
        self.manifest["files"][0]["path"] = "C:/ESCAPE.TXT"
        self.refused_without_output()

    def test_duplicate_fresh_path_refused(self):
        self.manifest["files"].append(copy.deepcopy(self.manifest["files"][0]))
        self.refused_without_output()

    def test_duplicate_skipped_update_path_refused(self):
        self.manifest["files"].append(copy.deepcopy(self.manifest["files"][0]))
        self.refused_without_output("update")

    def test_existing_output_preserved(self):
        out = self.root / "OUT"
        out.mkdir()
        (out / "KEEP.TXT").write_bytes(b"preserve")
        with self.assertRaises(M.Refused):
            self.run_prepare(output=out)
        self.assertEqual((out / "KEEP.TXT").read_bytes(), b"preserve")
        self.assertEqual(len(list(out.iterdir())), 1)

    def test_nested_output_refused(self):
        with self.assertRaises(M.Refused):
            self.run_prepare(output=self.media / "OUT")
        self.assertFalse((self.media / "OUT").exists())

    def test_wrong_declared_output_count_refused(self):
        self.manifest["output_counts"]["fresh"] += 1
        self.refused_without_output()

    def test_unknown_origin_refused(self):
        self.manifest["files"][0]["origin"] = "network"
        self.refused_without_output()

    def test_szdd_mode_a_literals(self):
        data = b"12345678"
        packed = b"SZDD\x88\xf0\x27\x33A\0" + struct.pack("<I", len(data)) + b"\xff" + data
        self.assertEqual(M.expanded_file(packed, "DATA"), data)

    def test_szdd_truncation_refused(self):
        with self.assertRaises(M.Refused):
            M.expanded_file(b"SZDD\x88\xf0\x27\x33A\0", "DATA")

    def test_szdd_trailing_data_refused(self):
        packed = b"SZDD\x88\xf0\x27\x33A\0" + struct.pack("<I", 1) + b"\1Aextra"
        with self.assertRaises(M.Refused):
            M.expanded_file(packed, "DATA")


if __name__ == "__main__":
    unittest.main()
