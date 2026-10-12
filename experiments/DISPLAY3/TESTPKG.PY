#!/usr/bin/env python3
"""Synthetic host packet/refusal tests. Never uses native tools or a guest.
MIT, Copyright (c) 2026 Windows XT contributors.
"""
import copy
import hashlib
import importlib.machinery
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader("display3_package", str(HERE / "PACKAGE.PY")).load_module()


class Packets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.pins = copy.deepcopy(P.PINS)
        for key, pin in self.pins["drivers"].items():
            data = ("SYNTHETIC HOST FIXTURE " + key).encode()
            (self.bin / pin["file"]).write_bytes(data)
            pin.update(bytes=len(data), sha256=P.sha(data))
        guard = self.pins["drivers"]["PCJR"]["guard"]
        data = b"SYNTHETIC GUARD FIXTURE"
        (self.bin / guard["file"]).write_bytes(data)
        guard.update(bytes=len(data), sha256=P.sha(data))
        self.launcher = b"SYNTHETIC LAUNCHER FIXTURE"
        (self.bin / "JRWIN.COM").write_bytes(self.launcher)
        self.pins["drivers"]["PCJR"]["launcher"].update(bytes=len(self.launcher),
            sha256=P.sha(self.launcher), source_sha256=P.sha(b"source"))
        self.native = dict(verdict="PASS", real_windows_cycles=2,
                           launcher_sha256=P.sha(self.launcher), launcher_source_sha256=P.sha(b"source"))
        self.rights = dict(publication_owner_authorized=True, component_notices_preserved=True,
                           record="SYNTHETIC TEST ONLY")
        self.commit = "a" * 40
        self.out = self.root / "release"

    def source(self, *args):
        files = {"src/pcjr/JRGUARD.ASM": b"source", "experiments/DISPLAY3/JRWIN.ASM": b"source"}
        own = "experiments/DISPLAY3/"
        files[own + "NATIVE.JSN"] = P.js(self.native)
        files[own + "RIGHTS.JSN"] = P.js(self.rights)
        for name in ("PC1512.TXT", "PCJR.TXT", "PCP3216.TXT", "LICENSE.TXT"):
            files[own + name] = b"source"
        files["SOURCE.JSN"] = P.js(dict(runtime_source_commit=self.pins["runtime_source_commit"],
            release_source_commit=self.commit, files={n: P.sha(d) for n, d in files.items()}))
        files["README.TXT"] = b"SYNTHETIC TEST ONLY"
        return files

    def build(self, out=None):
        with patch.object(P, "PINS", self.pins), patch.object(P, "read_blob", return_value=b"source"), \
                patch.object(P, "source_members", side_effect=self.source):
            return P.build(self.bin, self.root, self.root, self.commit, self.native, self.rights, out or self.out)

    def verify(self, publication=False):
        with patch.object(P, "PINS", self.pins):
            return P.verify(self.out, publication)

    def sums(self):
        (self.out / "SHA256SUMS").write_bytes("".join(P.sha(p.read_bytes()) + "  " + p.name + "\n"
            for p in sorted(self.out.iterdir()) if p.name != "SHA256SUMS").encode())

    def test_deterministic_runtime_and_source_archives(self):
        self.build()
        second = self.root / "second"
        self.build(second)
        self.assertEqual({p.name: p.read_bytes() for p in self.out.iterdir()},
                         {p.name: p.read_bytes() for p in second.iterdir()})
        self.assertTrue(self.verify(True)["publication_allowed"])

    def test_wrong_driver_or_guard_hash_refused_before_output(self):
        for name in ("PC1512.DRV", "JRGUARD.COM", "JRWIN.COM"):
            old = (self.bin / name).read_bytes()
            (self.bin / name).write_bytes(old + b"damage")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "identity mismatch"):
                self.build()
            self.assertFalse(self.out.exists())
            (self.bin / name).write_bytes(old)

    def test_launcher_source_or_binary_mismatch_refused(self):
        self.native["launcher_source_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "launcher binary/source"):
            self.build()

    def test_existing_output_refused(self):
        self.out.mkdir()
        with self.assertRaisesRegex(ValueError, "fresh"):
            self.build()

    def test_no_publication_without_native_windows_cycles(self):
        self.native["real_windows_cycles"] = 0
        self.build()
        with self.assertRaisesRegex(ValueError, "unresolved"):
            self.verify(True)

    def test_no_publication_without_owner_authorization_and_notices(self):
        self.rights = {}
        self.build()
        with self.assertRaisesRegex(ValueError, "unresolved"):
            self.verify(True)

    def test_extra_owned_media_refused(self):
        self.build()
        (self.out / "WIN.COM").write_bytes(b"not allowed")
        self.sums()
        with self.assertRaisesRegex(ValueError, "unexpected release"):
            self.verify()

    def test_changed_runtime_refused_even_after_checksums_refresh(self):
        self.build()
        archive = self.out / "PC1512.ZIP"
        members = P.zip_members(archive)
        members["PC1512.DRV"] += b"damage"
        P.zip_bytes(archive, members)
        self.sums()
        with self.assertRaisesRegex(ValueError, "runtime allowlist/pin"):
            self.verify()

    def test_unapproved_runtime_member_refused(self):
        self.build()
        archive = self.out / "PCJR.ZIP"
        members = P.zip_members(archive)
        members["JRHOLDT.COM"] = b"emulator-only negative helper"
        P.zip_bytes(archive, members)
        self.sums()
        with self.assertRaisesRegex(ValueError, "runtime allowlist"):
            self.verify()

    def test_runtime_metadata_and_notice_cannot_drift_from_source(self):
        for name in ("PINS.JSN", "NOTICE.TXT", "README.TXT"):
            self.out = self.root / (name + "-release")
            self.build()
            archive = self.out / "PC1512.ZIP"
            members = P.zip_members(archive)
            if name == "PINS.JSN":
                metadata = json.loads(members[name])
                metadata["release_source_commit"] = "b" * 40
                members[name] = P.js(metadata)
            else:
                members[name] += b"unbound change"
            members["SHA256.SUM"] = "".join(P.sha(d) + "  " + n + "\r\n"
                for n, d in sorted(members.items()) if n != "SHA256.SUM").encode()
            P.zip_bytes(archive, members)
            self.sums()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "identity mismatch|binding mismatch"):
                self.verify()

    def test_native_record_must_match_committed_companion(self):
        self.build()
        path = self.out / "QUALIFY.JSON"
        data = json.loads(path.read_bytes())
        data["native"]["real_windows_cycles"] = 3
        path.write_bytes(P.js(data))
        self.sums()
        with self.assertRaisesRegex(ValueError, "qualification/source binding"):
            self.verify()

    def test_noncanonical_archive_names_refused_by_writer_and_reader(self):
        for name in ("../EVIL.PY", "/EVIL.PY", "C:/EVIL.PY", "a/../EVIL.PY",
                     "a/./EVIL.PY", "a//EVIL.PY", "a\\EVIL.PY", "a/"):
            archive = self.root / "unsafe.zip"
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "unsafe archive path"):
                P.zip_bytes(archive, {name: b"SYNTHETIC TEST ONLY"})
            # Adversarial ZIP construction bypasses the safe publisher writer.
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as z:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.filename = name  # Preserve adversarial native separators.
                info.create_system, info.external_attr = 0, 0x20
                z.writestr(info, b"SYNTHETIC TEST ONLY")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "unsafe archive path"):
                P.zip_members(archive)

    def test_source_traversal_refused_after_manifest_and_checksums_refresh(self):
        self.build()
        archive = self.out / "DISP3SRC.ZIP"
        members = P.zip_members(archive)
        members["../EVIL.PY"] = b"SYNTHETIC TEST ONLY"
        manifest = json.loads(members["SOURCE.JSN"])
        manifest["files"]["../EVIL.PY"] = P.sha(members["../EVIL.PY"])
        members["SOURCE.JSN"] = P.js(manifest)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as z:
            for name, data in sorted(members.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system, info.external_attr = 0, 0x20
                z.writestr(info, data)
        self.sums()
        with self.assertRaisesRegex(ValueError, "unsafe archive path"):
            self.verify(True)

    def test_txt40_tga2_and_private_source_inputs_refused(self):
        for name in ("src/txt40/NEW.ASM", "src/tga2/T2PROBE.ASM", "DDK/README.TXT", "WINDOWS/WIN.COM"):
            out = self.root / (str(len(list(self.root.iterdir()))) + "release")
            self.out = out
            self.build()
            archive = out / "DISP3SRC.ZIP"
            members = P.zip_members(archive)
            members[name] = b"not allowed"
            P.zip_bytes(archive, members)
            self.sums()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "unapproved source"):
                self.verify()

    def test_changed_source_and_forged_permission_flag_refused(self):
        self.build()
        archive = self.out / "DISP3SRC.ZIP"
        members = P.zip_members(archive)
        members["src/pcjr/JRGUARD.ASM"] += b"damage"
        P.zip_bytes(archive, members)
        self.sums()
        with self.assertRaisesRegex(ValueError, "source manifest"):
            self.verify()
        self.out = self.root / "fresh"
        self.rights = {}
        self.build()
        path = self.out / "QUALIFY.JSON"
        q = json.loads(path.read_bytes())
        q["publication_allowed"] = True
        path.write_bytes(P.js(q))
        self.sums()
        with self.assertRaisesRegex(ValueError, "permission flag"):
            self.verify(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
