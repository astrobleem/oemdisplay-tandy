#!/usr/bin/env python3
"""Host tests for CPPOUT.PY (ColorPlus Output patch). No emulator, no DDK.

  python -B src/pcp/CPPOTEST.PY

Provenance. CPPOUT.FIX is the REAL TOutput procedure (lines 1108-1289)
extracted from the post-PCPPATCH staged EGA/TSOFT.ASM of the display view of
main 679d363. The post-PCPPATCH full TSOFT.ASM has SHA-256
340008a6a33951e89d423ca260ab2b540baff7dc8fd68ed2d3ab6994e5634acc. The fixture
is byte-identical to the PC1512 stage's TOutput extract.

These are source and model tests. They assemble and run nothing and prove
nothing about native ColorPlus behaviour or speed.
"""
import ast
import importlib.machinery
import random
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CPPOUT = importlib.machinery.SourceFileLoader(
    "cppout", str(HERE / "CPPOUT.PY")).load_module()
PCPPATCH = importlib.machinery.SourceFileLoader(
    "pcppatch", str(HERE / "PCPPATCH.PY")).load_module()
RR = CPPOUT.RR
FIX = (HERE / "CPPOUT.FIX").read_bytes().decode("latin-1")
SPREAD = [PCPPATCH.spread(b) for b in range(256)]


def patched():
    return CPPOUT.patch_output(FIX)


def lines(t):
    return t.split("\r\n")


def tout(t):
    a = t.index("cProc TOutput,")
    return t[a:t.index("cEnd", a) + 4]


def crlf(s):
    return s.replace("\n", "\r\n")


