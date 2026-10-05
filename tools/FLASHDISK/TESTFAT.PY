#!/usr/bin/env python3
"""FAT12.PY regression tests. Run with: python TESTFAT.PY -v.

No third-party Python packages required. fsck.fat and mtools checks run when
those tools are installed; DOSBox-X checks run when FAT12_DOSBOX is set.
"""

import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
LOADER = importlib.machinery.SourceFileLoader("fat12_test_subject", str(HERE / "FAT12.PY"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
fat12 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fat12
LOADER.exec_module(fat12)


def independent_read(image):
    """Small independent generic FAT12 reader, not using production helpers."""
    bps = int.from_bytes(image[11:13], "little")
    spc = image[13]
    reserved = int.from_bytes(image[14:16], "little")
    nfats = image[16]
    nroot = int.from_bytes(image[17:19], "little")
    sectors = int.from_bytes(image[19:21], "little")
    spf = int.from_bytes(image[22:24], "little")
    root_at = (reserved + nfats * spf) * bps
    data_at = root_at + ((nroot * 32 + bps - 1) // bps) * bps
    cluster_bytes = bps * spc
    fat_at = reserved * bps
    results = {}
    directory_clusters = {}

    def get_chain(start):
        chain = []
        while start < 0xFF8:
            if start < 2 or start in chain:
                raise AssertionError("Invalid cluster chain in independent reader")
            chain.append(start)
            at = fat_at + start * 3 // 2
            word = int.from_bytes(image[at:at + 2], "little")
            start = (word >> 4) if start % 2 else (word & 4095)
        return chain

    def read_chain(chain):
        return b"".join(image[data_at + (c - 2) * cluster_bytes:
                              data_at + (c - 1) * cluster_bytes] for c in chain)

    def read_dir(raw, prefix):
        for at in range(0, len(raw), 32):
            entry = raw[at:at + 32]
            if entry[0] == 0:
                break
            if entry[0] == 0xE5 or entry[11] == 0x0F:
                continue
            name = entry[:8].decode("ascii").rstrip()
            ext = entry[8:11].decode("ascii").rstrip()
            if ext:
                name += "." + ext
            if name in (".", "..") or entry[11] & 8:
                continue
            path = prefix + name
            first = int.from_bytes(entry[26:28], "little")
            size = int.from_bytes(entry[28:32], "little")
            if entry[11] & 16:
                chain = get_chain(first)
                results[path] = None
                directory_clusters[path] = chain
                read_dir(read_chain(chain), path + "/")
            else:
                results[path] = read_chain(get_chain(first))[:size] if size else b""
    read_dir(image[root_at:root_at + nroot * 32], "")
    return results, directory_clusters, (bps, spc, sectors, spf, data_at)


def mutate_fat(image, cluster, value):
    """Mutate both copies using integer bitfields, not the writer helper."""
    image = bytearray(image)
    spf = int.from_bytes(image[22:24], "little")
    for number in (0, 1):
        start = 512 + number * spf * 512
        raw = int.from_bytes(image[start:start + spf * 512], "little")
        shift = cluster * 12
        raw = (raw & ~(4095 << shift)) | (value << shift)
        image[start:start + spf * 512] = raw.to_bytes(spf * 512, "little")
    return image


class FAT12Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "SOURCE"
        self.source.mkdir()

    def put(self, path, data=b"hello\r\n"):
        target = self.source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def make(self, size=720, label="TANDY88"):
        return fat12.make_image(self.source, size, label)

    def verify(self, blob, expected=None):
        return fat12._verify_bytes(blob, expected)

    def fixture(self):
        self.put("README.TXT", b"read me\r\n")
        self.put("EMPTY.TXT", b"")
        self.put("SUB/DEEP/THIRD/FILE.BIN", bytes(range(256)) * 23 + b"end")
        self.put("SUB/FILE.DAT", b"subfolder")
        (self.source / "EMPTYDIR").mkdir()
        return {"README.TXT": b"read me\r\n", "EMPTY.TXT": b"",
                "SUB": None, "SUB/DEEP": None, "SUB/DEEP/THIRD": None,
                "SUB/DEEP/THIRD/FILE.BIN": bytes(range(256)) * 23 + b"end",
                "SUB/FILE.DAT": b"subfolder", "EMPTYDIR": None}

    def test_independent_reader_geometry_and_nested_content(self):
        expected = self.fixture()
        for size, sectors, spf, cylinders, media, clusters, data_at in (
                (720, 1440, 3, 80, 0xF9, 713, 7168),
                (360, 720, 2, 40, 0xFD, 354, 6144)):
            with self.subTest(size=size):
                blob = self.make(size)
                actual, dirs, dimensions = independent_read(blob)
                self.assertEqual(actual, expected)
                self.assertEqual(dimensions, (512, 2, sectors, spf, data_at))
                self.assertEqual(len(blob), size * 1024)
                self.assertEqual(blob[21], media)
                self.assertEqual(blob[24:28], b"\x09\0\x02\0")
                self.assertEqual(blob[512:515], bytes((media, 255, 255)))
                self.assertEqual(blob[512:512 + spf * 512],
                                 blob[512 + spf * 512:512 + spf * 1024])
                result = self.verify(blob, expected)
                self.assertEqual(result["total_clusters"], clusters)
                self.assertEqual(result["cylinders"], cylinders)
                self.assertFalse(result["bootable"])
                # Dot entries point to self and parent, root is represented by 0.
                for directory, chain in dirs.items():
                    first = chain[0]
                    offset = data_at + (first - 2) * 1024
                    self.assertEqual(blob[offset:offset + 11], b".          ")
                    self.assertEqual(int.from_bytes(blob[offset + 26:offset + 28], "little"), first)
                    parent = directory.rpartition("/")[0]
                    parent_cluster = dirs[parent][0] if parent else 0
                    self.assertEqual(int.from_bytes(blob[offset + 58:offset + 60], "little"), parent_cluster)

    def test_empty_source(self):
        for size in (720, 360):
            blob = self.make(size)
            self.assertEqual(independent_read(blob)[0], {})
            report = self.verify(blob)
            self.assertEqual(report["used_clusters"], 0)
            self.assertEqual(report["file_count"], 0)

    def test_deterministic_across_mtimes_and_creation_order(self):
        expected = self.fixture()
        original = self.make()
        other = self.base / "OTHER"
        other.mkdir()
        for path, data in reversed(list(expected.items())):
            target = other / path
            if data is None:
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                os.utime(str(target), (1700000000, 1700000000))
        self.assertEqual(original, fat12.make_image(other))
        self.assertEqual(original, self.make())

    def test_content_derived_serial_changes(self):
        path = self.put("FILE.TXT", b"one")
        first = self.make()
        path.write_bytes(b"two")
        second = self.make()
        self.assertNotEqual(first[39:43], second[39:43])
        self.assertNotEqual(self.make(label="OTHER")[39:43], second[39:43])

    def test_many_directory_entries_span_clusters(self):
        for n in range(100):
            self.put("SUB/DEEP/F%07d.TXT" % n, str(n).encode())
        blob = self.make()
        actual, dirs, _ = independent_read(blob)
        self.assertEqual(len(dirs["SUB/DEEP"]), 4)
        self.assertEqual(actual["SUB/DEEP/F0000099.TXT"], b"99")
        self.assertEqual(self.verify(blob)["file_count"], 100)

    def test_exactly_full_directory_without_end_marker(self):
        for n in range(30):
            self.put("SUB/F%07d" % n, b"")
        blob = self.make()
        actual, dirs, _ = independent_read(blob)
        self.assertEqual(len(dirs["SUB"]), 1)
        self.assertEqual(len(actual), 31)
        self.verify(blob)

    def test_root_capacity_and_overflow(self):
        for n in range(111):
            self.put("F%07d" % n, b"")
        self.assertEqual(self.verify(self.make())["file_count"], 111)
        self.put("OVERFLOW", b"")
        with self.assertRaisesRegex(fat12.ImageError, "Root directory is full"):
            self.make()

    def test_full_data_capacity_and_one_byte_over(self):
        for size, count in ((360, 354), (720, 713)):
            with self.subTest(size=size):
                self.put("FULL.BIN", b"x" * (count * 1024))
                blob = self.make(size)
                result = self.verify(blob)
                self.assertEqual(result["free_bytes"], 0)
                self.assertEqual(independent_read(blob)[0]["FULL.BIN"], b"x" * (count * 1024))
                self.put("FULL.BIN", b"x" * (count * 1024 + 1))
                with self.assertRaisesRegex(fat12.ImageError, "does not fit"):
                    self.make(size)

    def test_empty_directory_allocation_counts(self):
        self.put("FULL.BIN", b"x" * (354 * 1024))
        (self.source / "EMPTY").mkdir()
        with self.assertRaisesRegex(fat12.ImageError, "does not fit"):
            self.make(360)

    def test_oversized_payload_rejected_before_read(self):
        with (self.source / "HUGE.BIN").open("wb") as stream:
            stream.truncate(1024 * 1024 * 1024)
        with self.assertRaisesRegex(fat12.ImageError, "exceeds image capacity"):
            self.make()

    def test_invalid_dos_names(self):
        for name in ("lower.txt", "TOOLONGER.TXT", "FILE.LONG", "A.B.C", ".HIDDEN",
                     "TRAIL.", "A B.TXT", "A+X.TXT", "A;X.TXT", "A=X.TXT",
                     "A[X].TXT", "A,X.TXT", "A\u00c9.TXT", "CON", "CON.TXT", "PRN",
                     "AUX.BIN", "NUL", "COM1.TXT", "LPT9", "CLOCK$"):
            with self.subTest(name=name):
                target = self.put(name)
                try:
                    with self.assertRaises(fat12.ImageError):
                        self.make()
                finally:
                    target.unlink()

    def test_boot_files_rejected_even_nested(self):
        for name in sorted(fat12.BOOT_FILES):
            with self.subTest(name=name):
                path = self.put("SUB/" + name)
                try:
                    with self.assertRaisesRegex(fat12.ImageError, "boot file"):
                        self.make()
                finally:
                    path.unlink()

    def test_dos_safe_punctuation(self):
        for name in ("A_B-1.TXT", "$DATA.BIN", "~FILE", "A!#%&'().X", "@^_`{}~"):
            self.put(name)
        self.assertEqual(self.verify(self.make())["file_count"], 5)

    def test_case_collision(self):
        first = self.put("FILE.TXT")
        second = self.put("file.txt")
        if first.samefile(second):
            self.skipTest("Case-insensitive host filesystem")
        with self.assertRaisesRegex(fat12.ImageError, "collision"):
            self.make()

    def test_symlink_file_and_directory_rejected(self):
        if not hasattr(os, "symlink"):
            self.skipTest("Host lacks symlinks")
        external = self.base / "OUTSIDE.TXT"
        external.write_bytes(b"outside")
        for target in (external, self.base):
            link = self.source / "LINK"
            try:
                link.symlink_to(target, target_is_directory=target.is_dir())
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation unavailable")
            try:
                with self.assertRaisesRegex(fat12.ImageError, "Links"):
                    self.make()
            finally:
                link.unlink()

    def test_symlink_source_and_ancestor_rejected(self):
        alias = self.base / "ALIAS"
        try:
            alias.symlink_to(self.source, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        with self.assertRaisesRegex(fat12.ImageError, "Links"):
            fat12.make_image(alias)
        (self.source / "SUB").mkdir()
        with self.assertRaisesRegex(fat12.ImageError, "Links"):
            fat12.make_image(alias / "SUB")

    def test_hardlink_rejected(self):
        external = self.base / "OUTSIDE.TXT"
        external.write_bytes(b"outside")
        try:
            os.link(str(external), str(self.source / "LINK.TXT"))
        except (OSError, NotImplementedError):
            self.skipTest("Hard links unavailable")
        with self.assertRaisesRegex(fat12.ImageError, "Hard links"):
            self.make()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Host lacks FIFO files")
    def test_special_file_rejected(self):
        os.mkfifo(str(self.source / "FIFO"))
        with self.assertRaisesRegex(fat12.ImageError, "regular files"):
            self.make()

    def test_parent_traversal_rejected(self):
        with self.assertRaisesRegex(fat12.ImageError, "Parent traversal"):
            fat12.make_image(self.source / ".." / "SOURCE")

    def test_unsupported_sizes_and_labels(self):
        for size in (0, 180, 1200, 1440, 2880):
            with self.subTest(size=size), self.assertRaises(fat12.ImageError):
                self.make(size)
        for label in ("", "LOWERcase", "TOO LONG NAME", " BAD", "BAD ", "A.B", "A/B"):
            with self.subTest(label=label), self.assertRaises(fat12.ImageError):
                self.make(label=label)

    def test_build_never_overwrites_and_rejects_source_destination(self):
        self.fixture()
        output = self.base / "IMAGE.IMG"
        report = fat12.build_image(self.source, output)
        self.assertEqual(report, fat12.verify_image(output, self.source))
        original = output.read_bytes()
        with self.assertRaisesRegex(fat12.ImageError, "already exists"):
            fat12.build_image(self.source, output)
        self.assertEqual(original, output.read_bytes())
        with self.assertRaisesRegex(fat12.ImageError, "outside the source"):
            fat12.build_image(self.source, self.source / "IMAGE.IMG")

    def test_invalid_build_leaves_no_output(self):
        self.put("bad.txt")
        output = self.base / "IMAGE.IMG"
        with self.assertRaises(fat12.ImageError):
            fat12.build_image(self.source, output)
        self.assertFalse(output.exists())

    def test_source_mismatch_detects_missing_extra_type_and_content(self):
        expected = self.fixture()
        blob = self.make()
        for change in ({**expected, "EXTRA": b"x"},
                       {k: v for k, v in expected.items() if k != "EMPTY.TXT"},
                       {**expected, "README.TXT": b"other"},
                       {**expected, "EMPTYDIR": b""}):
            with self.assertRaisesRegex(fat12.ImageError, "Image/source"):
                self.verify(blob, change)

    def test_corrupt_bpb_and_boot_identifiers(self):
        blob = self.make()
        for offset in (0, 3, 11, 13, 14, 16, 17, 19, 21, 22, 24, 26, 28, 32,
                       36, 37, 38, 43, 54, 62, 200, 510, 511):
            with self.subTest(offset=offset):
                bad = bytearray(blob)
                bad[offset] ^= 0x01
                with self.assertRaises(fat12.ImageError):
                    self.verify(bad)
        for bad in (blob[:-1], blob + b"\0", b""):
            with self.assertRaisesRegex(fat12.ImageError, "length"):
                self.verify(bad)

    def test_corrupt_fat_copy_media_and_padding(self):
        blob = self.make()
        bad = bytearray(blob)
        bad[2048 + 3] ^= 1
        with self.assertRaisesRegex(fat12.ImageError, "copies differ"):
            self.verify(bad)
        bad = bytearray(blob)
        bad[512] = bad[2048] = 0xFD
        with self.assertRaisesRegex(fat12.ImageError, "media"):
            self.verify(bad)
        for cluster in (2, 714, 715, 999):
            with self.subTest(cluster=cluster), self.assertRaises(fat12.ImageError):
                self.verify(mutate_fat(blob, cluster, 0xFFF))

    def test_corrupt_chain_cycle_outside_free_reserved_bad_and_length(self):
        self.put("FILE.BIN", b"x" * 2500)
        blob = self.make()
        for value in (0, 1, 2, 715, 0xFF0, 0xFF7, 0xFFF):
            with self.subTest(value=value), self.assertRaises(fat12.ImageError):
                self.verify(mutate_fat(blob, 2, value))
        with self.assertRaisesRegex(fat12.ImageError, "cycle/cross-link"):
            self.verify(mutate_fat(blob, 4, 2))

    def test_crosslinked_files(self):
        self.put("FIRST", b"a")
        self.put("SECOND", b"b")
        blob = bytearray(self.make())
        root = 3584
        struct.pack_into("<H", blob, root + 2 * 32 + 26, 2)
        with self.assertRaisesRegex(fat12.ImageError, "cycle/cross-link"):
            self.verify(blob)

    def test_file_slack_free_space_and_serial_corruption(self):
        self.put("FILE", b"x")
        original = self.make()
        for offset, message in ((7169, "file slack"), (8192, "free cluster"),
                                (7168, "serial mismatch"), (39, "serial mismatch")):
            with self.subTest(offset=offset):
                blob = bytearray(original)
                blob[offset] ^= 0x01
                with self.assertRaisesRegex(fat12.ImageError, message):
                    self.verify(blob)

    def test_bad_directory_metadata_names_attributes_and_sizes(self):
        self.put("FILE", b"x")
        original = self.make()
        entry = 3584 + 32
        for offset, value in ((0, ord("a")), (11, 0x0F), (12, 1), (20, 1),
                              (22, 1), (24, 0), (26, 0), (28, 0)):
            with self.subTest(offset=offset):
                blob = bytearray(original)
                blob[entry + offset] = value
                with self.assertRaises(fat12.ImageError):
                    self.verify(blob)
        blob = bytearray(original)
        blob[entry + 32 + 12] = 1
        with self.assertRaisesRegex(fat12.ImageError, "unused directory"):
            self.verify(blob)

    def test_corrupt_dot_parent_entries(self):
        (self.source / "SUB" / "DEEP").mkdir(parents=True)
        original = self.make()
        for offset in (7168, 7168 + 26, 7168 + 32, 7168 + 58,
                       8192 + 26, 8192 + 58):
            with self.subTest(offset=offset):
                blob = bytearray(original)
                blob[offset] ^= 1
                with self.assertRaises(fat12.ImageError):
                    self.verify(blob)

    def test_cli_build_verify_and_failure(self):
        self.fixture()
        output = self.base / "TEST.IMG"
        command = [sys.executable, str(HERE / "FAT12.PY")]
        built = subprocess.run(command + ["build", str(self.source), str(output), "--size", "360"],
                               capture_output=True, text=True, check=True)
        verified = subprocess.run(command + ["verify", str(output), "--source", str(self.source)],
                                  capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(built.stdout), json.loads(verified.stdout))
        bad = subprocess.run(command + ["build", str(self.source), str(output), "--size", "1440"],
                             capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)

    def test_crlf_source_files(self):
        for name in ("FAT12.PY", "TESTFAT.PY"):
            data = (HERE / name).read_bytes()
            self.assertIn(b"\r\n", data)
            self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    @unittest.skipUnless(shutil.which("fsck.fat") or shutil.which("fsck.msdos"),
                         "dosfstools not installed")
    def test_external_fsck_readonly(self):
        self.fixture()
        tool = shutil.which("fsck.fat") or shutil.which("fsck.msdos")
        for size in (720, 360):
            output = self.base / ("TEST%d.IMG" % size)
            fat12.build_image(self.source, output, size)
            original = output.read_bytes()
            run = subprocess.run([tool, "-vn", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(output.read_bytes(), original)

    @unittest.skipUnless(shutil.which("mdir") and shutil.which("mcopy"), "mtools not installed")
    def test_external_mtools_read_and_extract(self):
        expected = self.fixture()
        for size in (720, 360):
            output = self.base / ("TEST%d.IMG" % size)
            fat12.build_image(self.source, output, size)
            subprocess.run([shutil.which("mdir"), "-i", str(output), "-s", "::/"],
                           capture_output=True, check=True)
            for path, content in expected.items():
                if content is not None:
                    extracted = self.base / "EXTRACT.BIN"
                    subprocess.run([shutil.which("mcopy"), "-o", "-i", str(output),
                                    "::/" + path, str(extracted)], capture_output=True, check=True)
                    self.assertEqual(extracted.read_bytes(), content)

    @unittest.skipUnless(os.environ.get("FAT12_DOSBOX"), "Set FAT12_DOSBOX for emulator tests")
    def test_external_dosbox_mount_read_nested_and_binary(self):
        expected = self.fixture()
        # Multi-cluster directory and both odd/even FAT chain ends.
        for n in range(40):
            self.put("SUB/DEEP/F%07d.TXT" % n, ("data %d\r\n" % n).encode())
        for size in (720, 360):
            output = self.base / ("TEST%d.IMG" % size)
            fat12.build_image(self.source, output, size)
            original = output.read_bytes()
            commands = ["mount c %s" % self.base,
                        "imgmount a %s -t floppy" % output,
                        "dir a:\\ /s > c:\\LIST%d.TXT" % size,
                        "copy /b a:\\SUB\\DEEP\\THIRD\\FILE.BIN c:\\GOT%d.BIN" % size,
                        "copy a:\\SUB\\DEEP\\F0000039.TXT c:\\END%d.TXT" % size,
                        "exit"]
            args = [os.environ["FAT12_DOSBOX"], "-fastlaunch", "-nopromptfolder"]
            for command in commands:
                args += ["-c", command]
            env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
            run = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual((self.base / ("GOT%d.BIN" % size)).read_bytes(),
                             expected["SUB/DEEP/THIRD/FILE.BIN"])
            self.assertEqual((self.base / ("END%d.TXT" % size)).read_bytes(), b"data 39\r\n")
            listing = (self.base / ("LIST%d.TXT" % size)).read_text()
            self.assertIn("Directory of A:\\SUB\\DEEP\\THIRD", listing)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
