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
F = importlib.machinery.SourceFileLoader("pcjsflp", str(HERE / "PCJSFLP.PY")).load_module()
K = importlib.machinery.SourceFileLoader("jrchk", str(HERE / "JRCHK.PY")).load_module()
G = importlib.machinery.SourceFileLoader("jrgrtest", str(HERE / "JRGRTEST.PY")).load_module()
T = importlib.machinery.SourceFileLoader("jrmodet", str(HERE / "JRMODET.PY")).load_module()
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


class Diskette(unittest.TestCase):
    """PCJSFLP: PCjs diskette JSON -> raw image, refused unless PCjs's MD5 matches."""

    def disk(self, mutate=None):
        import hashlib as h
        import struct
        sectors, raw = [], bytearray()
        for n in range(1, 3):
            data = bytes([n]) * 16 + b"\x01\xf7\xff\x00" + b"\0" * 492
            words = list(struct.unpack("<%di" % (len(data) // 4), data))
            while len(words) > 1 and words[-1] == words[-2]:
                words.pop()                          # PCjs: a short list repeats its last word
            sectors.append({"c": 0, "h": 0, "s": n, "l": 512, "d": words})
            raw += data
        if mutate:
            mutate(sectors)
        return {"imageInfo": {"type": "CHS", "hash": h.md5(bytes(raw)).hexdigest(), "diskSize": len(raw)},
                "diskData": [[sectors]]}

    def test_exact_image(self):
        d = self.disk()
        self.assertEqual(len(F.convert(d)), 1024)

    def test_altered_sector_refused(self):
        # the defect that damaged the first private copy: sector data changed
        def m(sectors):
            sectors[1]["d"] = sectors[1]["d"][:5]     # drops the explicit zero words
        with self.assertRaises(F.Refused):
            F.convert(self.disk(m))

    def test_wrong_hash_refused(self):
        d = self.disk()
        d["imageInfo"]["hash"] = "0" * 32
        with self.assertRaises(F.Refused):
            F.convert(d)

    def test_not_chs_refused(self):
        d = self.disk()
        d["imageInfo"]["type"] = "RAW"
        with self.assertRaises(F.Refused):
            F.convert(d)


class Checkers(unittest.TestCase):
    """The emulator checks accept only the intended evidence."""
    REFUSED = K.GUARD_REFUSED + K.JRWIN_REFUSED

    def test_refusal_accepted_only_for_jrguard_refusal(self):
        self.assertTrue(K.guard_refused_launch(self.REFUSED, "1")[0])

    def test_refusal_other_jrwin_failures_rejected(self):
        for text in (b"JRWIN: missing C:\\WINDOWS\\WIN.COM. Windows not started.\r\n",
                     b"JRWIN: Windows failed or terminated abnormally.\r\n",
                     b"JRGUARD: not an IBM PCjr (F000:FFFE is not FDh).\r\n" + K.JRWIN_REFUSED,
                     b"JRGUARD: DOS memory chain is not valid. Not starting.\r\n" + K.JRWIN_REFUSED,
                     b"", K.JRWIN_REFUSED):
            self.assertFalse(K.guard_refused_launch(text, "1")[0], text)

    def test_refusal_wrong_exit_code_rejected(self):
        for rc in ("0", "2", "5+", None):
            self.assertFalse(K.guard_refused_launch(self.REFUSED, rc)[0], rc)

    def test_guard_pass_needs_its_own_text_and_zero(self):
        self.assertTrue(K.guard_passed(K.GUARD_OK_OWNED, "0")[0])
        self.assertFalse(K.guard_passed(K.GUARD_OK_OWNED, "1")[0])
        self.assertFalse(K.guard_passed(b"JRGUARD: OK, DOS memory ends below the video page.\r\n", "0")[0])
        self.assertFalse(K.guard_passed(b"", "0")[0])

    def test_rc_lines(self):
        self.assertEqual(K.rc_lines("GUARD RC=0 \r\nHELD RC=1\r\n"), {"GUARD": "0", "HELD": "1"})
        self.assertEqual(K.rc_lines("A RC=0\r\nA RC=0\r\n")["A"], "duplicate")

    def test_every_display_entry_counted(self):
        extra = INF.replace("[sysfonts]", 'VGA = a:VGA.DRV, "Another", "100,96,96", a:JRGRAB.GR2\r\n\r\n[sysfonts]')
        self.assertEqual(len(K.inf_display_entries(extra)), 2)
        with self.assertRaises(P.Refused):
            P.check_inf(extra, Inf.present | {"VGA.DRV"})

    def test_only_entry_must_be_tndyjr(self):
        other = INF.replace("TNDYJR = a:TNDYJR.DRV", "PCJR = a:TNDYJR.DRV")
        with self.assertRaises(P.Refused):
            P.check_inf(other, Inf.present)

    def szdd(self, payload):
        # literal-only SZDD stream: one flag byte (all literals) per 8 bytes
        import struct
        body = bytearray()
        for i in range(0, len(payload), 8):
            chunk = payload[i:i + 8]
            body.append((1 << len(chunk)) - 1)
            body += chunk
        return b"SZDD\x88\xf0\x27\x33A\0" + struct.pack("<I", len(payload)) + bytes(body)

    def test_szdd_literals_and_backreference(self):
        self.assertEqual(K.szdd_expand(self.szdd(b"WIN.CNF content")), b"WIN.CNF content")
        # 'abc' then a 6-byte copy from window position 4080 (where 'abc' went)
        data = b"SZDD\x88\xf0\x27\x33A\0" + (9).to_bytes(4, "little") + bytes([0b0111, 97, 98, 99, 0xF0, 0xF3])
        self.assertEqual(K.szdd_expand(data), b"abcabcabc")
        with self.assertRaises(ValueError):
            K.szdd_expand(b"MZ" + bytes(20))

    def test_win_com_must_be_cnf_plus_static_logo(self):
        cnf, lgo, rle = b"C" * 30, b"L" * 7, b"R" * 9
        media = self.szdd(cnf)
        self.assertTrue(K.win_com_static_logo(cnf + lgo + rle, cnf, media, lgo, rle)[0])
        self.assertFalse(K.win_com_static_logo(cnf + b"CGALOGO" + rle, cnf, media, lgo, rle)[0])
        self.assertFalse(K.win_com_static_logo(cnf + lgo + rle[:-1] + b"X", cnf, media, lgo, rle)[0])
        self.assertFalse(K.win_com_static_logo(cnf + lgo + rle, b"D" * 30, media, lgo, rle)[0])
        # the old size-only check would have passed this one
        same_size = cnf + rle[:7] + lgo + rle[7:]
        self.assertEqual(len(same_size), len(cnf + lgo + rle))
        self.assertFalse(K.win_com_static_logo(same_size, cnf, media, lgo, rle)[0])

    def mode(self, **kw):
        r = dict(program_screen_shown=True, desktop_after_equals_first=True, program_intact=True)
        r.update(kw)
        return r

    def good_modes(self):
        out = {}
        for m in G.MODES:
            if m in G.PCJR_ONLY:
                out[m] = self.mode(switched_to_windows=False, screen_undisturbed=True)
            else:
                out[m] = self.mode(switched_to_windows=True, restored_exact=True)
        return out

    def test_grabber_design_accepts_intended_behaviour(self):
        self.assertEqual(G.jrgrab_expected(self.good_modes()), {})

    def test_grabber_design_rejects_each_bad_case(self):
        cases = [("9", dict(switched_to_windows=True, restored_exact=True)),   # PCjr mode switched
                 ("A", dict(screen_undisturbed=False)),                         # refused but screen changed
                 ("3", dict(restored_exact=False)),                             # text not restored
                 ("4", dict(switched_to_windows=False, screen_undisturbed=True)),  # CGA mode refused
                 ("8", dict(program_intact=False)),                             # JRMODE read back BAD
                 ("6", dict(desktop_after_equals_first=False)),
                 ("1", dict(program_screen_shown=False))]
        for m, change in cases:
            modes = self.good_modes()
            modes[m] = dict(modes[m], **change)
            self.assertIn(m, G.jrgrab_expected(modes), (m, change))

    def test_jrmode_self_test_judge(self):
        good = [("3", False, "MODE 3 OK"), ("A", False, "MODE A OK READ 1900"),
                ("4", True, "MODE 4 BAD 0001"), ("A", True, "MODE A BAD 0001 READ 1900")]
        bad = [("4", True, "MODE 4 OK"),            # injected fault not detected
               ("4", False, "MODE 4 BAD 0002"),     # undisturbed run reported a change
               ("4", True, "MODE 4 BAD 0002"),      # fault count wrong
               ("4", False, None), ("4", False, "MODE 5 OK")]
        for m, fault, text in good:
            self.assertTrue(T.judge(m, fault, text), text)
        for m, fault, text in bad:
            self.assertFalse(T.judge(m, fault, text), text)


class JrmodeScreens(unittest.TestCase):
    """JRCHK.jrmode_screen: only JRMODE's own screen for the mode passes."""

    @staticmethod
    def synth(m):
        spec = K.JRMODE_SCREENS[m]
        img = bytearray(640 * 400 * 3)

        def put(x, y, c):
            i = (y * 640 + x) * 3
            img[i:i + 3] = bytes(c)
        if spec[0] == "graphics":
            _, width, pal = spec
            sx = 640 // width
            for y in range(200):
                for x in range(width):
                    if 40 <= y < 56:
                        c = pal[((x >> 3) + y) & (len(pal) - 1)]
                    elif y < 8 and x < 8:
                        c = pal[-1]                      # a title pixel
                    else:
                        continue
                    for dx in range(sx):
                        for dy in range(2):
                            put(x * sx + dx, 2 * y + dy, c)
        else:
            cw = 640 // spec[1]
            for i in range(15):
                for y in range(84, 92):
                    put(i * cw + 1, y, K.IRGB[i + 1])   # a stroke of the glyph
            put(3, 3, K.IRGB[7])                         # the title
        return (640, 400), bytes(img)

    def test_each_mode_accepted(self):
        for m in K.JRMODE_SCREENS:
            ok, detail = K.jrmode_screen(m, self.synth(m))
            self.assertTrue(ok, (m, detail))

    def test_blank_missing_and_wrong_size_rejected(self):
        for m in K.JRMODE_SCREENS:
            self.assertFalse(K.jrmode_screen(m, ((640, 400), bytes(640 * 400 * 3)))[0], m)
            self.assertFalse(K.jrmode_screen(m, None)[0], m)
            self.assertFalse(K.jrmode_screen(m, ((320, 200), bytes(320 * 200 * 3)))[0], m)
        self.assertFalse(K.jrmode_screen("7", self.synth("3"))[0])

    def test_wrong_mode_rejected(self):
        # Pairs that DOSBox-X renders identically (colour burst only) cannot differ.
        same = {frozenset("45"), frozenset("01"), frozenset("23")}
        for a in K.JRMODE_SCREENS:
            for b in K.JRMODE_SCREENS:
                if a != b and frozenset(a + b) not in same:
                    self.assertFalse(K.jrmode_screen(b, self.synth(a))[0], f"mode {a} screen accepted as {b}")

    def test_single_pixel_faults_rejected(self):
        for m, (x, y) in (("8", (100, 90)), ("A", (5, 300)), ("9", (0, 98)), ("3", (600, 300))):
            size, img = self.synth(m)
            img = bytearray(img)
            i = (y * 640 + x) * 3
            img[i:i + 3] = b"\x55\x55\x55"
            self.assertFalse(K.jrmode_screen(m, (size, bytes(img)))[0], (m, x, y))

    def test_committed_captures(self):
        docs = HERE.parents[2] / "docs" / "pcjr" / "INSTALL"
        found = 0
        for name, m in (("GRJRM8.PNG", "8"), ("GRMODE9.PNG", "9"), ("GRJRMA.PNG", "A"), ("GRJRM4.PNG", "4")):
            if not (docs / name).exists():
                continue
            try:
                from PIL import Image
            except ImportError:
                self.skipTest("Pillow not installed")
            with Image.open(docs / name) as im:
                cap = (im.size, im.convert("RGB").tobytes())
            found += 1
            for other in K.JRMODE_SCREENS:
                want = other == m or frozenset(other + m) == frozenset("45")
                self.assertEqual(K.jrmode_screen(other, cap)[0], want, (name, other))
        if not found:
            self.skipTest("docs/pcjr/INSTALL captures not checked out")


class Pins(unittest.TestCase):
    def test_grabber_pin_shape(self):
        import json
        p = json.loads((HERE / "PINS.JSN").read_text())["JRGRAB.GR2"]
        self.assertRegex(p["sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
