#!/usr/bin/env python3
"""Host tests for P15OUT.PY (no emulator, no DDK, no native driver).

  python3 -B src/pc1512/P15OTEST.PY

P15OUT.FIX is the TOutput procedure of the real post-P15PATCH staged
EGA/TSOFT.ASM (BUILD15 view of main 316f21b). The tests check that every
anchor matches exactly once, that nothing is written on a mismatch or a
second application, the patched gate's structure (markers, validation order,
unchanged FlushShadow fallback, synchronous presentation) and, with a
plane-aware model, that the rounded byte-column region always covers every
pixel a supported primitive can change.

These are source and model tests. They do not assemble or run the driver and
prove nothing about PC1512 speed or native behaviour.
"""
import importlib.machinery
import ast
import random
import re
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = importlib.machinery.SourceFileLoader("p15out", str(HERE / "P15OUT.PY")).load_module()
P15 = importlib.machinery.SourceFileLoader("p15patch", str(HERE / "P15PATCH.PY")).load_module()
FIX = (HERE / "P15OUT.FIX").read_bytes().decode("latin-1")


def patched():
    return OUT.patch_output(FIX)


def lines(t):
    return t.split("\r\n")


class Anchors(unittest.TestCase):
    def test_fixture_is_crlf(self):
        self.assertNotIn("\n", FIX.replace("\r\n", ""))

    def test_every_edit_applies_once(self):
        t = OUT.RR.patch_candidate(FIX)
        for name, old, new in OUT.X_EDITS:
            self.assertEqual(t.count(old.replace("\n", "\r\n")), 1, name)
            t = OUT.RR.replace_n(t, old.replace("\n", "\r\n"),
                                 new.replace("\n", "\r\n"), 1, name)
        self.assertEqual(t, patched())

    def test_no_bare_lf(self):
        self.assertNotIn("\n", patched().replace("\r\n", ""))

    def test_second_application_refused(self):
        with self.assertRaises(SystemExit):
            OUT.patch_output(patched())

    def test_candidate_alone_stage_refused(self):
        with self.assertRaises(SystemExit):
            OUT.patch_output(OUT.RR.patch_candidate(FIX))

    def test_each_anchor_missing_refuses(self):
        anchors = [OUT.RR.CAND_STYLE_OLD, OUT.RR.CAND_POLY_OLD]
        anchors += [o.replace("\n", "\r\n") for _, o, _ in OUT.X_EDITS
                    if o.replace("\n", "\r\n") in FIX]
        self.assertGreaterEqual(len(anchors), 7)
        for a in anchors:
            self.assertEqual(FIX.count(a), 1, a)
            with self.assertRaises(SystemExit):
                OUT.patch_output(FIX.replace(a, "; gone\r\n", 1))

    def test_duplicate_anchor_refuses(self):
        a = OUT.RR.CAND_STYLE_OLD
        with self.assertRaises(SystemExit):
            OUT.patch_output(FIX + a)

    def test_mismatch_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "TSOFT.ASM"
            bad = FIX.replace("TOutput_scan_interval", "TOutput_scan_x")
            p.write_bytes(bad.encode("latin-1"))
            with self.assertRaises(SystemExit):
                OUT.patch_staged_output(d)
            self.assertEqual(p.read_bytes(), bad.encode("latin-1"))

    def test_staged_write_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "TSOFT.ASM"
            p.write_bytes(FIX.encode("latin-1"))
            new = OUT.patch_staged_output(d)
            self.assertEqual(p.read_bytes().decode("latin-1"), new)


