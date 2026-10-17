#!/usr/bin/env python3
"""Host tests for the PCjr install folder (JRPACK.PY), OEMSETUP.INF and
INSTALL.TXT. Synthetic fixtures only: no emulator, no Microsoft file.
MIT, Copyright (c) 2026 Windows XT contributors.
"""
import hashlib
import importlib.machinery
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader("jrpack", str(HERE / "JRPACK.PY")).load_module()
INF = (HERE / "OEMSETUP.INF").read_bytes().decode("ascii")


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Inf(unittest.TestCase):
    present = {"TNDYJR.DRV", "JRGRAB.GR2", "XTSTATIC.LGO", "WXTSPL01.RLE", "XTESYS.FON",
               "XTEFIX.FON", "XTEOEM.FON", "OEMSETUP.INF"}

    def refused(self, text, present=None):
        with self.assertRaises(P.Refused):
            P.check_inf(text, present or self.present)

    def test_current_inf_accepted(self):
        desc = P.check_inf(INF, self.present)
        self.assertTrue(desc.startswith("EXPERIMENTAL") and "PCjr" in desc)

    def test_inf_names_no_microsoft_grabber_or_font(self):
        up = INF.upper()
        for name in ("CGA.GR2", "EGA.GR2", "CGASYS.FON", "EGASYS.FON", "CGAFIX.FON", "CGAOEM.FON"):
            self.assertNotIn("A:" + name, up)

    def test_lf_refused(self):
        self.refused(INF.replace("\r\n", "\n"))

    def test_stock_cga_grabber_refused(self):
        self.refused(INF.replace("a:JRGRAB.GR2", "a:CGA.GR2"), self.present | {"CGA.GR2"})

    def test_unlabelled_selector_refused(self):
        self.refused(INF.replace('"EXPERIMENTAL IBM PCjr', '"IBM PCjr'))

    def test_long_selector_refused(self):
        self.refused(INF.replace("16 colors", "16 colors and a much longer label"))

    def test_relative_disk_refused(self):
        self.refused(INF.replace("a = C:\\PCJREXP,", "a = .,"))

    def test_second_row_refused(self):
        row = next(l for l in INF.split("\r\n") if l.startswith("TNDYJR"))
        self.refused(INF.replace(row, row + "\r\n" + row))

    def test_missing_file_refused(self):
        self.refused(INF, self.present - {"XTEOEM.FON"})


class InstallText(unittest.TestCase):
    def test_crlf_ascii_and_width(self):
        raw = (HERE / "INSTALL.TXT").read_bytes()
        raw.decode("ascii")
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        for line in raw.split(b"\r\n"):
            self.assertLessEqual(len(line), 76, line)

    def test_names_guarded_launch(self):
        text = (HERE / "INSTALL.TXT").read_text()
        self.assertIn("C:\\PCJREXP\\JRWIN", text)
        self.assertIn("C:\\PCJREXP\\JRGUARD", text)


class Build(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.bin = self.root / "bin"
        self.winxt = self.root / "winxt"
        self.bin.mkdir()
        self.winxt.mkdir()
        self.pins = {}
        for n in ("TNDYJR.DRV", "JRGUARD.COM", "JRWIN.COM", "JRGRAB.GR2"):
            data = b"SYNTHETIC " + n.encode()
            (self.bin / n).write_bytes(data)
            self.pins[n] = sha(data)
        self.first = {}
        for n in P.FIRST_PARTY:
            data = b"SYNTHETIC " + n.encode()
            (self.winxt / n).write_bytes(data)
            self.first[n] = sha(data) if P.FIRST_PARTY[n] else None
        for p in (patch.object(P, "pins", lambda: dict(self.pins)), patch.object(P, "WINXT", self.winxt),
                  patch.object(P, "FIRST_PARTY", self.first)):
            p.start()
            self.addCleanup(p.stop)

    def test_builds_folder_with_sums(self):
        out = self.root / "out"
        desc, names = P.build(self.bin, out)
        self.assertIn("PCjr", desc)
        sums = (out / "SHA256.SUM").read_bytes().decode().split("\r\n")
        listed = {l.split("  ")[1]: l.split("  ")[0] for l in sums if l}
        self.assertEqual(set(listed), set(names))
        for n, h in listed.items():
            self.assertEqual(sha((out / n).read_bytes()), h)
        self.assertNotIn("CGA.GR2", names)

    def test_wrong_driver_refused(self):
        (self.bin / "TNDYJR.DRV").write_bytes(b"other")
        with self.assertRaises(P.Refused):
            P.build(self.bin, self.root / "out")
        self.assertFalse((self.root / "out").exists())

    def test_missing_grabber_refused(self):
        (self.bin / "JRGRAB.GR2").unlink()
        with self.assertRaises(P.Refused):
            P.build(self.bin, self.root / "out")

    def test_changed_font_refused(self):
        (self.winxt / "XTESYS.FON").write_bytes(b"changed")
        with self.assertRaises(P.Refused):
            P.build(self.bin, self.root / "out")

    def test_existing_out_refused(self):
        (self.root / "out").mkdir()
        with self.assertRaises(P.Refused):
            P.build(self.bin, self.root / "out")

    def test_cli_exit_code(self):
        (self.bin / "JRWIN.COM").write_bytes(b"other")
        self.assertEqual(P.main(["--bin", str(self.bin), "--out", str(self.root / "o")]), 1)


class Pins(unittest.TestCase):
    def test_grabber_pin_shape(self):
        import json
        p = json.loads((HERE / "PINS.JSN").read_text())["JRGRAB.GR2"]
        self.assertRegex(p["sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
