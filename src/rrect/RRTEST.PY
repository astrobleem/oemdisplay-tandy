#!/usr/bin/env python3
"""Host tests for the RoundRect investigation tools (no emulator, no DDK).

  python3 -B src/rrect/RRTEST.PY

RRCMP must pass only byte-identical frames: a single changed pixel, a
changed padding byte, a missing dump, a missing stage and a different API
result each fail. RRPATCH's trace record decoder and the candidate/mutant
patch texts are checked against a synthetic TOutput gate carrying the exact
anchors the patches require (each anchor must match exactly once).
"""
import importlib.machinery
import struct
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = importlib.machinery.SourceFileLoader("rrcmp", str(HERE / "RRCMP.PY")).load_module()
P = importlib.machinery.SourceFileLoader("rrpatch", str(HERE / "RRPATCH.PY")).load_module()

LOG = ("VERSION=2\r\nSTAGE=1\r\nNAME=roundrect_key\r\nELAPSED_MS=100\r\nAPI_SUCCESSES=20\r\n"
       "STAGE=2\r\nNAME=calc\r\nREPAINT_MS=50\r\nCOMPLETE=1\r\n")

# The exact staged-source anchors the patches edit (from BUILD88's TR5 stage).
GATE = ("sBegin Data\r\npublic enabled_flag,ScratchSel,is_protected,_cstods,diag_markers\r\n"
        "    cmp style,4\r\n    jne TOutput_thin_count\r\n"
        "TOutput_thin_count:\r\n    cmp style,18\r\n    or_require je,TOutput_render\r\n"
        "    cmp count,2\r\n    or_require je,TOutput_render\r\nTOutput_style_ok:\r\n"
        "TOutput_polyline:\r\n    mov cx,es:[di]\r\n"
        "    popf\r\n    cCall Output,<dst,style,count,points,pen,brush,mode,clip>\r\n"
        "    cmp dirty,0\r\n    je TOutput_done\r\n"
        "    ; Preserve the actual renderer result and all post-render GPRs.\r\n"
        "    parmD output\r\ncBegin\r\n    xor ax,ax\r\n    les di,input\r\n    mov bx,function\r\n")


def frame(fill=0x11):
    return bytes([fill]) * 32768


def run_dir(root, name, dumps, log=LOG):
    d = root / name
    d.mkdir()
    (d / "RRBENCH.LOG").write_text(log)
    for n, data in dumps.items():
        (d / f"RB{n:02d}.BIN").write_bytes(data)
    return d


class Compare(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)

    def cmp(self, a, b):
        return C.main([str(a), str(b)])

    def test_identical_runs_pass(self):
        a = run_dir(self.root, "a", {1: frame(), 2: frame(0x22)})
        b = run_dir(self.root, "b", {1: frame(), 2: frame(0x22)})
        self.assertEqual(self.cmp(a, b), 0)

    def test_one_pixel_fails_with_its_position(self):
        f = bytearray(frame())
        f[(41 % 4) * 8192 + (41 // 4) * 160 + 101 // 2] ^= 0x0F      # x=101 (odd: low nibble), y=41
        r = C.compare_dumps(frame(), bytes(f))
        self.assertFalse(r["equal"])
        self.assertEqual(r["differing_pixels"], 1)
        self.assertEqual(r["bbox"], [101, 41, 101, 41])
        a = run_dir(self.root, "a", {1: frame(), 2: frame()})
        b = run_dir(self.root, "b", {1: bytes(f), 2: frame()})
        self.assertEqual(self.cmp(a, b), 1)

    def test_padding_byte_fails(self):
        f = bytearray(frame())
        f[8000] ^= 1                                                  # bank 0 padding, not displayed
        r = C.compare_dumps(frame(), bytes(f))
        self.assertFalse(r["equal"])
        self.assertEqual(r["differing_pixels"], 0)

    def test_missing_dump_and_stage_fail(self):
        a = run_dir(self.root, "a", {1: frame(), 2: frame()})
        b = run_dir(self.root, "b", {1: frame()})
        self.assertEqual(self.cmp(a, b), 1)
        c = run_dir(self.root, "c", {1: frame(), 2: frame()}, log=LOG.split("STAGE=2")[0])
        self.assertEqual(self.cmp(a, c), 1)

    def test_api_result_difference_fails(self):
        a = run_dir(self.root, "a", {1: frame(), 2: frame()})
        b = run_dir(self.root, "b", {1: frame(), 2: frame()}, log=LOG.replace("API_SUCCESSES=20", "API_SUCCESSES=19"))
        self.assertEqual(self.cmp(a, b), 1)

    def test_timings_are_not_compared(self):
        a = run_dir(self.root, "a", {1: frame(), 2: frame()})
        b = run_dir(self.root, "b", {1: frame(), 2: frame()}, log=LOG.replace("ELAPSED_MS=100", "ELAPSED_MS=3"))
        self.assertEqual(self.cmp(a, b), 0)


class Patches(unittest.TestCase):
    def test_trace_records_decode(self):
        rec = struct.pack("<HHBBBBHhhhhH", 18, 17, 3, 13, 2, 0, 0xFFFF, 4, 18, 4, 29, 17)
        r = P.decode_records(rec * 2)
        self.assertEqual(len(r), 2)
        self.assertEqual((r[0]["style"], r[0]["count"], r[0]["bounded"], r[0]["y"], r[0]["x"]),
                         (18, 17, True, [4, 18], [4, 29]))

    def test_patches_apply_exactly_once(self):
        for fn in (P.patch_trace, P.patch_candidate, P.patch_noflush, P.patch_nodraw,
                   P.patch_mut_lastrow, P.patch_mut_firstrow, P.patch_mut_scanskip):
            out = fn(GATE)
            self.assertNotEqual(out, GATE, fn.__name__)
        cand = P.patch_candidate(GATE)
        self.assertIn("cmp style,80", cand)
        self.assertIn(f"cmp count,{P.RR_POLY_MAX}", cand)
        self.assertIn("    inc bx\r\n    mov lastrow,bx\r\n", cand)
        self.assertNotIn("    inc bx\r\n    mov lastrow,bx\r\n", P.patch_mut_lastrow(GATE).split("TOutput_poly_point")[1]
                         .split("TOutput_two_point")[0])

    def test_patch_refuses_missing_or_repeated_anchor(self):
        with self.assertRaises(SystemExit):
            P.patch_candidate(GATE.replace("TOutput_polyline:", "TOutput_line:"))
        with self.assertRaises(SystemExit):
            P.patch_candidate(GATE + GATE)


if __name__ == "__main__":
    unittest.main()