class Structure(unittest.TestCase):
    def setUp(self):
        self.t = patched()
        self.f = lines(self.t)

    def idx(self, s, start=0):
        return self.f.index(s, start)

    def test_marker_skips_copy_before_render(self):
        m = self.idx("TOutput_marker:")
        self.assertEqual(self.f[m + 1:m + 3],
                         ["    mov dirty,0", "    jmp TOutput_render"])
        self.assertIn("    cmp style,80", self.f)
        self.assertIn("    cmp style,81", self.f)
        # Markers are handled before any points/pen/brush are dereferenced.
        self.assertLess(m, self.idx("    les di,points"))

    def test_x_bounds_follow_validation(self):
        t = self.t
        scan = t[t.index("TOutput_scan_interval:"):t.index("TOutput_polyline:")]
        self.assertLess(scan.index("or_require jb,TOutput_render"),
                        scan.index("cmp bx,firstcol"))
        self.assertLess(scan.index("cmp dx,SCREEN_WIDTH"), scan.index("mov lastcol,dx"))
        poly = t[t.index("TOutput_poly_point:"):t.index("TOutput_two_point:")]
        self.assertLess(poly.index("cmp dx,SCREEN_WIDTH"), poly.index("mov firstcol,dx"))
        self.assertLess(poly.index("inc dx"), poly.index("mov lastcol,dx"))

    def test_synchronous_presentation_only(self):
        t = self.t
        self.assertEqual(t.count("call FlushRetainColumns"), 1)
        self.assertEqual(t.count("call FlushRetainRows"), 1)
        for banned in ("rr_bopen", "BatchClose", "rr_bfirst", "rr_settle"):
            self.assertNotIn(banned, t)
        # The presentation sits between the renderer call and the return.
        self.assertLess(t.index("cCall Output,"), t.index("call FlushRetainColumns"))
        self.assertLess(t.index("call FlushRetainColumns"), t.index("TOutput_done:"))
        self.assertLess(t.index("cCall Output,"), t.index("call FlushRetainRows"))
        self.assertLess(t.index("call FlushRetainRows"), t.index("TOutput_done:"))

    def test_full_scan_shortcut_is_after_safety_checks(self):
        t=self.t
        a=t.index("    cmp count,2\r\n    jne TOutput_scan_collect")
        b=t.index("TOutput_scan_collect:",a)
        fast=t[a:b]
        self.assertIn("    cmp word ptr es:[di+4],0\r\n",fast)
        self.assertIn("    cmp word ptr es:[di+6],SCREEN_WIDTH\r\n",fast)
        self.assertEqual(fast.count("    jne TOutput_scan_collect"),3)
        self.assertTrue(fast.endswith("    mov outrows,2\r\n    jmp TOutput_render\r\n"))
        prefix=t[:a]
        self.assertIn("    call ORowsSpanSafe\r\n",prefix)
        self.assertIn("    les di,mode\r\n",prefix)
        self.assertIn("    cmp ax,SCREEN_HEIGHT\r\n",prefix)
        self.assertIn("    mov firstrow,ax\r\n    inc ax\r\n    mov lastrow,ax\r\n",prefix)
        self.assertNotIn("firstcol",fast)

    def test_full_width_rows_do_not_read_uninitialized_columns(self):
        t=self.t
        a=t.index("; Preserve the actual renderer result")
        seg=t[a:t.index("TOutput_done:",a)]
        flag=seg.index("    cmp outrows,2\r\n    je TOutput_rows\r\n")
        self.assertLess(flag,seg.index("    cmp firstcol,0"))
        self.assertIn("    cmp lastcol,SCREEN_WIDTH\r\n    je TOutput_rows\r\n",seg)
        rows=seg[seg.index("TOutput_rows:"):seg.index("TOutput_full:")]
        self.assertEqual(rows,"TOutput_rows:\r\n    call FlushRetainRows\r\n    jmp short TOutput_flushed\r\n")
        self.assertLess(seg.index("    push cx"),seg.index("call FlushRetainColumns"))
        self.assertLess(seg.index("call FlushRetainColumns"),seg.index("    pop cx"))

    def test_fallback_unchanged(self):
        # Rejected cases still end in the stage's full FlushShadow.
        a = "TOutput_full:\r\n    call FlushShadow\r\nTOutput_flushed:"
        self.assertIn(a, self.t)
        self.assertIn("    cmp outrows,0\r\n    je TOutput_full\r\n", self.t)

    def test_rejection_sites_only_grow(self):
        # Every original rejection test is kept, except the one PR151
        # deliberately replaces (thin count == 2 becomes 2..1024); the only
        # additions are listed below.
        from collections import Counter
        old = Counter(l.strip() for l in lines(FIX) if "or_require" in l)
        new = Counter(l.strip() for l in self.f if "or_require" in l)
        self.assertEqual(old - new, Counter({"or_require je,TOutput_render": 1}))
        # ...plus the polyline loop's per-point X and Y screen checks.
        self.assertEqual(new - old, Counter({"or_require jae,TOutput_render": 1,
                                             "or_require jbe,TOutput_render": 1,
                                             "or_require jb,TOutput_render": 2}))

    def test_registers_preserved(self):
        t = self.t
        a = t.index("; Preserve the actual renderer result")
        b = t.index("TOutput_done:")
        seg = t[a:b]
        self.assertEqual(seg.count("    push "), seg.count("    pop "))
        self.assertEqual(re.findall(r"    push (\w+)", seg), ["ax", "bx", "cx", "dx"])
        self.assertEqual(re.findall(r"    pop (\w+)", seg), ["dx", "cx", "bx", "ax"])

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

    def test_no_xr1_or_tandy_assumptions(self):
        for banned in ("cursor_begin_retain", "SCREEN_W_BYTES*4", "bp-26", "viewport",
                       "cursor_end_retain", "lea si,[bp"):
            self.assertNotIn(banned, self.t)


