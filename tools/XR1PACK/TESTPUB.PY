"""Synthetic host tests for the local XR1 release publisher; no guest/media use."""
import copy
import hashlib
import importlib.machinery
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

P = importlib.machinery.SourceFileLoader(
    "xr1_local_publish", str(Path(__file__).with_name("PUBLISH.PY"))).load_module()
COMMIT = "0123456789abcdef0123456789abcdef01234567"


def ident(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="xr1-publish-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "XR1PACK"
        self.root.mkdir()
        self.payload = self.root / "PAYLOAD"
        self.mine = self.root / "MINE"
        self.payload.mkdir()
        self.mine.mkdir()
        self.payload_data = {}
        for index in range(1, 48):
            leaf = "HPXY.DRV" if index == 1 else "TNDYK3.DRV" if index == 2 else "RT%02d.EXE" % index
            data = ("runtime-" + leaf).encode("ascii")
            (self.payload / leaf).write_bytes(data)
            self.payload_data[leaf] = data
        self.mine_data = {
            "WINMINE.EXE": b"converted synthetic mine executable",
            "WMABT.DLL": b"synthetic about module",
            "README.TXT": b"mine readme\r\n",
            "NOTICE.TXT": b"mine notice\r\n",
            "QUALIFY.JSN": b"{}\r\n",
            "SHA256S.TXT": b"mine checksum\r\n",
        }
        for name, data in self.mine_data.items():
            (self.mine / name).write_bytes(data)
        P.MINE_PINS = {
            "WINMINE.EXE": hashlib.sha256(self.mine_data["WINMINE.EXE"]).hexdigest(),
            "WMABT.DLL": hashlib.sha256(self.mine_data["WMABT.DLL"]).hexdigest(),
        }
        self.files = {
            "PREPARE.PY": b"# synthetic validated preparation tool\r\n",
            "WHEELLIC.TXT": b"Synthetic license notice.\r\n",
            "WHEELPRO.TXT": b"Synthetic provenance note.\r\n",
            "OWATCOM.TXT": b"Synthetic toolchain note.\r\n",
            "PROVENANCE.JSN": b"{}\r\n",
            "README.TXT": b"Private XR1 local release test.\r\n",
            "NOTICE.TXT": (b"HPXY.DRV and TNDYK3.DRV are adapted from Microsoft DDK code. "
                           b"No public redistribution license is asserted.\r\n"),
        }
        for name, data in self.files.items():
            (self.root / name).write_bytes(data)
        self.inputs = {
            "schema": 1,
            "files": [
                {"path": "W30/WIN.COM", "origin": "windows", "bytes": 4,
                 "sha256": hashlib.sha256(b"OS!!").hexdigest()},
                {"path": "WINXT/SETUP.INF", "origin": "generated", "bytes": 5,
                 "sha256": hashlib.sha256(b"setup").hexdigest()},
                {"path": "WINXT/HPXY.DRV", "origin": "drivers", "bytes": 1,
                 "sha256": hashlib.sha256(b"x").hexdigest()},
            ],
        }
        (self.root / "INPUTS.JSN").write_text(json.dumps(self.inputs), encoding="utf-8")
        self.files["INPUTS.JSN"] = (self.root / "INPUTS.JSN").read_bytes()
        self.qual = {
            "schema": 1,
            "status": "PASS_HOST_AND_NATIVE",
            "physical_qualification": False,
            "native": {
                key: {"status": "PASS", "run_id": key + "-run",
                      "owned_process_stopped": True, "lease_released": True}
                for key in ("fresh", "update")
            },
            "tested_source_pins": {},
            "runtime_pins": {},
            "minesweeper": {"status": "PASS_HOST_AND_NATIVE", "files": {}},
        }
        for name, data in self.payload_data.items():
            self.qual["runtime_pins"][name] = ident(data)
        for name, data in self.mine_data.items():
            self.qual["minesweeper"]["files"][name] = ident(data)
        self.files.update({
            "NOTICE.TXT": self.files["NOTICE.TXT"],
            "PREPARE.PY": self.files["PREPARE.PY"],
            "README.TXT": self.files["README.TXT"],
        })
        self.refresh()

    def refresh(self):
        self.qual["tested_source_pins"] = {
            "PREPARE.PY": hashlib.sha256(self.files["PREPARE.PY"]).hexdigest(),
            "INPUTS.JSN": hashlib.sha256((self.root / "INPUTS.JSN").read_bytes()).hexdigest(),
        }
        self.files["INPUTS.JSN"] = (self.root / "INPUTS.JSN").read_bytes()
        qual_data = json.dumps(self.qual, sort_keys=True).encode("utf-8")
        (self.root / "QUALIFY.JSN").write_bytes(qual_data)
        self.files["QUALIFY.JSN"] = qual_data
        for name, data in self.payload_data.items():
            self.files["PAYLOAD/" + name] = data
        for name, data in self.mine_data.items():
            self.files["MINE/" + name] = data
        public_files = {name: ident(data) for name, data in self.files.items()}
        win_map = {name: name for name in P.DOCS}
        win_map.update({"WINXT/" + name: "PAYLOAD/" + name for name in self.payload_data})
        mine_map = {"WINMINE30/" + name: "MINE/" + name for name in self.mine_data}
        self.public = {"schema": 1, "tag": "v0.1.0-rc.8", "files": public_files,
                       "bundles": {"WINXT-XR1.ZIP": win_map, "WINMINE30.ZIP": mine_map}}
        (self.root / "PUBLIC.JSN").write_text(json.dumps(self.public), encoding="utf-8")
        (self.root / "PUBLISH.PY").write_bytes(Path(P.__file__).read_bytes())

    def test_publish_verify_closed_six_assets_and_reproducible_zips(self):
        out1, out2 = self.root.parent / "release-one", self.root.parent / "release-two"
        first = P.publish(out1, COMMIT, self.root)
        P.verify(out1, COMMIT, self.root)
        second = P.publish(out2, COMMIT, self.root)
        self.assertEqual(set(first), set(P.ASSETS))
        self.assertEqual(first, second)
        self.assertEqual(sorted(p.name for p in out1.iterdir()), sorted(P.ASSETS))
        self.assertEqual((out1 / "START-HERE.TXT").read_bytes(), self.files["README.TXT"])
        self.assertEqual((out1 / "WINXT-XR1.ZIP").read_bytes(), (out2 / "WINXT-XR1.ZIP").read_bytes())
        self.assertEqual((out1 / "WINMINE30.ZIP").read_bytes(), (out2 / "WINMINE30.ZIP").read_bytes())
        release = json.loads((out1 / "RELEASE.JSON").read_text(encoding="ascii"))
        self.assertEqual((release["tag"], release["commit"]), ("v0.1.0-rc.8", COMMIT))
        self.assertFalse(release["physical_qualification"])
        for archive in ("WINXT-XR1.ZIP", "WINMINE30.ZIP"):
            with zipfile.ZipFile(out1 / archive) as zf:
                self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in zf.infolist()))

    def test_refuses_existing_output_without_overwriting(self):
        out = self.root.parent / "existing"
        out.mkdir()
        (out / "KEEP.TXT").write_bytes(b"keep")
        with self.assertRaises(P.Refused):
            P.publish(out, COMMIT, self.root)
        self.assertEqual([p.name for p in out.iterdir()], ["KEEP.TXT"])
        self.assertEqual((out / "KEEP.TXT").read_bytes(), b"keep")

    def test_preflight_hash_mismatch_does_not_create_output(self):
        (self.payload / "RT03.EXE").write_bytes(b"changed")
        out = self.root.parent / "must-not-exist"
        with self.assertRaises(P.Refused):
            P.publish(out, COMMIT, self.root)
        self.assertFalse(out.exists())

    def test_verify_rejects_extra_asset_and_tampered_checksum(self):
        out = self.root.parent / "verify"
        P.publish(out, COMMIT, self.root)
        (out / "EXTRA.TXT").write_bytes(b"extra")
        with self.assertRaises(P.Refused):
            P.verify(out, COMMIT, self.root)
        (out / "EXTRA.TXT").unlink()
        (out / "SHA256SUMS").write_bytes(b"tampered\r\n")
        with self.assertRaises(P.Refused):
            P.verify(out, COMMIT, self.root)

    def test_rejects_windows_bytes_in_runtime_payload(self):
        banned = b"OS!!"
        self.payload_data["RT03.EXE"] = banned
        (self.payload / "RT03.EXE").write_bytes(banned)
        self.inputs["files"].append({"path": "W30/OTHER.EXE", "origin": "windows",
                                     "bytes": len(banned), "sha256": hashlib.sha256(banned).hexdigest()})
        (self.root / "INPUTS.JSN").write_text(json.dumps(self.inputs), encoding="utf-8")
        self.files["INPUTS.JSN"] = (self.root / "INPUTS.JSN").read_bytes()
        self.qual["runtime_pins"]["RT03.EXE"] = ident(banned)
        self.refresh()
        with self.assertRaisesRegex(P.Refused, "overlap original/generated"):
            P.collect(self.root, COMMIT)

    def test_rejects_qualification_cleanup_failure(self):
        self.qual["native"]["update"]["lease_released"] = False
        self.refresh()
        with self.assertRaisesRegex(P.Refused, "cleanup is incomplete"):
            P.collect(self.root, COMMIT)

    def test_rejects_archive_path_case_collision(self):
        self.public["bundles"]["WINXT-XR1.ZIP"]["prepare.py"] = "README.TXT"
        (self.root / "PUBLIC.JSN").write_text(json.dumps(self.public), encoding="utf-8")
        with self.assertRaisesRegex(P.Refused, "(?i)case-colliding"):
            P.collect(self.root, COMMIT)

    def test_rejects_changed_minesweeper_binary_pin(self):
        self.mine_data["WINMINE.EXE"] = b"changed mine binary"
        (self.mine / "WINMINE.EXE").write_bytes(self.mine_data["WINMINE.EXE"])
        self.refresh()
        with self.assertRaisesRegex(P.Refused, "Minesweeper packet mismatch"):
            P.collect(self.root, COMMIT)

    def test_rejects_noncanonical_or_partial_commit(self):
        for value in ("abc", "0" * 41, "z" * 40):
            with self.subTest(commit=value), self.assertRaises(P.Refused):
                P.collect(self.root, value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
