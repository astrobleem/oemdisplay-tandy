#!/usr/bin/env python3
"""Host regressions: actual first-party splash, synthetic Windows support files."""
import importlib.machinery
import importlib.util
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("makedisk", str(ROOT / "MAKEDISK.PY"))
spec = importlib.util.spec_from_loader(loader.name, loader)
builder = importlib.util.module_from_spec(spec)
loader.exec_module(builder)
s = builder.stage


def font_fixture():
    data = bytearray(256)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3c, 64)
    data[64:66] = b"NE"
    struct.pack_into("<HH", data, 64 + 0x24, 64, 100)
    struct.pack_into("<HHH", data, 128, 0, 0x8008, 1)
    struct.pack_into("<HH", data, 138, 192, 64)
    return bytes(data)


def compressed_fixture(data):
    body = bytearray()
    for offset in range(0, len(data), 8):
        chunk = data[offset:offset + 8]
        body.append((1 << len(chunk)) - 1)
        body.extend(chunk)
    return b"SZDD\x88\xf0\x27\x33A\x00" + struct.pack("<I", len(data)) + body


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="oemdisk-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        for name in ("STAGE.PY", "oemsetup.inf", "README.TXT", "FILE_ID.DIZ"):
            shutil.copyfile(ROOT / name, self.repo / name)
        relatives = ["oemdisk/INSTALL.BAT", "oemdisk/TANDY88.BAT",
                     "src/splash/assets/TNDYLOGO.RLE"]
        relatives += ["src/tandysw/bin/" + name for name in s.BINARY_HASHES]
        for relative in relatives:
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.archive = self.base / "T88TOOLS.ZIP"
        self.fonts = self.base / "owned"
        self.fonts.mkdir()
        for name in s.inf_support_files((self.repo / "oemsetup.inf").read_bytes()):
            data = font_fixture() if name.endswith(".FON") else b"Synthetic test fixture only"
            (self.fonts / name).write_bytes(data)
        # Unit fixtures never pretend to be accepted Windows media. Replace the
        # production hashes only inside each isolated test, then restore them.
        fixture_pins = {p.name: s.sha(p.read_bytes()) for p in self.fonts.iterdir()}
        patcher = mock.patch.dict(s.SUPPORT_HASHES, fixture_pins, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def disk(self):
        builder.build_toolkit(self.repo, self.archive)
        target = self.base / "clean"
        with zipfile.ZipFile(self.archive) as archive:
            archive.extractall(target)
        return target / "DISK1"

    def test_five_profiles_have_distinct_files_and_original_default(self):
        text = (self.repo / "oemsetup.inf").read_text()
        lines = text.split("[display]\n", 1)[1].split("[sysfonts]", 1)[0].splitlines()
        choices = [line for line in lines if line and not line.startswith(";")]
        self.assertEqual(len(choices), 5)
        self.assertEqual(choices[0],
            'TANDY88 = a:TANDY88.DRV, "Tandy EX/HX 320x200 16 colors (8088 c05)", '
            '"133,96,72", a:CGA.GR2, a:CGALOGO.LGO,,,, a:TNDYLOGO.RLE')
        self.assertEqual([line.split(" = ")[0] for line in choices],
                         ["TANDY88", "TNDY6404", "TNDY160", "TNDY3204", "TNDY6402"])
        self.assertEqual(len(s.DRIVER_NAMES), 5)
        for name in s.PAYLOAD_NAMES | set(s.SUPPORT_HASHES):
            self.assertRegex(name, "^" + s.DOS_NAME + "$")
        for line in choices[1:]:
            self.assertIn('"200,96,48"', line)
        for font in ("CGASYS", "CGAFIX", "CGAOEM"):
            self.assertIn("a:" + font + ".FON", text)

    def test_missing_duplicate_reordered_and_crosswired_profiles_rejected(self):
        original = (self.repo / "oemsetup.inf").read_bytes()
        lines = original.splitlines(keepends=True)
        default = next(line for line in lines if line.startswith(b"TANDY88 ="))
        extra = next(line for line in lines if line.startswith(b"TNDY6404 ="))
        variants = [original.replace(extra, b""), original.replace(extra, extra + extra),
                    original.replace(default + extra, extra + default),
                    original.replace(b"a:TNDY6404.DRV", b"a:TANDY88.DRV"),
                    original.replace(b"TNDY6404 =", b"TANDY88 =")]
        for data in variants:
            with self.subTest(data=data), self.assertRaises(s.DiskError):
                s.inf_support_files(data)

    def test_other_sections_cannot_force_install_unselected_drivers(self):
        original = (self.repo / "oemsetup.inf").read_bytes()
        for name in sorted(s.DRIVER_NAMES):
            extra = s.dos_text("[fonts]\na:" + name + ", unselected, 1\n")
            with self.subTest(name=name), self.assertRaisesRegex(s.DiskError, "Setup selects one"):
                s.inf_support_files(original + extra)

    def test_every_profile_requires_its_font_resolution_and_splash(self):
        original = (self.repo / "oemsetup.inf").read_bytes()
        for key, _, resolution in s.DISPLAY_PROFILES:
            line = next(line for line in original.splitlines() if line.startswith(key.encode() + b" ="))
            for value in (line.replace(resolution.encode(), b"1,2,3"),
                          line.replace(b"a:TNDYLOGO.RLE", b"a:CGALOGO.RLE"),
                          line.replace(b"a:CGA.GR2", b"a:OTHER.GR2")):
                with self.subTest(key=key, value=value), self.assertRaises(s.DiskError):
                    s.inf_support_files(original.replace(line, value))

    def test_font_contract_rejects_missing_swapped_and_wrong_metadata(self):
        original = (self.repo / "oemsetup.inf").read_bytes()
        for font in ("EGASYS", "EGAFIX", "EGAOEM", "CGASYS", "CGAFIX", "CGAOEM"):
            line = next(line for line in original.splitlines(keepends=True)
                        if line.startswith(b"a:" + font.encode() + b".FON"))
            wrong = b"200,96,48" if font.startswith("EGA") else b"133,96,72"
            right = b"133,96,72" if font.startswith("EGA") else b"200,96,48"
            for value in (b"", line + line, line.replace(right, wrong),
                          line.replace(font.encode(), b"OTHER")):
                with self.subTest(font=font, value=value), self.assertRaises(s.DiskError):
                    s.inf_support_files(original.replace(line, value))
        with self.assertRaises(s.DiskError):
            s.inf_support_files(original.replace(b'"200,96,48", 1', b'"200,96,48", 2'))

    def test_every_new_driver_is_required_and_pinned_for_both_outputs(self):
        for name in sorted(s.DRIVER_NAMES - {"TANDY88.DRV"}):
            path = self.repo / "src/tandysw/bin" / name
            original = path.read_bytes()
            for data in (None, b"unaccepted build"):
                if data is None:
                    path.unlink()
                else:
                    path.write_bytes(data)
                for complete in (False, True):
                    with self.subTest(name=name, data=data, complete=complete), self.assertRaises(s.DiskError):
                        if complete:
                            builder.build(self.repo, self.archive, self.fonts)
                        else:
                            builder.build_toolkit(self.repo, self.archive)
                    self.assertFalse(self.archive.exists())
            path.write_bytes(original)

    def test_every_cga_font_is_required_and_pinned_without_partial_output(self):
        for name in ("CGASYS.FON", "CGAFIX.FON", "CGAOEM.FON"):
            path = self.fonts / name
            original = path.read_bytes()
            for data in (None, original + b"modified font"):
                if data is None:
                    path.unlink()
                else:
                    path.write_bytes(data)
                local = self.base / "local"
                with self.subTest(name=name, data=data), self.assertRaises(s.DiskError):
                    builder.build_with_local(self.repo, self.archive, self.fonts, local)
                self.assertFalse(self.archive.exists())
                self.assertFalse(local.exists())
            path.write_bytes(original)

    def test_completion_paths_reject_cluster_rounded_overflow(self):
        path = self.repo / "README.TXT"
        path.write_bytes(b"Large README\r\n" * 30000)
        with self.assertRaisesRegex(s.DiskError, "360 KB"):
            builder.build(self.repo, self.archive, self.fonts, self.base / "local")
        self.assertFalse(self.archive.exists())
        self.assertFalse((self.base / "local").exists())
        disk = self.disk()
        with self.assertRaisesRegex(s.DiskError, "360 KB"):
            s.stage(disk, self.fonts, self.base / "local")
        self.assertFalse((self.base / "local").exists())

    def test_toolkit_verifier_rejects_unexpected_members_and_stale_sources(self):
        builder.build_toolkit(self.repo, self.archive)
        self.assertEqual(builder.verify_toolkit(self.repo, self.archive), sorted(s.SUPPORT_HASHES))
        with zipfile.ZipFile(self.archive) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        for index, (name, value) in enumerate((
                ("DISK1/CGASYS.FON", b"not allowed"), ("DISK1/LOCAL.TXT", b"not complete"),
                ("STAGE.PY", b"changed\r\n"), ("README.TXT", b"changed\r\n"),
                ("DISK1/MANIFEST.SHA", b"wrong\r\n"), ("DISK1/TNDY6404.DRV", b"wrong"))):
            changed = dict(entries)
            changed[name] = value
            path = self.base / ("WRONG" + str(index) + ".ZIP")
            builder.write_zip(changed, path)
            with self.subTest(name=name), self.assertRaises(s.DiskError):
                builder.verify_toolkit(self.repo, path)
        (self.repo / "STAGE.PY").write_bytes((self.repo / "STAGE.PY").read_bytes() + b"# changed\r\n")
        with self.assertRaisesRegex(s.DiskError, "differs from current source"):
            builder.verify_toolkit(self.repo, self.archive)

    def test_archive_verifiers_reject_duplicates_and_noncanonical_metadata(self):
        for complete in (False, True):
            entries = (builder.disk_entries(s.prepare_complete(builder.source_payload(self.repo), self.fonts))
                       if complete else builder.toolkit_entries(self.repo))
            verify = builder.verify_archive if complete else builder.verify_toolkit
            name = next(iter(entries))
            path = self.base / ("BAD" + str(complete) + ".ZIP")
            builder.write_zip(entries, path)
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("EXTRA", b"extra")
            with self.assertRaises(s.DiskError):
                verify(self.repo, path)
            path = self.base / ("DUP" + str(complete) + ".ZIP")
            builder.write_zip(entries, path)
            with zipfile.ZipFile(path, "a") as archive:
                with self.assertWarns(UserWarning):
                    archive.writestr(name, entries[name])
            with self.assertRaisesRegex(s.DiskError, "duplicate files"):
                verify(self.repo, path)
            path = self.base / ("TIME" + str(complete) + ".ZIP")
            with zipfile.ZipFile(path, "w") as archive:
                for key, data in sorted(entries.items()):
                    archive.writestr(key, data)  # Current timestamps, not canonical epoch.
            with self.assertRaisesRegex(s.DiskError, "Noncanonical"):
                verify(self.repo, path)

    def test_one_command_outputs_complete_disk_and_complete_zip(self):
        local = self.base / "local"
        builder.build_with_local(self.repo, self.archive, self.fonts, local)
        for name in s.DRIVER_NAMES | set(s.SUPPORT_HASHES):
            self.assertTrue((local / name).is_file(), name)
        self.assertTrue((local / "EGASYS.FON").is_file())
        self.assertTrue((local / "LOCAL.TXT").is_file())
        with zipfile.ZipFile(self.archive) as archive:
            self.assertIn("DISK1/EGASYS.FON", archive.namelist())
            self.assertEqual(archive.read("DISK1/EGASYS.FON"), (local / "EGASYS.FON").read_bytes())
        other = self.base / "OTHER.ZIP"
        builder.build(self.repo, other, self.fonts)
        self.assertEqual(self.archive.read_bytes(), other.read_bytes())

    def test_one_command_missing_media_leaves_neither_output(self):
        (self.fonts / "EGASYS.FON").unlink()
        local = self.base / "local"
        with self.assertRaises(s.DiskError):
            builder.build_with_local(self.repo, self.archive, self.fonts, local)
        self.assertFalse(local.exists())
        self.assertFalse(self.archive.exists())

    def test_one_command_existing_output_is_preserved(self):
        local = self.base / "local"
        local.mkdir()
        (local / "KEEP").write_bytes(b"keep")
        with self.assertRaises(s.DiskError):
            builder.build_with_local(self.repo, self.archive, self.fonts, local)
        self.assertEqual((local / "KEEP").read_bytes(), b"keep")
        self.assertFalse(self.archive.exists())

    def test_normal_build_requires_media_and_leaves_no_archive(self):
        with self.assertRaisesRegex(s.DiskError, "requires --windows-files"):
            builder.build(self.repo, self.archive)
        self.assertFalse(self.archive.exists())

    def test_toolkit_cannot_be_named_normal_download(self):
        with self.assertRaisesRegex(s.DiskError, "distinctly named"):
            builder.build_toolkit(self.repo, self.base / "TANDY88.ZIP")

    def test_complete_archive_exact_members_and_current_source(self):
        builder.build(self.repo, self.archive, self.fonts)
        self.assertEqual(builder.verify_archive(self.repo, self.archive), sorted(s.SUPPORT_HASHES))
        with zipfile.ZipFile(self.archive) as archive:
            names = set(archive.namelist())
            expected = {"DISK1/" + name for name in s.PAYLOAD_NAMES | set(s.SUPPORT_HASHES)
                        | {"LOCAL.TXT", "MANIFEST.SHA"}} | {"README.TXT"}
            self.assertEqual(names, expected)
            self.assertNotIn("STAGE.PY", names)
            for name in s.SUPPORT_HASHES:
                self.assertEqual(s.sha(archive.read("DISK1/" + name)), s.SUPPORT_HASHES[name])

    def test_complete_archive_is_deterministic(self):
        builder.build(self.repo, self.archive, self.fonts)
        other = self.base / "COMPLETE.ZIP"
        builder.build(self.repo, other, self.fonts)
        self.assertEqual(self.archive.read_bytes(), other.read_bytes())

    def test_wrong_support_bytes_rejected(self):
        path = self.fonts / "CGA.GR2"
        path.write_bytes(path.read_bytes() + b"wrong")
        with self.assertRaisesRegex(s.DiskError, "Unverified Windows support file"):
            builder.build(self.repo, self.archive, self.fonts)
        self.assertFalse(self.archive.exists())

    def test_media_fixtures_exclude_first_party_splash(self):
        self.assertEqual({p.name for p in self.fonts.iterdir()},
                         {"EGASYS.FON", "EGAFIX.FON", "EGAOEM.FON", "CGASYS.FON",
                          "CGAFIX.FON", "CGAOEM.FON", "CGA.GR2", "CGALOGO.LGO"})
        splash = self.repo / "src/splash/assets/TNDYLOGO.RLE"
        self.assertEqual(len(splash.read_bytes()), 5930)
        self.assertEqual(s.sha(splash.read_bytes()), s.SPLASH_SHA)
        self.assertNotIn(s.SPLASH_NAME, s.SUPPORT_HASHES)

    def test_stock_or_wrong_media_splash_never_used(self):
        (self.fonts / "CGALOGO.RLE").write_bytes(b"old cached stock splash")
        (self.fonts / "TNDYLOGO.RLE").write_bytes(b"wrong media override")
        builder.build(self.repo, self.archive, self.fonts)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertNotIn("DISK1/CGALOGO.RLE", archive.namelist())
            self.assertEqual(s.sha(archive.read("DISK1/TNDYLOGO.RLE")), s.SPLASH_SHA)

    def test_missing_source_splash_does_not_fall_back_to_media_or_dirty_disk(self):
        splash = self.repo / "src/splash/assets/TNDYLOGO.RLE"
        data = splash.read_bytes()
        splash.unlink()
        (self.fonts / "TNDYLOGO.RLE").write_bytes(data)
        (self.repo / "disk1").mkdir()
        (self.repo / "disk1/TNDYLOGO.RLE").write_bytes(data)
        for complete in (False, True):
            with self.subTest(complete=complete), self.assertRaises(s.DiskError):
                if complete:
                    builder.build(self.repo, self.archive, self.fonts)
                else:
                    builder.build_toolkit(self.repo, self.archive)
            self.assertFalse(self.archive.exists())

    def test_wrong_source_splash_rejected_without_output(self):
        path = self.repo / "src/splash/assets/TNDYLOGO.RLE"
        changed = bytearray(path.read_bytes())
        changed[63] ^= 0x11  # Valid monochrome run, different artwork.
        path.write_bytes(changed)
        with self.assertRaisesRegex(s.DiskError, "Unverified first-party splash"):
            builder.build_toolkit(self.repo, self.archive)
        self.assertFalse(self.archive.exists())

    def test_unrequested_media_never_packaged(self):
        (self.fonts / "WIN.COM").write_bytes(b"unrequested OS file")
        (self.fonts / "PRIVATE.TXT").write_bytes(b"unrelated")
        builder.build(self.repo, self.archive, self.fonts)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertNotIn("DISK1/WIN.COM", archive.namelist())
            self.assertNotIn("DISK1/PRIVATE.TXT", archive.namelist())

    def test_extra_inf_dependency_rejected(self):
        path = self.repo / "oemsetup.inf"
        path.write_bytes(path.read_bytes() + b"[fonts]\r\na:EXTRA.FON, extra, 1\r\n")
        with self.assertRaisesRegex(s.DiskError, "exactly eight"):
            builder.build(self.repo, self.archive, self.fonts)
        self.assertFalse(self.archive.exists())

    def modified_archive(self, mutate):
        builder.build(self.repo, self.archive, self.fonts)
        with zipfile.ZipFile(self.archive) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        mutate(entries)
        changed = self.base / "CHANGED.ZIP"
        builder.write_zip(entries, changed)
        return changed

    def test_verify_missing_dependency_and_extra_file_rejected(self):
        changed = self.modified_archive(lambda entries: entries.pop("DISK1/EGASYS.FON"))
        with self.assertRaisesRegex(s.DiskError, "missing, extra"):
            builder.verify_archive(self.repo, changed)
        with zipfile.ZipFile(changed, "a") as archive:
            archive.writestr("UNWANTED.TXT", b"extra")
        with self.assertRaisesRegex(s.DiskError, "missing, extra"):
            builder.verify_archive(self.repo, changed)

    def test_verify_missing_or_old_splash_name_rejected(self):
        changed = self.modified_archive(lambda entries: entries.__setitem__(
            "DISK1/CGALOGO.RLE", entries.pop("DISK1/TNDYLOGO.RLE")))
        with self.assertRaisesRegex(s.DiskError, "missing, extra"):
            builder.verify_archive(self.repo, changed)

    def test_verify_wrong_splash_rejected(self):
        def mutate(entries):
            changed = bytearray(entries["DISK1/TNDYLOGO.RLE"])
            changed[63] ^= 0x11
            entries["DISK1/TNDYLOGO.RLE"] = bytes(changed)
        changed = self.modified_archive(mutate)
        with self.assertRaisesRegex(s.DiskError, "Unverified first-party splash"):
            builder.verify_archive(self.repo, changed)

    def test_verify_wrong_support_rejected(self):
        changed = self.modified_archive(lambda entries: entries.update({"DISK1/CGA.GR2": b"wrong"}))
        with self.assertRaisesRegex(s.DiskError, "Unverified Windows support file"):
            builder.verify_archive(self.repo, changed)

    def test_verify_marker_and_manifest_rejected(self):
        changed = self.modified_archive(lambda entries: entries.update({"DISK1/MANIFEST.SHA": b"wrong\r\n"}))
        with self.assertRaisesRegex(s.DiskError, "differs from current source or manifest"):
            builder.verify_archive(self.repo, changed)
        with zipfile.ZipFile(self.archive) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        entries["DISK1/LOCAL.TXT"] = b"old marker\r\n"
        other = self.base / "MARKER.ZIP"
        builder.write_zip(entries, other)
        with self.assertRaisesRegex(s.DiskError, "Windows directory marker"):
            builder.verify_archive(self.repo, other)

    def test_verify_source_change_rejected(self):
        builder.build(self.repo, self.archive, self.fonts)
        path = self.repo / "README.TXT"
        path.write_bytes(path.read_bytes() + b"New source text\r\n")
        with self.assertRaisesRegex(s.DiskError, "differs from current source"):
            builder.verify_archive(self.repo, self.archive)

    def test_verify_custom_windows_path(self):
        builder.build(self.repo, self.archive, self.fonts, windows_dir=r"D:\WIN30")
        builder.verify_archive(self.repo, self.archive)

    def test_360k_fat12_allocation_budget(self):
        budget = builder.disk_allocation({"A": b"a", "B": b"b" * 1025})
        self.assertEqual(budget["allocated_file_bytes"], 3072)
        self.assertEqual(budget["filesystem_overhead_bytes"], 6144)
        self.assertEqual(budget["capacity_bytes"], 368640)
        self.assertEqual(budget["total_used_bytes"], 9216)
        with self.assertRaisesRegex(s.DiskError, "360 KB"):
            builder.disk_allocation({"BIG": b"x" * (354 * 1024 + 1)})
        with self.assertRaisesRegex(s.DiskError, "360 KB"):
            builder.disk_allocation({str(i): b"" for i in range(113)})

    def test_binary_pins_match_repository(self):
        s.verify_binaries({name: (ROOT / "src/tandysw/bin" / name).read_bytes()
                           for name in s.BINARY_HASHES})

    def test_deterministic_archive_and_exact_allowlist(self):
        builder.build_toolkit(self.repo, self.archive)
        second = self.base / "SECOND.ZIP"
        for path in self.repo.rglob("*"):
            if path.is_file():
                path.touch()
        builder.build_toolkit(self.repo, second)
        self.assertEqual(self.archive.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(self.archive) as archive:
            names = [info.filename for info in archive.infolist()]
            expected = {"DISK1/" + n for n in s.PAYLOAD_NAMES | {"MANIFEST.SHA"}}
            self.assertEqual(set(names), expected | {"STAGE.PY", "TOOLKIT.TXT", "README.TXT"})
            self.assertEqual(names, sorted(names))
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.create_system, 0)
                self.assertEqual(info.external_attr, 0x20)
            self.assertFalse(any(n.endswith((".FON", ".LGO", ".GR2")) for n in names))
            self.assertEqual({n for n in names if n.endswith(".RLE")}, {"DISK1/TNDYLOGO.RLE"})
            self.assertEqual(s.sha(archive.read("DISK1/TNDYLOGO.RLE")), s.SPLASH_SHA)

    def test_root_old_driver_and_dirty_disk_are_never_inputs(self):
        (self.repo / "TNDY16.DRV").write_bytes(b"wrong old driver")
        dirty = self.repo / "disk1"
        dirty.mkdir()
        (dirty / "EGASYS.FON").write_bytes(b"must not distribute")
        (dirty / "PRIVATE.TXT").write_bytes(b"must not distribute")
        builder.build_toolkit(self.repo, self.archive)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertNotIn("DISK1/TNDY16.DRV", archive.namelist())
            self.assertNotIn("DISK1/EGASYS.FON", archive.namelist())
            self.assertEqual(s.sha(archive.read("DISK1/TANDY88.DRV")), s.DRIVER_SHA)
        self.assertTrue((dirty / "PRIVATE.TXT").exists())

    def test_wrong_driver_rejected_without_output(self):
        (self.repo / "src/tandysw/bin/TANDY88.DRV").write_bytes(b"stale")
        with self.assertRaisesRegex(s.DiskError, "Unverified TANDY88"):
            builder.build_toolkit(self.repo, self.archive)
        self.assertFalse(self.archive.exists())

    def test_wrong_helper_rejected_without_output(self):
        (self.repo / "src/tandysw/bin/RESERVE.COM").write_bytes(b"stale")
        with self.assertRaisesRegex(s.DiskError, "Unverified RESERVE"):
            builder.build_toolkit(self.repo, self.archive)
        self.assertFalse(self.archive.exists())

    def test_missing_driver_does_not_fall_back_or_build(self):
        (self.repo / "src/tandysw/bin/TANDY88.DRV").unlink()
        (self.repo / "TNDY16.DRV").write_bytes(b"old")
        with self.assertRaises(s.DiskError):
            builder.build_toolkit(self.repo, self.archive)
        self.assertFalse(self.archive.exists())

    def test_existing_archive_is_preserved(self):
        self.archive.write_bytes(b"preserve")
        with self.assertRaises(s.DiskError):
            builder.build_toolkit(self.repo, self.archive)
        self.assertEqual(self.archive.read_bytes(), b"preserve")

    def test_lf_text_rejected(self):
        path = self.repo / "README.TXT"
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
        with self.assertRaisesRegex(s.DiskError, "CRLF"):
            builder.build_toolkit(self.repo, self.archive)
        self.assertFalse(self.archive.exists())

    def test_old_inf_driver_rejected(self):
        path = self.repo / "oemsetup.inf"
        path.write_bytes(path.read_bytes().replace(b"TANDY88.DRV", b"TNDY16.DRV"))
        with self.assertRaisesRegex(s.DiskError, "OEM display"):
            builder.build_toolkit(self.repo, self.archive)

    def test_stock_logo_name_cannot_reuse_setup_cache(self):
        path = self.repo / "oemsetup.inf"
        path.write_bytes(path.read_bytes().replace(b"a:TNDYLOGO.RLE", b"a:CGALOGO.RLE"))
        with self.assertRaisesRegex(s.DiskError, "cached stock splash"):
            builder.build_toolkit(self.repo, self.archive)
        self.assertFalse(self.archive.exists())

    def test_omitted_custom_bitmap_rejected(self):
        path = self.repo / "oemsetup.inf"
        path.write_bytes(path.read_bytes().replace(b"a:TNDYLOGO.RLE", b""))
        with self.assertRaisesRegex(s.DiskError, "logo"):
            builder.build_toolkit(self.repo, self.archive)

    def test_omitted_wincom_logo_rejected(self):
        path = self.repo / "oemsetup.inf"
        path.write_bytes(path.read_bytes().replace(b"a:CGALOGO.LGO", b""))
        with self.assertRaisesRegex(s.DiskError, "logo"):
            builder.build_toolkit(self.repo, self.archive)

    def test_unsupported_helper_inf_section_rejected(self):
        path = self.repo / "oemsetup.inf"
        path.write_bytes(path.read_bytes() + b"[optional]\r\na:RESERVE.COM\r\n")
        with self.assertRaisesRegex(s.DiskError, "optional"):
            builder.build_toolkit(self.repo, self.archive)

    def test_local_stage_complete_and_manifest(self):
        disk = self.disk()
        out = self.base / "local"
        names = s.stage(disk, self.fonts, out)
        self.assertEqual(names, s.inf_support_files((disk / "OEMSETUP.INF").read_bytes()))
        payload = {p.name: p.read_bytes() for p in out.iterdir() if p.name != "MANIFEST.SHA"}
        self.assertEqual((out / "MANIFEST.SHA").read_bytes(), s.manifest(payload))
        self.assertIn(b"COMPLETE TANDY88 OEM DISK", (out / "LOCAL.TXT").read_bytes())
        self.assertFalse(list(out.glob("*.ZIP")))
        for name in s.BINARY_HASHES:
            self.assertEqual((out / name).read_bytes(), (disk / name).read_bytes())

    def test_extracted_toolkit_stages_without_source_tree_or_site_packages(self):
        disk = self.disk()
        out = self.base / "standalone"
        # The fixture pins apply only in this isolated test process. The custom
        # bitmap remains the actual accepted first-party file with its real pin.
        code = ("import runpy,sys; from pathlib import Path; "
                "m=runpy.run_path(sys.argv[1]); "
                "m['SUPPORT_HASHES'].update(" + repr(dict(s.SUPPORT_HASHES)) + "); "
                "m['stage'](Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]))")
        result = subprocess.run([sys.executable, "-I", "-S", "-c", code,
                                 str(disk.parent / "STAGE.PY"), str(disk),
                                 str(self.fonts), str(out)], cwd=self.base,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((disk.parent / "src").exists())
        self.assertEqual(s.sha((out / "TNDYLOGO.RLE").read_bytes()), s.SPLASH_SHA)
        self.assertFalse((out / "CGALOGO.RLE").exists())

    def test_missing_toolkit_splash_rejected(self):
        disk = self.disk()
        (disk / "TNDYLOGO.RLE").unlink()
        out = self.base / "local"
        with self.assertRaisesRegex(s.DiskError, "untouched toolkit"):
            s.stage(disk, self.fonts, out)
        self.assertFalse(out.exists())

    def test_changed_toolkit_splash_rejected_even_with_recomputed_manifest(self):
        disk = self.disk()
        path = disk / "TNDYLOGO.RLE"
        changed = bytearray(path.read_bytes())
        changed[63] ^= 0x11
        path.write_bytes(changed)
        payload = {p.name: p.read_bytes() for p in disk.iterdir() if p.name != "MANIFEST.SHA"}
        (disk / "MANIFEST.SHA").write_bytes(s.manifest(payload))
        out = self.base / "local"
        with self.assertRaisesRegex(s.DiskError, "Unverified first-party splash"):
            s.stage(disk, self.fonts, out)
        self.assertFalse(out.exists())

    def test_compressed_owned_files_stage_locally(self):
        for path in self.fonts.iterdir():
            path.write_bytes(compressed_fixture(path.read_bytes()))
        out = self.base / "local"
        s.stage(self.disk(), self.fonts, out)
        self.assertEqual((out / "EGASYS.FON").read_bytes(), font_fixture())
        with zipfile.ZipFile(self.archive) as archive:
            self.assertFalse(any(n.endswith(".FON") for n in archive.namelist()))

    def test_missing_font_and_missing_logo_leave_no_output(self):
        disk = self.disk()
        for name in ("EGASYS.FON", "CGALOGO.LGO"):
            path = self.fonts / name
            saved = path.read_bytes()
            path.unlink()
            out = self.base / "missing"
            with self.subTest(name=name), self.assertRaises(s.DiskError):
                s.stage(disk, self.fonts, out)
            self.assertFalse(out.exists())
            path.write_bytes(saved)

    def test_invalid_font_leaves_no_output(self):
        (self.fonts / "EGASYS.FON").write_bytes(b"not a font")
        out = self.base / "local"
        with self.assertRaisesRegex(s.DiskError, "expanded Windows"):
            s.stage(self.disk(), self.fonts, out)
        self.assertFalse(out.exists())

    def test_changed_clean_payload_rejected(self):
        disk = self.disk()
        (disk / "README.TXT").write_bytes(b"changed\r\n")
        with self.assertRaisesRegex(s.DiskError, "manifest mismatch"):
            s.stage(disk, self.fonts, self.base / "local")

    def test_extra_local_files_rejected_as_distribution_input(self):
        disk = self.disk()
        (disk / "EGASYS.FON").write_bytes(font_fixture())
        with self.assertRaisesRegex(s.DiskError, "untouched toolkit"):
            s.stage(disk, self.fonts, self.base / "local")

    def test_existing_stage_output_preserved(self):
        out = self.base / "local"
        out.mkdir()
        (out / "KEEP.TXT").write_bytes(b"preserve")
        with self.assertRaises(s.DiskError):
            s.stage(self.disk(), self.fonts, out)
        self.assertEqual((out / "KEEP.TXT").read_bytes(), b"preserve")

    def test_case_insensitive_media(self):
        for path in self.fonts.iterdir():
            path.rename(path.with_name(path.name.lower()))
        s.stage(self.disk(), self.fonts, self.base / "local")
        self.assertTrue((self.base / "local/EGASYS.FON").is_file())

    def test_ambiguous_media_rejected_where_supported(self):
        (self.fonts / "egasys.fon").write_bytes(font_fixture())
        if len([p for p in self.fonts.iterdir() if p.name.upper() == "EGASYS.FON"]) == 1:
            self.skipTest("Case-insensitive host filesystem")
        with self.assertRaisesRegex(s.DiskError, "ambiguous"):
            s.stage(self.disk(), self.fonts, self.base / "local")

    def test_custom_dos_path_preserves_helper_location(self):
        out = self.base / "local"
        s.stage(self.disk(), self.fonts, out, r"d:\win30")
        script = (out / "TANDY88.BAT").read_bytes()
        self.assertIn(b"D:\\WIN30\\WIN.COM /R", script)
        self.assertIn(b"REM WINDOWSDRIVE\r\nD:\r\nCD D:\\WIN30", script)
        self.assertIn(b"C:\\TANDY88\\RESERVE.COM", script)
        self.assertNotIn(b"C:\\WINDOWS", script)

    def test_invalid_paths_rejected(self):
        for path in ("WINDOWS", "C:WINDOWS", "C:\\", r"C:\Program Files", r"C:\WINDOWS&WIN",
                     r"C:\..\WINDOWS", r"C:\TANDY88", r"C:\TANDY88\WIN", "C:\\WIN\nSTART"):
            with self.subTest(path=path), self.assertRaises(s.DiskError):
                s.windows_path(path)

    def test_launcher_gates_both_executables(self):
        text = (self.repo / "oemdisk/TANDY88.BAT").read_text()
        gate = text.index("IF ERRORLEVEL 1 GOTO FAILED")
        self.assertLess(text.index("IF NOT EXIST C:\\TANDY88\\RESERVE.COM GOTO NOHELP"), gate)
        self.assertLess(text.index("\nC:\\TANDY88\\RESERVE.COM\n"), gate)
        self.assertLess(gate, text.index("\nC:\\WINDOWS\\WIN.COM /R\n"))
        self.assertLess(gate, text.index("\nC:\\WINDOWS\\SETUP.EXE\n"))

    def test_installer_never_starts_windows_or_setup(self):
        lines = (self.repo / "oemdisk/INSTALL.BAT").read_text().splitlines()
        self.assertFalse(any(line.upper().endswith("WIN.COM /R") for line in lines))
        self.assertFalse(any(line.upper().endswith("\\SETUP.EXE") for line in lines))
        self.assertLess(lines.index("IF ERRORLEVEL 1 GOTO FAILED"), lines.index("MD C:\\TANDY88"))

    def test_partial_stage_write_failure_cleans_new_output(self):
        disk = self.disk()
        out = self.base / "local"
        original = Path.write_bytes
        def failing(path, data):
            if path.parent == out and path.name == "OEMSETUP.INF":
                raise OSError("simulated full disk")
            return original(path, data)
        with mock.patch.object(Path, "write_bytes", failing):
            with self.assertRaises(OSError):
                s.stage(disk, self.fonts, out)
        self.assertFalse(out.exists())

    def test_partial_archive_failure_cleans_new_output(self):
        with mock.patch.object(zipfile.ZipFile, "writestr", side_effect=OSError("simulated full disk")):
            with self.assertRaises(OSError):
                builder.build_toolkit(self.repo, self.archive)
        self.assertFalse(self.archive.exists())


class FormatTests(unittest.TestCase):
    def test_accepted_splash_format_and_pins(self):
        data = (ROOT / "src/splash/assets/TNDYLOGO.RLE").read_bytes()
        s.verify_splash({s.SPLASH_NAME: data})
        self.assertEqual(s.splash_rle(data), {"width": 640, "height": 200,
                         "encoded_runs": 2733, "eol_commands": 200,
                         "file_bytes": 5930, "image_bytes": 5868})
        self.assertEqual(s.SUPPORT_HASHES["CGALOGO.LGO"],
                         "d9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807")

    def test_malformed_splash_headers_rejected(self):
        good = (ROOT / "src/splash/assets/TNDYLOGO.RLE").read_bytes()
        variants = [("too short", good[:61]), ("too large", good + b"x" * 65280),
                    ("signature", b"XX" + good[2:]), ("truncated", good[:-1]),
                    ("trailing", good + b"x")]
        for label, offset, fmt, value in (
                ("file size", 2, "I", len(good) - 2), ("reserved", 6, "H", 1),
                ("pixel offset", 10, "I", 54), ("header size", 14, "I", 12),
                ("width", 18, "i", 320), ("height", 22, "i", -200),
                ("planes", 26, "H", 2), ("bpp", 28, "H", 4),
                ("compression", 30, "I", 0), ("image size", 34, "I", 1),
                ("resolution", 38, "i", 1), ("palette count", 46, "I", 16),
                ("important colors", 50, "I", 1), ("palette bytes", 54, "I", 1)):
            changed = bytearray(good)
            struct.pack_into("<" + fmt, changed, offset, value)
            variants.append((label, bytes(changed)))
        for label, data in variants:
            with self.subTest(label=label), self.assertRaises(s.DiskError):
                s.splash_rle(data)

    def test_malformed_splash_commands_rejected(self):
        good = (ROOT / "src/splash/assets/TNDYLOGO.RLE").read_bytes()
        def with_stream(stream):
            header = bytearray(good[:62])
            struct.pack_into("<I", header, 2, 62 + len(stream))
            struct.pack_into("<I", header, 34, len(stream))
            return bytes(header) + stream
        row = bytes((254, 0, 254, 0, 132, 0, 0, 0))
        valid = with_stream(row * 200 + b"\0\1")
        s.splash_rle(valid)
        # A valid alternative bitmap still cannot replace the accepted artwork.
        with self.assertRaisesRegex(s.DiskError, "Unverified first-party splash"):
            s.verify_splash({s.SPLASH_NAME: valid})
        for label, stream in (
                ("early eol", b"\0\0"), ("early eob", b"\0\1"),
                ("delta", b"\0\2"), ("absolute", b"\0\3"),
                ("invalid color", bytes((1, 0x22))),
                ("alternating run", bytes((2, 0x01))),
                ("oversized run", bytes((255, 0))),
                ("row overflow", bytes((254, 0)) * 3),
                ("height overflow", row * 201 + b"\0\1"),
                ("extra eol", row * 200 + b"\0\0\0\1"),
                ("no eob", row * 200), ("half command", row * 200 + b"\0"),
                ("trailing command", row * 200 + b"\0\1\0\0")):
            with self.subTest(label=label), self.assertRaises(s.DiskError):
                s.splash_rle(with_stream(stream))

    def test_literal_szdd_roundtrip(self):
        for data in (b"a", b"12345678", b"123456789", bytes(range(256)), font_fixture()):
            self.assertEqual(s.expanded_file(compressed_fixture(data), "TEST.FON"), data)

    def test_backreference_and_initial_space_dictionary(self):
        # Initial dictionary spaces, then literal A and overlapping A repetition.
        body = bytes((2, 0, 0, ord("A"), 0xf3, 0xf0))
        data = b"SZDD\x88\xf0\x27\x33A\x00" + struct.pack("<I", 7) + body
        self.assertEqual(s.expanded_file(data, "TEST"), b"   AAAA")

    def test_malformed_szdd_rejected(self):
        good = compressed_fixture(b"abc")
        variants = [good[:10], good[:-1], good + b"x", good[:8] + b"B" + good[9:],
                    good[:10] + struct.pack("<I", 2**24) + good[14:],
                    good[:10] + struct.pack("<I", 0) + good[14:]]
        for data in variants:
            with self.subTest(data=data), self.assertRaises(s.DiskError):
                s.expanded_file(data, "TEST")

    def test_font_resource_bounds_checked(self):
        good = font_fixture()
        s.font_ne(good, "TEST.FON")
        variants = [good[:100], good[:128], good[:200], b"X" + good[1:]]
        for data in variants:
            with self.subTest(length=len(data)), self.assertRaises(s.DiskError):
                s.font_ne(data, "TEST.FON")

    def test_all_authored_dos_text_is_crlf(self):
        paths = [ROOT / p for p in ("MAKEDISK.BAT", "MAKEDISK.PY", "STAGE.PY", "README.TXT",
                                     "FILE_ID.DIZ", "BUILDING.MD", "docs/OEMDISK.MD")]
        paths += [ROOT / "oemsetup.inf"]
        paths += list((ROOT / "oemdisk").glob("*.BAT")) + list((ROOT / "oemdisk").glob("*.PY"))
        for path in paths:
            with self.subTest(path=path):
                s.checked_text(path.read_bytes(), path.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