# --- plane-aware model ------------------------------------------------------

def set_pixel(sh, x, y, colour):
    """Write an IRGB colour into the 640-wide four-plane shadow."""
    base = y * 320 + (x >> 3)
    bit = 0x80 >> (x & 7)
    for k, mask in enumerate((4, 2, 1, 8)):          # shadow plane R,G,B,I
        if colour & mask:
            sh[base + 80 * k] |= bit
        else:
            sh[base + 80 * k] &= ~bit & 0xFF


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


def flush_region(vram, shadow, r0, r1, c0, c1):
    """FlushRetainColumns on rows r0..r1 (excl) and byte columns c0..c1."""
    for y in range(r0, r1):
        di = (y & 1) * 0x2000 + (y >> 1) * 80
        for k, mask in enumerate(P15.HW_MASK):
            for p in range(4):
                if mask & (1 << p):
                    s = y * 320 + 80 * k + c0
                    vram[p * 0x4000 + di + c0:p * 0x4000 + di + c1] = shadow[s:s + (c1 - c0)]


def apply_gate(shadow_old, draw, bounds):
    """Draw in the shadow, present the gate's region, return (vram, expected)."""
    new = bytearray(shadow_old)
    draw(new)
    vram = P15.model_flush(bytes(shadow_old))
    y0, y1, x0, x1 = bounds
    c0, c1 = OUT.flush_columns(x0, x1)
    flush_region(vram, new, y0, y1, c0, c1)
    return vram, P15.model_flush(bytes(new))


