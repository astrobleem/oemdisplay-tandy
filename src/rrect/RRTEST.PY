#!/usr/bin/env python3
"""Host tests for the RoundRect investigation tools (no emulator, no DDK).

  python3 -B src/rrect/RRTEST.PY

RRCMP must pass only complete runs with byte-identical frames: logs truncated
anywhere, missing or short API counts, missing stages, applications or dumps
fail even when both runs are equally incomplete; a single changed pixel, a
changed padding byte, a missing dump and a different API result each fail.
The committed logs must be complete and must fail once truncated. RRPATCH's trace record decoder and the candidate/mutant
patch texts are checked against a synthetic TOutput gate carrying the exact
anchors the patches require (each anchor must match exactly once).
"""
import hashlib
import importlib.machinery
import json
import struct
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = importlib.machinery.SourceFileLoader("rrcmp", str(HERE / "RRCMP.PY")).load_module()
P = importlib.machinery.SourceFileLoader("rrpatch", str(HERE / "RRPATCH.PY")).load_module()

def make_log(version=3, shots=0, api=None, repaints=3):
    """A complete RRBENCH log in the probe's own format (see RRBENCH.C)."""
    L = [f"VERSION={version}", "SCREEN_WIDTH=320", "SCREEN_HEIGHT=200", "MULTIPLIER=1"]
    if version >= 3:
        L.append(f"SHOTS={shots}")
    for n, name in enumerate(C.expected_names(version, shots), 1):
        L += ["CLEAR_SUCCESS=1", f"STAGE={n}", f"NAME={name}"]
        if name in C.APPS:
            L += ["WINEXEC=33", "APP_FOUND=1" if version >= 2 else "CALC_FOUND=1"]
            L += [f"TITLE={name.title()}"] if version >= 2 else []
            L += ["LAUNCH_TO_PAINTED_MS=900"] + ["REPAINT_MS=500"] * repaints
        else:
            L += ["KIND=1", "COUNT=20", "ELAPSED_MS=100", f"API_SUCCESSES={20 if api is None else api}"]
        L += ["TRACE_RECORDS=-1", "TRACE_LOST=0", "DUMP_CREATED=1", "DUMP_BYTES=32768"]
    L.append("COMPLETE=1")
    return "\r\n".join(L) + "\r\n"


LOG = make_log()
N = len(C.expected_names(3, 0))


# The exact staged-source anchors the patches edit (from BUILD88's TR5 stage).
GATE = ("sBegin Data\r\npublic enabled_flag,ScratchSel,is_protected,_cstods,diag_markers\r\n"
        "    cmp style,4\r\n    jne TOutput_thin_count\r\n"
        "TOutput_thin_count:\r\n    cmp style,18\r\n    or_require je,TOutput_render\r\n"
        "    cmp count,2\r\n    or_require je,TOutput_render\r\nTOutput_style_ok:\r\n"
        "    jmp short TOutput_bounded\r\nTOutput_polyline:\r\n    mov cx,es:[di]\r\n"
        "    popf\r\n    cCall Output,<dst,style,count,points,pen,brush,mode,clip>\r\n"
        "    cmp dirty,0\r\n    je TOutput_done\r\n"
        "    ; Preserve the actual renderer result and all post-render GPRs.\r\n"
        "    parmD output\r\ncBegin\r\n    xor ax,ax\r\n    les di,input\r\n    mov bx,function\r\n")


def frame(fill=0x11):
    return bytes([fill]) * 32768


def run_dir(root, name, dumps=None, log=LOG):
    d = root / name
    d.mkdir()
    (d / "RRBENCH.LOG").write_text(log, newline="")
    if dumps is None:
        dumps = {n: frame() for n in range(1, N + 1)}
    for n, data in dumps.items():
        (d / f"RB{n:02d}.BIN").write_bytes(data)
    return d


def truncated(log, upto):
    """The log as if the probe (or the run) stopped before line index upto."""
    return "".join(log.splitlines(keepends=True)[:upto])