class Anchors(unittest.TestCase):
    def test_fixture_is_pure_crlf(self):
        self.assertNotIn("\n", FIX.replace("\r\n", ""))

    def test_every_edit_applies_once(self):
        t = RR.patch_candidate(FIX)
        for name, old, new in CPPOUT.X_EDITS:
            t = RR.replace_n(t, crlf(old), crlf(new), 1, name)
        self.assertEqual(t, patched())

    def test_rrpatch_anchors_match_fixture_once(self):
        self.assertEqual(FIX.count(RR.CAND_STYLE_OLD), 1)
        self.assertEqual(FIX.count(RR.CAND_POLY_OLD), 1)

    def test_no_bare_lf(self):
        self.assertNotIn("\n", patched().replace("\r\n", ""))

    def test_second_application_refused(self):
        with self.assertRaises(SystemExit):
            CPPOUT.patch_output(patched())

    def test_candidate_only_stage_refused(self):
        with self.assertRaises(SystemExit):
            CPPOUT.patch_output(RR.patch_candidate(FIX))

    def test_each_anchor_missing_refuses_through_patch_output(self):
        # Anchors present in the fixture: remove each one from the stage and
        # the whole patch must refuse, naming the edit that failed.
        for a, name in ((RR.CAND_STYLE_OLD, "candidate style gate"),
                        (RR.CAND_POLY_OLD, "candidate polyline bounds")):
            with self.assertRaisesRegex(SystemExit, re.escape(name)):
                CPPOUT.patch_output(FIX.replace(a, "; gone\r\n", 1))
        for name, old, _ in CPPOUT.X_EDITS:
            o = crlf(old)
            if o not in FIX:
                continue
            with self.assertRaisesRegex(SystemExit, re.escape(name)):
                CPPOUT.patch_output(FIX.replace(o, "; gone\r\n", 1))

    def test_anchors_built_by_candidate_refuse_when_missing(self):
        # Edits whose anchors exist only after patch_candidate: the same
        # replace step must refuse once that anchor is removed.
        base = RR.patch_candidate(FIX)
        for i, (name, old, new) in enumerate(CPPOUT.X_EDITS):
            o = crlf(old)
            if o in FIX:
                continue
            t = base
            for _, oo, nn in CPPOUT.X_EDITS[:i]:
                t = RR.replace_n(t, crlf(oo), crlf(nn), 1, "prior")
            with self.assertRaisesRegex(SystemExit, re.escape(name)):
                RR.replace_n(t.replace(o, "; gone\r\n", 1), o, crlf(new), 1, name)

    def test_duplicate_anchor_refuses_through_patch_output(self):
        with self.assertRaisesRegex(SystemExit, re.escape("candidate style gate")):
            CPPOUT.patch_output(FIX + RR.CAND_STYLE_OLD)
        for name, old, _ in CPPOUT.X_EDITS:
            with self.assertRaisesRegex(SystemExit, re.escape(name)):
                CPPOUT.patch_output(FIX + crlf(old))

    def test_patch_staged_roundtrip_and_refusals(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "TSOFT.ASM"
            p.write_bytes(FIX.encode("latin-1"))
            new = CPPOUT.patch_staged(d)
            self.assertEqual(p.read_bytes().decode("latin-1"), new)
            self.assertEqual(new, patched())
            before = p.read_bytes()
            with self.assertRaises(SystemExit):
                CPPOUT.patch_staged(d)
            self.assertEqual(p.read_bytes(), before)

    def test_patch_staged_mismatch_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "TSOFT.ASM"
            bad = FIX.replace("TOutput_scan_interval", "TOutput_scan_x")
            p.write_bytes(bad.encode("latin-1"))
            with self.assertRaises(SystemExit):
                CPPOUT.patch_staged(d)
            self.assertEqual(p.read_bytes(), bad.encode("latin-1"))

    def test_patch_staged_candidate_stage_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "TSOFT.ASM"
            cand = RR.patch_candidate(FIX).encode("latin-1")
            p.write_bytes(cand)
            with self.assertRaises(SystemExit):
                CPPOUT.patch_staged(d)
            self.assertEqual(p.read_bytes(), cand)

    def test_module_api(self):
        self.assertTrue(callable(CPPOUT.patch_staged))
        self.assertFalse(hasattr(CPPOUT, "patch_staged_output"))

    def test_source_reuses_rrpatch_and_has_no_port_scheme(self):
        src = (HERE / "CPPOUT.PY").read_bytes().decode("latin-1")
        self.assertNotIn("CAND_STYLE_OLD", src)
        self.assertNotIn("CAND_POLY_OLD", src)
        # Code only: comments and docstrings are prose and are excluded.
        tree = ast.parse(src)
        doc_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                b = node.body
                if b and isinstance(b[0], ast.Expr) and \
                        isinstance(b[0].value, ast.Constant) and \
                        isinstance(b[0].value.value, str):
                    doc_lines.update(range(b[0].lineno, b[0].end_lineno + 1))
        code = "\n".join(l.split("#", 1)[0] for i, l in
                         enumerate(src.splitlines(), 1) if i not in doc_lines)
        for banned in ("TCURSOR", "3DEh", "3DDh"):
            self.assertNotIn(banned, code, banned)


class Structure(unittest.TestCase):
    def setUp(self):
        self.t = patched()
        self.f = lines(self.t)
        self.to = tout(self.t)

    def idx(self, s, start=0):
        return self.f.index(s, start)

    def test_marker_skips_copy_before_render(self):
        m = self.idx("TOutput_marker:")
        self.assertEqual(self.f[m + 1:m + 3],
                         ["    mov dirty,0", "    jmp TOutput_render"])
        self.assertIn("    cmp style,80", self.f)
        self.assertIn("    cmp style,81", self.f)
        self.assertLess(m, self.idx("    les di,points"))

    def test_scan_and_polyline_limits_match_constants(self):
        t = self.t
        scan = re.search(r"cmp style,4\r\n    jne TOutput_thin_count\r\n"
                         r"    cmp count,2\r\n    or_require jae,TOutput_render\r\n"
                         r"    cmp count,(\d+)\r\n    or_require jbe,TOutput_render\r\n",
                         t)
        poly = re.search(r"    cmp count,2\r\n    or_require jae,TOutput_render\r\n"
                         r"    cmp count,(\d+)\r\n    or_require jbe,TOutput_render\r\n"
                         r"TOutput_style_ok:", t)
        self.assertIsNotNone(scan)
        self.assertIsNotNone(poly)
        self.assertEqual(int(scan.group(1)), CPPOUT.SCAN_MAX)
        self.assertEqual(int(poly.group(1)), CPPOUT.POLY_MAX)
        self.assertEqual(CPPOUT.SCAN_MAX, 64)
        self.assertEqual(CPPOUT.POLY_MAX, 1024)

    def test_x_bounds_follow_validation(self):
        t = self.t
        scan = t[t.index("TOutput_scan_interval:"):t.index("TOutput_polyline:")]
        self.assertLess(scan.index("or_require jb,TOutput_render"),
                        scan.index("cmp bx,firstcol"))
        self.assertLess(scan.index("cmp dx,SCREEN_WIDTH"),
                        scan.index("mov lastcol,dx"))
        poly = t[t.index("TOutput_poly_point:"):t.index("TOutput_two_point:")]
        self.assertLess(poly.index("cmp dx,SCREEN_WIDTH"),
                        poly.index("mov firstcol,dx"))
        self.assertLess(poly.index("inc dx"), poly.index("mov lastcol,dx"))

    def test_synchronous_presentation_only(self):
        t = self.t
        self.assertEqual(t.count("call FlushRetainColumns"), 1)
        self.assertEqual(t.count("call FlushRetainRows"), 1)
        for banned in ("rr_bopen", "BatchClose", "rr_bfirst", "rr_settle"):
            self.assertNotIn(banned, t)
        self.assertLess(t.index("cCall Output,"), t.index("call FlushRetainColumns"))
        self.assertLess(t.index("call FlushRetainColumns"), t.index("TOutput_done:"))
        self.assertLess(t.index("cCall Output,"), t.index("call FlushRetainRows"))
        self.assertLess(t.index("call FlushRetainRows"), t.index("TOutput_done:"))

    def test_full_scan_shortcut_is_after_safety_checks(self):
        t = self.t
        a = t.index("    cmp count,2\r\n    jne TOutput_scan_collect")
        b = t.index("TOutput_scan_collect:", a)
        fast = t[a:b]
        self.assertIn("    cmp word ptr es:[di+4],0\r\n", fast)
        self.assertIn("    cmp word ptr es:[di+6],SCREEN_WIDTH\r\n", fast)
        self.assertEqual(fast.count("    jne TOutput_scan_collect"), 3)
        self.assertTrue(fast.endswith(
            "    mov outrows,2\r\n    jmp TOutput_render\r\n"))
        prefix = t[:a]
        self.assertIn("    call ORowsSpanSafe\r\n", prefix)
        self.assertIn("    les di,mode\r\n", prefix)
        self.assertIn("    cmp ax,SCREEN_HEIGHT\r\n", prefix)
        self.assertIn("    mov firstrow,ax\r\n    inc ax\r\n    mov lastrow,ax\r\n",
                      prefix)
        self.assertNotIn("firstcol", fast)

    def test_full_width_rows_do_not_read_uninitialized_columns(self):
        t = self.t
        a = t.index("; Preserve the actual renderer result")
        seg = t[a:t.index("TOutput_done:", a)]
        flag = seg.index("    cmp outrows,2\r\n    je TOutput_rows\r\n")
        self.assertLess(flag, seg.index("    cmp firstcol,0"))
        self.assertIn("    cmp lastcol,SCREEN_WIDTH\r\n    je TOutput_rows\r\n", seg)
        rows = seg[seg.index("TOutput_rows:"):seg.index("TOutput_full:")]
        self.assertEqual(rows, "TOutput_rows:\r\n    call FlushRetainRows\r\n"
                               "    jmp short TOutput_flushed\r\n")
        self.assertLess(seg.index("    push cx"), seg.index("call FlushRetainColumns"))
        self.assertLess(seg.index("call FlushRetainColumns"), seg.index("    pop cx"))

    def test_uninitialized_bounds_outrows_writers(self):
        # outrows is written exactly at init (0), the shortcut (2) and bounded (1).
        self.assertEqual(self.to.count("mov outrows,"), 3)
        self.assertEqual(self.to.count("mov outrows,2\r\n    jmp TOutput_render\r\n"), 1)
        self.assertEqual(self.to.count("mov outrows,1\r\n"), 1)
        self.assertLess(self.to.index("TOutput_bounded:"),
                        self.to.index("mov outrows,1"))

    def test_uninitialized_bounds_producers(self):
        f = self.f
        label_at = {}
        for i, l in enumerate(f):
            if l.endswith(":") and not l.startswith(" "):
                label_at[l[:-1]] = i
        bounded = label_at["TOutput_bounded"]
        # Each producer runs from its entry label to the line that leaves it.
        jmp_bounded = [i for i, l in enumerate(f)
                       if l == "    jmp TOutput_bounded"]
        self.assertEqual(len(jmp_bounded), 2)
        ranges = {
            "scan": (label_at["TOutput_scan_collect"], jmp_bounded[0]),
            "polyline": (label_at["TOutput_polyline"], jmp_bounded[1]),
            "two_point": (label_at["TOutput_two_point"], bounded - 1),
        }
        jump_re = re.compile(r"^\s*(j\w+|loop)\s+(?:short\s+)?(\w+)\s*$")
        jumps = []
        for i, l in enumerate(f):
            m = jump_re.match(l)
            if m:
                jumps.append((i, m.group(1), m.group(2)))
        # Exactly three producers reach TOutput_bounded.
        self.assertEqual([i for i, _, t in jumps if t == "TOutput_bounded"],
                         jmp_bounded)
        # The fall-through predecessor is the two-point producer's last line.
        self.assertEqual(f[bounded - 1].strip(), "mov lastrow,bx")
        # Entry labels: only from the dispatch points, and entered by an
        # unconditional jmp on the line before (never by fall-through).
        dispatch = {"TOutput_scan_collect": "jne", "TOutput_polyline": "je",
                    "TOutput_two_point": "je"}
        for label, op in dispatch.items():
            preds = [(i, o) for i, o, t in jumps if t == label]
            self.assertTrue(preds, label)
            for i, o in preds:
                self.assertEqual(o, op, label)
            self.assertTrue(f[label_at[label] - 1].strip().startswith("jmp "),
                            label)
        # Interior labels: every jump into them and the fall-in line come
        # from inside the same producer.
        for name, (lo, hi) in ranges.items():
            for label, at in label_at.items():
                if not lo < at <= hi:
                    continue
                self.assertLess(at - 1, hi, (name, label))
                self.assertGreaterEqual(at - 1, lo, (name, label))
                for i, _, t in jumps:
                    if t == label:
                        self.assertTrue(lo <= i <= hi, (name, label, i))
        # Every producer writes both column bounds.
        for name, (lo, hi) in ranges.items():
            seg = f[lo:hi + 1]
            self.assertTrue(any(l.startswith("    mov firstcol,") for l in seg), name)
            self.assertTrue(any(l.startswith("    mov lastcol,") for l in seg), name)
        # The only early exit without column bounds is the scan shortcut.
        self.assertIn("    mov outrows,2\r\n    jmp TOutput_render\r\n", self.to)
        self.assertLess(self.to.index("    mov outrows,2"),
                        self.to.index("TOutput_scan_collect:"))

    def test_outrows_two_checked_before_column_reads(self):
        seg = self.to[self.to.index("; Preserve the actual renderer result"):]
        self.assertLess(seg.index("cmp outrows,2"), seg.index("firstcol"))
        rows = seg[seg.index("TOutput_rows:"):seg.index("TOutput_full:")]
        self.assertNotIn("firstcol", rows)
        self.assertNotIn("lastcol", rows)

    def test_fallback_unchanged(self):
        self.assertIn("TOutput_full:\r\n    call FlushShadow\r\nTOutput_flushed:",
                      self.t)
        self.assertIn("    cmp outrows,0\r\n    je TOutput_full\r\n", self.t)

    def test_rejection_sites_only_grow(self):
        old = Counter(l.strip() for l in lines(FIX) if "or_require" in l)
        new = Counter(l.strip() for l in self.f if "or_require" in l)
        self.assertEqual(old - new, Counter({"or_require je,TOutput_render": 1}))
        self.assertEqual(new - old, Counter({"or_require jae,TOutput_render": 1,
                                             "or_require jbe,TOutput_render": 1,
                                             "or_require jb,TOutput_render": 2}))

    def test_registers_preserved(self):
        t = self.t
        a = t.index("; Preserve the actual renderer result")
        seg = t[a:t.index("TOutput_done:")]
        self.assertEqual(seg.count("    push "), seg.count("    pop "))
        self.assertEqual(re.findall(r"    push (\w+)", seg),
                         ["ax", "bx", "cx", "dx"])
        self.assertEqual(re.findall(r"    pop (\w+)", seg),
                         ["dx", "cx", "bx", "ax"])

    def test_two_point_extent_is_exclusive(self):
        seg = self.t[self.t.index("TOutput_x_ordered:"):self.t.index("TOutput_bounded:")]
        self.assertLess(seg.index("mov firstcol,cx"), seg.index("inc dx"))
        self.assertLess(seg.index("inc dx"), seg.index("mov lastcol,dx"))

    def test_edge_rounding_code(self):
        seg = self.t[self.t.index("    mov cx,firstcol\r\n    mov dx,lastcol"):]
        seg = seg[:seg.index("call FlushRetainColumns")]
        self.assertEqual(seg.count("    shr cx,1"), 3)
        self.assertEqual(seg.count("    shr dx,1"), 3)
        self.assertIn("    add dx,7\r\n", seg)
        self.assertLess(seg.index("add dx,7"), seg.index("shr dx,1"))

    def test_no_literal_640_stride_or_port_io(self):
        self.assertNotIn("640", self.to)
        self.assertNotIn("SCREEN_W_BYTES", self.to)
        self.assertIsNone(re.search(r"mov\s+(cx|dx|ax),\s*(80|160)\b", self.to))
        self.assertIsNone(re.search(r"^\s*(in|out)\s", self.to, re.M))
        self.assertIn("SCREEN_WIDTH", self.to)

    def test_no_xr1_or_tandy_assumptions(self):
        for banned in ("cursor_begin_retain", "SCREEN_W_BYTES*4", "bp-26",
                       "viewport", "cursor_end_retain", "lea si,[bp"):
            self.assertNotIn(banned, self.t)


# --- plane-aware model: independent of PCPPATCH.model_flush -----------------

def set_pixel(sh, x, y, colour):
    """Write an IRGB colour into the 4-plane shadow (inverse of shadow_pixel)."""
    base = y * 160 + (x >> 3)
    bit = 0x80 >> (x & 7)
    for off, mask in ((0, 4), (40, 2), (80, 1), (120, 8)):   # R G B I
        if colour & mask:
            sh[base + off] |= bit
        else:
            sh[base + off] &= ~bit & 0xFF


def line_pixels(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        yield x0, y0
        if (x0, y0) == (x1, y1):
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _put(vram, i, w, order="high"):
    if i + 1 < len(vram):           # writes past the 32 KB image are lost
        hi, lo = w >> 8, w & 255
        vram[i], vram[i + 1] = (hi, lo) if order == "high" else (lo, hi)


def cp_flush_region(vram, shadow, r0, r1, c0, c1, bank="cga",
                    planes="correct", order="high"):
    """FlushRetainColumns model: logical columns [c0,c1) of rows [r0,r1).

    Computes every byte itself from the four-plane shadow. Mutations are
    selectable here so the same code path produces the negative controls.
    """
    for y in range(r0, r1):
        if bank == "cga":
            base = (y & 1) * 0x2000 + (y >> 1) * 80
        elif bank == "tandy":
            base = (y & 3) * 0x2000 + (y >> 2) * 160
        elif bank == "inverted":
            base = (1 - (y & 1)) * 0x2000 + (y >> 1) * 80
        else:
            raise ValueError(bank)
        for c in range(c0, c1):
            s = y * 160 + c
            w0 = (SPREAD[shadow[s]] << 1) | SPREAD[shadow[s + 40]]
            w1 = (SPREAD[shadow[s + 80]] << 1) | SPREAD[shadow[s + 120]]
            off = 2 * c                       # two plane bytes per column
            if off + 1 >= 80:                 # never past the plane row
                continue
            lo, hi = (w0, w1) if planes == "correct" else (w1, w0)
            _put(vram, base + off, lo, order)
            _put(vram, base + 0x4000 + off, hi, order)


def rnd_shadow(seed):
    r = random.Random(seed)
    return bytes(r.randrange(1, 256) for _ in range(32000))


def draw_polyline(pts, col):
    def draw(sh):
        for a, b in zip(pts, pts[1:]):
            for x, y in line_pixels(a, b):
                set_pixel(sh, x, y, col)
    return draw


def draw_scan(y, ivs, col):
    def draw(sh):
        for left, right in ivs:
            for x in range(left, right):
                set_pixel(sh, x, y, col)
    return draw


def apply_gate(old, draw, bounds, mutate=None):
    """Draw into a copy of old, present the gate's region, return results.

    Returns (vram, expected, new) where vram starts from the old picture,
    expected is PCPPATCH.model_flush(new) and bounds None means the fail-closed
    full flush. mutate is a dict of cp_flush_region arguments, plus an
    optional "cols" pair that replaces the gate's logical columns.
    """
    m = dict(mutate or {})
    cols = m.pop("cols", None)
    new = bytearray(old)
    draw(new)
    vram = PCPPATCH.model_flush(bytes(old))
    if bounds is None:
        r0, r1, c0, c1 = 0, 200, 0, 40
    else:
        r0, r1 = bounds[0], bounds[1]
        c0, c1 = CPPOUT.flush_columns(bounds[2], bounds[3])
    if cols is not None:
        c0, c1 = cols
    cp_flush_region(vram, new, r0, r1, c0, c1, **m)
    return vram, PCPPATCH.model_flush(bytes(new)), bytes(new)


def choose_present(outrows, firstcol, lastcol):
    """Mirror of the patched epilogue: rows or logical columns."""
    if outrows == 2 or (firstcol == 0 and lastcol == 320):
        return "rows"
    return "columns"


class Model(unittest.TestCase):
    def assert_gate(self, old, draw, bounds, decode=False, label=None):
        vram, want, new = apply_gate(old, draw, bounds)
        self.assertEqual(vram, want, label or bounds)
        if decode:
            self.assert_decodes(vram, new, label)
        return vram, want, new

    def assert_decodes(self, vram, new, label=None):
        for y in range(200):
            for x in range(320):
                if PCPPATCH.pcp_pixel(vram, y, x) != PCPPATCH.shadow_pixel(new, y, x):
                    self.fail("pixel (%d,%d) mismatch %s" % (x, y, label))

    def test_flush_columns_edge_table(self):
        table = {(0, 1): (0, 1), (0, 8): (0, 1), (0, 9): (0, 2), (7, 9): (0, 2),
                 (8, 9): (1, 2), (311, 312): (38, 39), (312, 313): (39, 40),
                 (312, 320): (39, 40), (319, 320): (39, 40), (0, 320): (0, 40)}
        for args, want in table.items():
            self.assertEqual(CPPOUT.flush_columns(*args), want, args)

    def test_flush_columns_right_column_never_past_40(self):
        for x1 in range(1, 321):
            self.assertLessEqual(CPPOUT.flush_columns(x1 - 1, x1)[1], 40)

    def test_reference_region_equals_model_flush(self):
        new = rnd_shadow(7)
        vram = bytearray(0x8000)
        cp_flush_region(vram, new, 0, 200, 0, 40)
        self.assertEqual(bytes(vram), bytes(PCPPATCH.model_flush(new)))

    def test_scan_count_limits(self):
        self.assertIsNone(CPPOUT.scan_bounds(0, []))                 # count 1
        self.assertIsNotNone(CPPOUT.scan_bounds(0, [(0, 1)]))        # count 2
        self.assertIsNotNone(CPPOUT.scan_bounds(0, [(0, 1)] * 63))   # count 64
        self.assertIsNone(CPPOUT.scan_bounds(0, [(0, 1)] * 64))      # count 65
        ivs = [(i * 5, i * 5 + 3) for i in range(63)]
        self.assert_gate(rnd_shadow(64), draw_scan(120, ivs, 9), (120, 121, 0, 313),
                         decode=True, label="count 64")

    def test_polyline_count_limits(self):
        self.assertIsNone(CPPOUT.polyline_bounds([(0, 0)]))
        self.assertIsNotNone(CPPOUT.polyline_bounds([(0, 0), (5, 5)]))
        self.assertIsNotNone(CPPOUT.polyline_bounds([(0, 0), (5, 5), (9, 1)]))
        pts = [(i * 7 % 320, i * 3 % 200) for i in range(1024)]
        self.assertIsNotNone(CPPOUT.polyline_bounds(pts))
        self.assertIsNone(CPPOUT.polyline_bounds(pts + [(1, 1)]))
        self.assert_gate(rnd_shadow(1024), draw_polyline(pts, 6),
                         CPPOUT.polyline_bounds(pts), decode=True, label="1024")

    def test_invalid_bounds_fall_back(self):
        self.assertIsNone(CPPOUT.scan_bounds(200, [(0, 1)]))         # y off screen
        self.assertIsNone(CPPOUT.scan_bounds(-1, [(0, 1)]))
        self.assertIsNone(CPPOUT.scan_bounds(0, [(4, 4)]))           # empty
        self.assertIsNone(CPPOUT.scan_bounds(0, [(9, 3)]))           # reversed
        self.assertIsNone(CPPOUT.scan_bounds(0, [(0, 321)]))         # right > 320
        self.assertIsNone(CPPOUT.polyline_bounds([(320, 0), (1, 1)]))
        self.assertIsNone(CPPOUT.polyline_bounds([(-1, 0), (1, 1), (2, 2)]))
        self.assertIsNone(CPPOUT.polyline_bounds([(0, 200), (1, 1)]))
        self.assertIsNone(CPPOUT.polyline_bounds([(5, 5), (5, 5)]))  # identical

    def test_random_polylines(self):
        rnd = random.Random(1512)
        for i in range(24):
            n = rnd.choice((2, 3, 5))
            pts = [(rnd.randrange(320), rnd.randrange(200)) for _ in range(n)]
            b = CPPOUT.polyline_bounds(pts)
            if b is None:
                continue
            self.assert_gate(rnd_shadow(100 + i), draw_polyline(pts, rnd.randrange(16)),
                             b, decode=True, label=pts)

    def test_random_polyline_1024(self):
        rnd = random.Random(1024)
        pts = [(rnd.randrange(320), rnd.randrange(200)) for _ in range(1024)]
        self.assert_gate(rnd_shadow(2024), draw_polyline(pts, 11),
                         CPPOUT.polyline_bounds(pts), decode=True, label="rnd1024")

    def test_random_scans(self):
        rnd = random.Random(640)
        for i in range(30):
            ivs = []
            for _ in range(rnd.choice((1, 2, 4))):
                a = rnd.randrange(319)
                ivs.append((a, rnd.randrange(a + 1, 321)))
            y = rnd.randrange(200)
            b = CPPOUT.scan_bounds(y, ivs)
            self.assert_gate(rnd_shadow(300 + i), draw_scan(y, ivs, rnd.randrange(16)),
                             b, decode=True, label=(y, ivs))

    def test_boundary_spans(self):
        spans = [(0, 1), (319, 320), (311, 312), (312, 313), (312, 320),
                 (3, 13), (7, 9), (8, 16), (0, 320)]
        for y in (0, 1, 198, 199):
            for i, (l, r) in enumerate(spans):
                self.assert_gate(rnd_shadow(500 + 10 * y + i),
                                 draw_scan(y, [(l, r)], 15 - i),
                                 CPPOUT.scan_bounds(y, [(l, r)]),
                                 decode=True, label=(y, l, r))

    def test_full_width_scan(self):
        b = CPPOUT.scan_bounds(77, [(0, 320)])
        self.assertEqual(CPPOUT.flush_columns(b[2], b[3]), (0, 40))
        self.assert_gate(rnd_shadow(77), draw_scan(77, [(0, 320)], 5), b, decode=True)

    def test_markers_and_rejections_leave_picture(self):
        old = rnd_shadow(9)
        # Markers draw nothing: no region, nothing to copy.
        vram, want, _ = apply_gate(old, lambda s: None, None)
        self.assertEqual(vram, want)
        self.assertEqual(vram, bytes(PCPPATCH.model_flush(old)))
        # Rejected lists have no bounds; the fail-closed full flush is used.
        self.assertIsNone(CPPOUT.scan_bounds(250, [(0, 1)]))
        vram, want, _ = apply_gate(old, lambda s: None, None)
        self.assertEqual(vram, want)

    def test_choose_present_matches_epilogue_text(self):
        # The epilogue text makes exactly the choose_present decision.
        pat = ("    cmp outrows,2\r\n    je TOutput_rows\r\n"
               "    cmp firstcol,0\r\n    jne TOutput_columns\r\n"
               "    cmp lastcol,SCREEN_WIDTH\r\n    je TOutput_rows\r\n"
               "TOutput_columns:")
        self.assertIn(pat, tout(patched()))
        self.assertEqual(choose_present(2, 0, 320), "rows")
        self.assertEqual(choose_present(1, 0, 320), "rows")
        self.assertEqual(choose_present(1, 0, 319), "columns")
        self.assertEqual(choose_present(1, 1, 320), "columns")

    def test_rows_vs_columns_cases(self):
        old = rnd_shadow(4242)
        # (name, bounds, draw, outrows, expected choice)
        cases = [
            ("shortcut full", (10, 11, 0, 320), draw_scan(10, [(0, 320)], 3), 2, "rows"),
            ("two halves", CPPOUT.scan_bounds(12, [(0, 160), (160, 320)]),
             draw_scan(12, [(0, 160), (160, 320)], 4), 1, "rows"),
            ("0..319", CPPOUT.scan_bounds(14, [(0, 319)]),
             draw_scan(14, [(0, 319)], 6), 1, "columns"),
            ("poly 0..319", CPPOUT.polyline_bounds([(0, 10), (319, 20)]),
             draw_polyline([(0, 10), (319, 20)], 9), 1, "rows"),
            ("312..320", CPPOUT.scan_bounds(30, [(312, 320)]),
             draw_scan(30, [(312, 320)], 12), 1, "columns"),
            ("0..1", CPPOUT.scan_bounds(31, [(0, 1)]),
             draw_scan(31, [(0, 1)], 2), 1, "columns"),
        ]
        for name, bounds, draw, outrows, want_choice in cases:
            fc, lc = (0, 320) if outrows == 2 else (bounds[2], bounds[3])
            choice = choose_present(outrows, fc, lc)
            self.assertEqual(choice, want_choice, name)
            cols = (0, 40) if choice == "rows" else CPPOUT.flush_columns(fc, lc)
            self.assert_gate(old, draw, bounds, decode=True, label=name)
            vram, want, _ = apply_gate(old, draw, bounds, mutate={"cols": cols})
            self.assertEqual(vram, want, name)
        # Columns for the full width give the same picture as Rows.
        full = CPPOUT.scan_bounds(40, [(0, 320)])
        rows_vram, want, _ = apply_gate(old, draw_scan(40, [(0, 320)], 8), full,
                                        mutate={"cols": (0, 40)})
        cols_vram, _, _ = apply_gate(old, draw_scan(40, [(0, 320)], 8), full,
                                     mutate={"cols": CPPOUT.flush_columns(0, 320)})
        self.assertEqual(rows_vram, cols_vram)
        self.assertEqual(rows_vram, want)

    def test_all_four_planes_presented(self):
        for colour in (1, 2, 4, 8, 15):
            pts = [(100, 50), (100, 51)]
            vram, want, new = apply_gate(rnd_shadow(colour), draw_polyline(pts, colour),
                                         CPPOUT.polyline_bounds(pts))
            self.assertEqual(vram, want)
            self.assertEqual(PCPPATCH.pcp_pixel(vram, 50, 100), colour)

    # --- negative controls: each correct case passes, the mutant fails ---

    def test_neg_rounding_polyline_right_column(self):
        pts = [(7, 10), (9, 10)]
        b = CPPOUT.polyline_bounds(pts)
        self.assert_gate(rnd_shadow(11), draw_polyline(pts, 15), b, decode=True)
        vram, want, _ = apply_gate(rnd_shadow(11), draw_polyline(pts, 15), b,
                                   mutate={"cols": (b[2] >> 3, b[3] >> 3)})
        self.assertNotEqual(vram, want)
        pts = [(312, 3), (318, 3)]
        b = CPPOUT.polyline_bounds(pts)
        self.assert_gate(rnd_shadow(12), draw_polyline(pts, 15), b, decode=True)
        vram, want, _ = apply_gate(rnd_shadow(12), draw_polyline(pts, 15), b,
                                   mutate={"cols": (b[2] >> 3, b[3] >> 3)})
        self.assertNotEqual(vram, want)

    def test_neg_rounding_plus6(self):
        b = CPPOUT.scan_bounds(10, [(8, 9)])
        self.assert_gate(rnd_shadow(13), draw_scan(10, [(8, 9)], 15), b, decode=True)
        vram, want, _ = apply_gate(rnd_shadow(13), draw_scan(10, [(8, 9)], 15), b,
                                   mutate={"cols": (b[2] >> 3, (b[3] + 6) >> 3)})
        self.assertNotEqual(vram, want)

    def test_neg_double_scaling(self):
        pts = [(100, 50), (108, 50)]
        b = CPPOUT.polyline_bounds(pts)
        self.assertEqual(CPPOUT.flush_columns(b[2], b[3]), (12, 14))
        self.assert_gate(rnd_shadow(14), draw_polyline(pts, 9), b, decode=True)
        # Columns already doubled by the caller, then doubled again by the model.
        vram, want, _ = apply_gate(rnd_shadow(14), draw_polyline(pts, 9), b,
                                   mutate={"cols": (24, 28)})
        self.assertNotEqual(vram, want)

    def test_neg_plane_order(self):
        pts = [(100, 50), (110, 50)]
        b = CPPOUT.polyline_bounds(pts)
        zero = bytes(32000)
        self.assert_gate(zero, draw_polyline(pts, 4), b, decode=True)
        vram, want, _ = apply_gate(zero, draw_polyline(pts, 4), b,
                                   mutate={"planes": "swapped"})
        self.assertNotEqual(vram, want)

    def test_neg_bank_addressing(self):
        for y in (1, 2, 3, 198, 199):
            b = CPPOUT.scan_bounds(y, [(0, 320)])
            self.assert_gate(rnd_shadow(20 + y), draw_scan(y, [(0, 320)], 10), b)
        differs = {"tandy": [], "inverted": []}
        for y in (1, 2, 3, 198, 199):
            b = CPPOUT.scan_bounds(y, [(0, 320)])
            for name in differs:
                vram, want, _ = apply_gate(rnd_shadow(20 + y),
                                           draw_scan(y, [(0, 320)], 10), b,
                                           mutate={"bank": name})
                if vram != want:
                    differs[name].append(y)
        # Row 1 maps to the same bank under both formulas; the rest must differ.
        self.assertEqual(sorted(differs["tandy"]), [2, 3, 198, 199])
        self.assertEqual(sorted(differs["inverted"]), [1, 2, 3, 198, 199])

    def test_neg_byte_order(self):
        # Solid colours give words with equal bytes (0xAAAA) that a byte swap
        # cannot change, so draw a different colour at every pixel.
        rnd = random.Random(33)

        def draw(sh):
            for x in range(320):
                set_pixel(sh, x, 50, rnd.randrange(16))
        b = CPPOUT.scan_bounds(50, [(0, 320)])
        self.assert_gate(rnd_shadow(33), draw, b, decode=True)
        rnd = random.Random(33)
        vram, want, _ = apply_gate(rnd_shadow(33), draw, b,
                                   mutate={"order": "low"})
        self.assertNotEqual(vram, want)


class Scope(unittest.TestCase):
    def test_only_buildpcp_uses_cppout(self):
        root = HERE.parents[1]
        users = set()
        files = []
        for sub in ("src", "tools", "experiments"):
            d = root / sub
            if d.exists():
                files += [p for p in d.rglob("*") if p.is_file() and p.suffix.lower() == ".py"]
        for p in files:
            if p.name.upper() in ("CPPOUT.PY", "CPPOTEST.PY"):
                continue
            text = p.read_bytes().decode("latin-1")
            if "CPPOUT" not in text.upper():
                continue
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(
                        n.name.split(".")[-1].upper() == "CPPOUT" for n in node.names):
                    users.add(p.name)
                if isinstance(node, ast.ImportFrom) and \
                        (node.module or "").split(".")[-1].upper() == "CPPOUT":
                    users.add(p.name)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                        and node.func.attr == "SourceFileLoader":
                    if any(isinstance(n, ast.Constant) and isinstance(n.value, str)
                           and n.value.upper().endswith("CPPOUT.PY")
                           for n in ast.walk(node)):
                        users.add(p.name)
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                        and node.value.id.upper() == "CPPOUT":
                    users.add(p.name)
        self.assertEqual(users, {"BUILDPCP.PY"})

    def test_buildpcp_applies_cppout_once_in_patched_block(self):
        # Code calls only: the module docstring may mention the call in prose.
        t = (HERE / "BUILDPCP.PY").read_bytes().decode("latin-1")
        tree = ast.parse(t)
        starts = [0]
        for line in t.splitlines(True):
            starts.append(starts[-1] + len(line))

        def offset(node):
            return starts[node.lineno - 1] + node.col_offset

        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "patch_staged"
                 and isinstance(n.func.value, ast.Name)
                 and n.func.value.id == "CPPOUT"]
        self.assertEqual(len(calls), 1)
        cc = offset(calls[0])
        pc = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute)
              and n.func.attr == "patch_staged"
              and isinstance(n.func.value, ast.Name)
              and n.func.value.id == "PCPPATCH"]
        self.assertEqual(len(pc), 1)
        self.assertLess(offset(pc[0]), cc)
        self.assertLess(cc, t.index("return real_run("))
        # The call must sit in the body of the real `if "patched" not in state`
        # guard (an AST If, so a dedent out of the guard fails the test).
        guards = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                  and ast.unparse(n.test).replace("'", '"')
                  == '"patched" not in state']
        self.assertGreaterEqual(len(guards), 1)
        inside = []
        for g in guards:
            body = set(id(x) for stmt in g.body for x in ast.walk(stmt))
            inside.append((id(calls[0]) in body, id(pc[0]) in body))
        self.assertIn((True, True), inside)

    def test_buildpcp_no_other_cppout_use(self):
        t = (HERE / "BUILDPCP.PY").read_bytes().decode("latin-1")
        tree = ast.parse(t)
        uses = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name) and n.value.id.upper() == "CPPOUT"]
        self.assertEqual(len(uses), 1)

    def test_pcppatch_does_not_mention_cppout(self):
        t = (HERE / "PCPPATCH.PY").read_bytes().decode("latin-1")
        self.assertNotIn("CPPOUT", t.upper())


if __name__ == "__main__":
    unittest.main(verbosity=1)