class Model(unittest.TestCase):
    def test_rounding_edges(self):
        self.assertEqual(OUT.flush_columns(0, 1), (0, 1))
        self.assertEqual(OUT.flush_columns(0, 8), (0, 1))
        self.assertEqual(OUT.flush_columns(0, 9), (0, 2))
        self.assertEqual(OUT.flush_columns(7, 9), (0, 2))
        self.assertEqual(OUT.flush_columns(8, 9), (1, 2))
        self.assertEqual(OUT.flush_columns(631, 632), (78, 79))
        self.assertEqual(OUT.flush_columns(632, 633), (79, 80))
        self.assertEqual(OUT.flush_columns(639, 640), (79, 80))
        self.assertEqual(OUT.flush_columns(0, 640), (0, 80))
        # The exclusive right edge never exceeds the 80 byte plane row.
        for x1 in range(1, 641):
            self.assertLessEqual(OUT.flush_columns(x1 - 1, x1)[1], 80)

    def test_bounds_scanlines(self):
        self.assertEqual(OUT.scan_bounds(5, [(10, 20), (3, 4), (100, 101)]),
                         (5, 6, 3, 101))
        self.assertEqual(OUT.scan_bounds(199, [(632, 640)]), (199, 200, 632, 640))
        self.assertEqual(OUT.scan_bounds(0, [(0, 1)]), (0, 1, 0, 1))
        self.assertIsNone(OUT.scan_bounds(200, [(0, 1)]))        # row off screen
        self.assertIsNone(OUT.scan_bounds(-1, [(0, 1)]))
        self.assertIsNone(OUT.scan_bounds(0, [(4, 4)]))          # empty interval
        self.assertIsNone(OUT.scan_bounds(0, [(0, 641)]))        # right > width
        self.assertIsNone(OUT.scan_bounds(0, [(0, 5), (9, 3)]))

    def test_bounds_polyline(self):
        self.assertEqual(OUT.polyline_bounds([(3, 9), (20, 2)]), (2, 10, 3, 21))
        self.assertEqual(OUT.polyline_bounds([(639, 199), (0, 0)]), (0, 200, 0, 640))
        self.assertEqual(OUT.polyline_bounds([(5, 5), (9, 5), (9, 12), (1, 7)]),
                         (5, 13, 1, 10))
        self.assertIsNone(OUT.polyline_bounds([(5, 5), (5, 5)]))      # fallback
        self.assertIsNone(OUT.polyline_bounds([(640, 0), (1, 1)]))     # x off screen
        self.assertIsNone(OUT.polyline_bounds([(0, 200), (1, 1)]))     # y off screen
        self.assertIsNone(OUT.polyline_bounds([(-1, 0), (1, 1), (2, 2)]))
        self.assertIsNone(OUT.polyline_bounds([(1, 1)]))
        self.assertIsNone(OUT.polyline_bounds([(1, 1)] * 1025))
        self.assertIsNotNone(OUT.polyline_bounds([(1, 1)] * 1024 + [(2, 2)][:0]))

    def test_polyline_region_equals_full_flush(self):
        rnd = random.Random(1512)
        old = bytes(rnd.randrange(256) for _ in range(64000))
        shapes = [[(0, 0), (639, 199)], [(639, 0), (0, 199)], [(0, 5), (639, 5)],
                  [(7, 0), (7, 199)], [(8, 100), (8, 101)], [(631, 3), (632, 3)],
                  [(0, 0), (1, 0)], [(639, 199), (638, 199)]]
        for _ in range(200):
            n = rnd.choice((2, 2, 3, 5, 9))
            shapes.append([(rnd.randrange(640), rnd.randrange(200)) for _ in range(n)])
        for pts in shapes:
            b = OUT.polyline_bounds(pts)
            if b is None:
                continue
            col = rnd.randrange(16)

            def draw(sh, pts=pts, col=col):
                for a, c in zip(pts, pts[1:]):
                    for x, y in line_pixels(a, c):
                        set_pixel(sh, x, y, col)
            vram, want = apply_gate(old, draw, b)
            self.assertEqual(vram, want, pts[:3])

    def test_scanline_region_equals_full_flush(self):
        rnd = random.Random(640)
        old = bytes(rnd.randrange(256) for _ in range(64000))
        cases = [(0, [(0, 640)]), (199, [(632, 640)]), (3, [(7, 9)]), (3, [(0, 1)]),
                 (9, [(639, 640)]), (9, [(8, 16)]), (9, [(1, 2), (630, 632)])]
        for _ in range(200):
            ivs = []
            for _ in range(rnd.choice((1, 2, 4))):
                a = rnd.randrange(639)
                ivs.append((a, rnd.randrange(a + 1, 641)))
            cases.append((rnd.randrange(200), ivs))
        for y, ivs in cases:
            b = OUT.scan_bounds(y, ivs)
            col = rnd.randrange(16)

            def draw(sh, y=y, ivs=ivs, col=col):
                for l, r in ivs:
                    for x in range(l, r):
                        set_pixel(sh, x, y, col)
            vram, want = apply_gate(old, draw, b)
            self.assertEqual(vram, want, (y, ivs))

    def test_model_detects_narrow_or_unrounded_region(self):
        # Negative controls: without outward rounding, or one column short,
        # a pixel at a byte edge stays stale in a plane.
        old = bytes(64000)
        pts = [(7, 10), (9, 10)]
        b = OUT.polyline_bounds(pts)

        def draw(sh):
            for x, y in line_pixels(*pts):
                set_pixel(sh, x, y, 15)
        new = bytearray(old)
        draw(new)
        want = P15.model_flush(bytes(new))
        for c0, c1 in ((7 >> 3, 9 >> 3), (0, 1), (1, 2)):
            vram = P15.model_flush(old)
            flush_region(vram, new, b[0], b[1], c0, c1)
            self.assertNotEqual(vram, want)
        vram = P15.model_flush(old)
        flush_region(vram, new, b[0], b[1], *OUT.flush_columns(b[2], b[3]))
        self.assertEqual(vram, want)

    def test_all_four_planes_presented(self):
        # A pixel in each single colour plane reaches its hardware plane.
        for colour in (1, 2, 4, 8, 15):
            old = bytes(64000)
            pts = [(100, 50), (100, 51)]
            b = OUT.polyline_bounds(pts)

            def draw(sh, c=colour):
                for x, y in line_pixels(*pts):
                    set_pixel(sh, x, y, c)
            vram, want = apply_gate(old, draw, b)
            self.assertEqual(vram, want)
            self.assertEqual(P15.p1512_pixel(vram, 50, 100), colour)