class Compare(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.k = 0

    def cmp(self, a, b):
        return C.main([str(a), str(b)])

    def pair(self, log_a, log_b=None, dumps_a=None, dumps_b=None):
        self.k += 1
        return (run_dir(self.root, f"a{self.k}", dumps_a, log_a),
                run_dir(self.root, f"b{self.k}", dumps_b, log_a if log_b is None else log_b))

    def test_complete_identical_runs_pass(self):
        self.assertEqual(C.validate(LOG)[1], [])
        self.assertEqual(self.cmp(*self.pair(LOG)), 0)
        v1 = make_log(version=1)
        self.assertEqual(C.validate(v1)[1], [])
        self.assertEqual(self.cmp(*self.pair(v1, dumps_a={n: frame() for n in range(1, 11)},
                                             dumps_b={n: frame() for n in range(1, 11)})), 0)

    def test_equally_truncated_runs_fail(self):
        lines = LOG.splitlines(keepends=True)
        cuts = [len(lines) - 1] + [i for i, l in enumerate(lines) if l.startswith("STAGE=")][1:] + [8, 20]
        for cut in cuts:
            log = truncated(LOG, cut)
            self.assertNotEqual(C.validate(log)[1], [], cut)
            self.assertEqual(self.cmp(*self.pair(log)), 1, cut)

    def test_equally_missing_api_counts_fail(self):
        for log in (LOG.replace("API_SUCCESSES=20\r\n", ""),                       # every batch
                    LOG.replace("API_SUCCESSES=20\r\n", "", 1),                    # one batch
                    LOG.replace("API_SUCCESSES=20", "API_SUCCESSES=", 1),
                    make_log(api=19),                                               # some calls failed
                    LOG.replace("COUNT=20\r\n", "", 1)):
            self.assertNotEqual(C.validate(log)[1], [])
            self.assertEqual(self.cmp(*self.pair(log)), 1)

    def test_equally_missing_cases_fail(self):
        no_stage = LOG.replace("NAME=roundrect_clipped", "NAME=roundrect_key")
        no_app = LOG.replace("APP_FOUND=1", "APP_FOUND=0", 1)
        short = make_log(repaints=2)
        no_dump = LOG.replace("DUMP_BYTES=32768", "DUMP_BYTES=0", 1)
        no_clear = LOG.replace("CLEAR_SUCCESS=1", "CLEAR_SUCCESS=0", 1)
        no_title = LOG.replace("TITLE=Calc", "TITLE=", 1)
        no_version = LOG.replace("VERSION=3\r\n", "")
        twice = LOG + "COMPLETE=1\r\n"
        early = LOG.replace("COMPLETE=1\r\n", "").replace(f"STAGE={N}\r\n", f"COMPLETE=1\r\nSTAGE={N}\r\n")
        for log in (no_stage, no_app, short, no_dump, no_clear, no_title, no_version, twice, early):
            self.assertNotEqual(C.validate(log)[1], [])
            self.assertEqual(self.cmp(*self.pair(log)), 1)

    def test_runs_of_different_probe_setups_fail(self):
        self.assertEqual(self.cmp(*self.pair(LOG, LOG.replace("MULTIPLIER=1", "MULTIPLIER=2"))), 1)

    def test_one_pixel_fails_with_its_position(self):
        f = bytearray(frame())
        f[(41 % 4) * 8192 + (41 // 4) * 160 + 101 // 2] ^= 0x0F      # x=101 (odd: low nibble), y=41
        r = C.compare_dumps(frame(), bytes(f))
        self.assertFalse(r["equal"])
        self.assertEqual(r["differing_pixels"], 1)
        self.assertEqual(r["bbox"], [101, 41, 101, 41])
        bad = {n: frame() for n in range(1, N + 1)}
        bad[11] = bytes(f)
        self.assertEqual(self.cmp(*self.pair(LOG, dumps_b=bad)), 1)

    def test_padding_byte_fails(self):
        f = bytearray(frame())
        f[8000] ^= 1                                                  # bank 0 padding, not displayed
        r = C.compare_dumps(frame(), bytes(f))
        self.assertFalse(r["equal"])
        self.assertEqual(r["differing_pixels"], 0)

    def test_missing_dump_fails(self):
        some = {n: frame() for n in range(1, N)}
        self.assertEqual(self.cmp(*self.pair(LOG, dumps_a=some, dumps_b=some)), 1)

    def test_api_result_difference_fails(self):
        self.assertEqual(self.cmp(*self.pair(LOG, LOG.replace("TITLE=Calc", "TITLE=Calculator", 1))), 1)
        other = LOG.replace("COUNT=20\r\nELAPSED_MS=100\r\nAPI_SUCCESSES=20",
                            "COUNT=19\r\nELAPSED_MS=100\r\nAPI_SUCCESSES=19", 1)
        self.assertEqual(C.validate(other)[1], [])
        self.assertEqual(self.cmp(*self.pair(LOG, other)), 1)

    def test_timings_are_not_compared(self):
        self.assertEqual(self.cmp(*self.pair(LOG, LOG.replace("ELAPSED_MS=100", "ELAPSED_MS=3"))), 0)


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


class Evidence(unittest.TestCase):
    """The committed comparison results say what the PR claims."""
    D = HERE.parents[1] / "docs" / "rrect"

    def load(self, tag):
        return json.loads((self.D / f"C_{tag}.JSN").read_text())

    def test_candidate_frames_equal_baseline(self):
        for tag, n in (("CAND", 13), ("CANDTR", 13), ("SHOT", 3)):
            r = self.load(tag)
            self.assertTrue(r["all_frames_equal"], tag)
            self.assertEqual(len(r["stages"]), n)
            self.assertTrue(all(s["frame"]["equal"] and s["same_name_and_api_results"] for s in r["stages"]))

    def test_committed_logs_are_complete(self):
        for d in sorted(p for p in self.D.iterdir() if (p / "RRBENCH.LOG").exists()):
            raw = (d / "RRBENCH.LOG").read_bytes()
            recorded = json.loads((d / "RRRUN.JSN").read_text())["files"]["RRBENCH.LOG"]
            self.assertEqual(hashlib.sha256(raw).hexdigest(), recorded, d.name)    # the run's own bytes
            log = raw.decode("latin-1")
            self.assertEqual(C.validate(log)[1], [], d.name)
            self.assertNotEqual(C.validate(truncated(log, len(log.splitlines()) - 3))[1], [], d.name)
        self.assertGreaterEqual(len([p for p in self.D.iterdir() if (p / "RRBENCH.LOG").exists()]), 12)

    def test_committed_comparisons_were_complete(self):
        for tag in ("CAND", "CANDTR", "SHOT", "MLAST", "MFIRST", "MSCAN"):
            r = self.load(tag)
            self.assertTrue(r["runs_complete"], tag)
            self.assertEqual(r["problems"], {}, tag)

    def test_every_mutant_is_caught(self):
        for tag in ("MLAST", "MFIRST", "MSCAN"):
            r = self.load(tag)
            self.assertFalse(r["all_frames_equal"], tag)
            self.assertTrue(any(s["frame"].get("differing_pixels", 0) > 0 for s in r["stages"]), tag)

    def test_baseline_driver_is_the_accepted_tr5_driver(self):
        base = json.loads((self.D / "B_BASE.JSN").read_text())["sha256"]
        builds = (HERE.parents[1] / "docs" / "TRIAL5" / "BUILDS.JSN").read_text()
        self.assertIn(base, builds)
        for run in ("BASE", "SHOTBASE"):
            prep = json.loads((self.D / run / "RRRUN.JSN").read_text())["prep"]
            self.assertIn(base, json.dumps(prep))
        cand = json.loads((self.D / "B_CAND.JSN").read_text())["sha256"]
        for run in ("CAND", "SHOTCAND"):
            self.assertIn(cand, json.dumps(json.loads((self.D / run / "RRRUN.JSN").read_text())["prep"]))

if __name__ == "__main__":
    unittest.main()
