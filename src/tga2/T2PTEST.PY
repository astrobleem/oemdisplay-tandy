"""Host packet/font/SZDD refusal checks; no installer or emulator execution."""
import importlib.machinery
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader("t2pack_test", str(HERE / "T2PACK.PY")).load_module()




def compressed_grabber():
    raw = (P.ROOT / 'distributions/WINXT/CGA.GR2').read_bytes()
    body = b''.join(bytes([(1 << len(raw[i:i+8])) - 1]) + raw[i:i+8]
                    for i in range(0, len(raw), 8))
    return b'SZDD\x88\xf0\x27\x33A\x00' + len(raw).to_bytes(4, 'little') + body

class Packets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="t2font-host-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.actual_specs = P.specs
        real = self.actual_specs()
        self.runtime = {n: ("synthetic runtime " + n).encode("ascii") for n in real["runtime"]}
        self.pins = {"runtime": {n: P.identity(b) for n, b in self.runtime.items()},
                     "support": real["support"], "accepted_metadata": real["accepted_metadata"]}
        P.specs = lambda: self.pins
        self.addCleanup(setattr, P, "specs", self.actual_specs)
        original = dict(self.runtime)
        original["NOTICE.TXT"] = (P.ROOT / "src/tga2/HISTORY/NOTER2.TXT").read_bytes()
        original.update({n: b"historical fixture" for n in
                         ("OEMSETUP.INF", "PREPINF.BAT", "README.TXT", "PINS.JSN", "SHA256.SUM")})
        self.original = original
        self.accepted = self.base / "OLD.ZIP"
        self.accepted.write_bytes(P.archive(original))

    def build(self, name="new", grabber=None):
        out = self.base / name
        P.prepare(self.accepted, out, grabber)
        return out

    def test_current_packet_is_closed_reproducible_and_uses_original_fonts(self):
        a = self.build("a")
        b = self.build("b")
        self.assertEqual((a / "TNDYV2.ZIP").read_bytes(), (b / "TNDYV2.ZIP").read_bytes())
        record = P.verify_bytes((a / "TNDYV2.ZIP").read_bytes())
        self.assertEqual(record["selected_fonts"]["fonts.fon"], "XTCSYS.FON")
        self.assertEqual(record["external_support_inputs"], [])
        for name, data in self.runtime.items():
            self.assertEqual((a / "T2EXP" / name).read_bytes(), data)
        for name in self.pins["support"]:
            self.assertEqual(P.identity((a / "T2EXP" / name).read_bytes()), self.pins["support"][name])
        self.assertFalse((a / "T2EXP/CGA.GR2").read_bytes().startswith(b"SZDD"))

    def test_changed_driver_rejected_before_output(self):
        original = dict(self.original)
        original["TNDYV2.DRV"] += b"changed"
        self.accepted.write_bytes(P.archive(original))
        with self.assertRaisesRegex(ValueError, "Qualified bytes differ"):
            self.build()
        self.assertFalse((self.base / "new").exists())

    def test_existing_output_refused(self):
        out = self.build()
        before = (out / "TNDYV2.ZIP").read_bytes()
        with self.assertRaisesRegex(ValueError, "must be new"):
            self.build()
        self.assertEqual(before, (out / "TNDYV2.ZIP").read_bytes())

    def test_extra_or_duplicate_accepted_members_refused(self):
        original = dict(self.original)
        original["UNRELATED.TXT"] = b"extra"
        self.accepted.write_bytes(P.archive(original))
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            self.build()
        self.accepted.write_bytes(P.archive(self.original))
        with zipfile.ZipFile(self.accepted, "a") as z:
            z.writestr("TNDYV2.DRV", b"duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.build()

    def test_supplied_szdd_and_expanded_grabber_match(self):
        compressed = compressed_grabber()
        expanded = P.MEDIA.expanded_file(compressed, "CGA.GR2")
        path = self.base / "CGA.GR2"
        path.write_bytes(expanded)
        a = self.build("a")
        b = self.build("b", path)
        self.assertEqual((a / "TNDYV2.ZIP").read_bytes(), (b / "TNDYV2.ZIP").read_bytes())

    def test_malformed_or_wrong_szdd_refused_before_output(self):
        good = compressed_grabber()
        cases = [good[:13], good[:-1], good + b"extra", good[:8] + b"B" + good[9:], b"wrong"]
        for i, data in enumerate(cases):
            path = self.base / ("BAD" + str(i))
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                self.build("new" + str(i), path)
            self.assertFalse((self.base / ("new" + str(i))).exists())

    def test_old_stock_font_mapping_refused(self):
        raw = (HERE / "OEMSETUP.INF").read_bytes()
        for current, stock in [(b"XTCSYS.FON", b"CGASYS.FON"), (b"XTCFIX.FON", b"CGAFIX.FON"),
                               (b"XTCOEM.FON", b"CGAOEM.FON")]:
            with self.assertRaises(ValueError):
                P.INF.verify(raw.replace(current, stock))

    def test_legacy_logo_mapping_refused(self):
        raw = (HERE / "OEMSETUP.INF").read_bytes()
        for current, old in [(b"XTSTATIC.LGO", b"CGALOGO.LGO"),
                             (b"WXTSPL01.RLE", b"CGALOGO.RLE")]:
            with self.assertRaises(ValueError):
                P.INF.verify(raw.replace(current, old))

    def test_native_claim_or_font_record_drift_refused(self):
        out = self.build()
        with zipfile.ZipFile(out / "TNDYV2.ZIP") as z:
            files = {n: z.read(n) for n in z.namelist()}
        for key, value in [("native_setup_test", "PASS"), ("selected_fonts", {})]:
            altered = dict(files)
            record = json.loads(altered["PINS.JSN"])
            record[key] = value
            altered["PINS.JSN"] = P.dos(json.dumps(record))
            altered["SHA256.SUM"] = P.manifest({n: b for n, b in altered.items() if n != "SHA256.SUM"})
            with self.assertRaises(ValueError):
                P.verify_bytes(P.archive(altered))

    def test_prepinf_only_checks_complete_packet(self):
        text = (HERE / "PREPINF.BAT").read_text()
        copies = [line for line in text.splitlines() if line.startswith("COPY ")]
        self.assertEqual(copies, [])
        for name in ("XTCSYS.FON", "XTCFIX.FON", "XTCOEM.FON", "CGA.GR2",
                     "XTSTATIC.LGO", "WXTSPL01.RLE"):
            self.assertIn("IF NOT EXIST " + name + " GOTO MISSING", text)


if __name__ == "__main__":
    unittest.main()