class Scope(unittest.TestCase):
    def test_only_build15_uses_p15out(self):
        root = HERE.parents[1]
        users = set()
        for p in list(root.glob("src/**/*.PY")) + list(root.glob("tools/**/*.PY")) + \
                list(root.glob("experiments/**/*.PY")):
            if p.name in ("P15OUT.PY", "P15OTEST.PY"):
                continue
            text=p.read_bytes().decode("latin-1")
            if "P15OUT" not in text:continue
            # A source-hash binding is not an application of the patch.
            # Check imports/loaders and actual patch calls, without granting
            # another builder or verifier an exception to the integration rule.
            for node in ast.walk(ast.parse(text)):
                if isinstance(node,ast.Import) and any(n.name.split('.')[-1]=='P15OUT' for n in node.names):users.add(p.name)
                if isinstance(node,ast.ImportFrom) and (node.module or '').split('.')[-1]=='P15OUT':users.add(p.name)
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                    if node.func.attr=='patch_staged_output':users.add(p.name)
                    if node.func.attr=='SourceFileLoader' and any(isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.upper().endswith('P15OUT.PY') for n in ast.walk(node)):
                        users.add(p.name)
        self.assertEqual(users, {"BUILD15.PY"})

    def test_build15_applies_it_once_after_patch_staged(self):
        t = (HERE / "BUILD15.PY").read_bytes().decode("latin-1")
        self.assertEqual(t.count("P15OUT.patch_staged_output("), 1)
        self.assertLess(t.index("P15.patch_staged("), t.index("P15OUT.patch_staged_output("))
        self.assertLess(t.index("P15OUT.patch_staged_output("), t.index("d = ren / "))


if __name__ == "__main__":
    unittest.main(verbosity=1)
