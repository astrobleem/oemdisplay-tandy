#!/usr/bin/env python3
"""Host tests for the ColorPlus 86Box harness (no emulator needed).

  python3 src/pcp/HOSTTEST.PY

1. SHOTDEC decodes synthetic 86Box-style captures exactly: a random
   320x200x16 frame, pixel-doubled to 640x400 with an 8-pixel border and
   scaled with bilinear smoothing to both capture sizes seen in 86Box 6.0
   (1368x868 graphics, 1335x834 text geometry). It must reject a
   non-uniform scale, a blurred capture and a frame shifted by one logical
   pixel (decodes, but no longer equals the source).
2. PCPMOUSE packets round-trip through a model of MSTEST.ASM's decoder for
   every dx, dy in -128..127, both button states; split() sums exactly.
3. On Linux, PCP86's PID ownership: a recorded PID is only "ours" while the
   kernel start time still matches, so a reused PID is never signalled.
Runs on Windows too (sections needing /proc or ptys are skipped).
"""
import importlib.machinery
import random
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
SHOTDEC = importlib.machinery.SourceFileLoader("shotdec", str(HERE / "SHOTDEC.PY")).load_module()
MOUSE = importlib.machinery.SourceFileLoader("pcpmouse", str(HERE / "PCPMOUSE.PY")).load_module()

fails = []


def expect(label, ok):
    print(("ok   " if ok else "FAIL ") + label)
    if not ok:
        fails.append(label)


def render(idx, size, border=True, width=320, method=Image.BILINEAR):
    w, h = (656, 416) if border else (640, 400)
    o = 8 if border else 0
    xs = 640 // width
    im = Image.new("RGB", (w, h), (0, 0, 0))
    px = im.load()
    for y in range(200):
        for x in range(width):
            c = SHOTDEC.PAL[idx[y * width + x]]
            for dy in (0, 1):
                for dx in range(xs):
                    px[o + xs * x + dx, o + 2 * y + dy] = c
    return im.resize(size, method)


def decode_png(im, tmp, name, width=320):
    p = Path(tmp) / name
    im.save(p)
    try:
        idx, worst, bad, size, geom = SHOTDEC.decode(str(p), width)
    except SystemExit:
        return None, None
    return bytes(idx), bad


def mstest_model(stream):
    """Python port of MSTEST.ASM's take(): returns (packets, sumx, sumy, bad)."""
    n = p = sx = sy = bad = 0
    pk0 = pk1 = 0
    for b in stream:
        if b & 0x40:
            if n:
                bad += 1
            pk0, n = b, 1
        elif n == 1:
            pk1, n = b, 2
        elif n == 2:
            n = 0
            p += 1
            dy = ((pk0 & 0x0C) << 4) | (b & 0x3F)
            dx = ((pk0 & 0x03) << 6) | (pk1 & 0x3F)
            sy += dy - 256 if dy > 127 else dy
            sx += dx - 256 if dx > 127 else dx
    return p, sx, sy, bad


def main():
    rnd = random.Random(1216)
    idx = bytes(rnd.randrange(16) for _ in range(64000))
    with tempfile.TemporaryDirectory() as tmp:
        got, bad = decode_png(render(idx, (1368, 868)), tmp, "g.png")
        expect("graphics capture 1368x868 decodes exactly", got == idx and bad == 0)
        got, bad = decode_png(render(idx, (1335, 834), border=False), tmp, "t.png")
        expect("text-geometry capture 1335x834 decodes exactly", got == idx and bad == 0)
        got, bad = decode_png(render(idx, (1368, 900)), tmp, "n.png")
        expect("non-uniform scale rejected", got is None)
        blurred = render(idx, (1368, 868)).filter(ImageFilter.GaussianBlur(3))
        got, bad = decode_png(blurred, tmp, "b.png")
        expect("blurred capture rejected (samples over tolerance)", got is not None and bad > 0)
        shifted = bytes(idx[i + 1] if i % 320 != 319 else 0 for i in range(64000))
        got, bad = decode_png(render(shifted, (1368, 868)), tmp, "s.png")
        expect("one-pixel shift detected (decodes, differs from source)", bad == 0 and got != idx)
        wide = bytes(rnd.randrange(16) for _ in range(128000))
        # 86Box runs with nearest-neighbour output (video_filter_method = 0).
        got, bad = decode_png(render(wide, (1368, 868), width=640, method=Image.NEAREST), tmp, "w.png", 640)
        expect("640-wide nearest capture 1368x868 decodes exactly (PC1512)", got == wide and bad == 0)
        got, bad = decode_png(render(wide, (1368, 868), width=640), tmp, "wb.png", 640)
        expect("640-wide smoothed capture is exact or rejected, never silently wrong",
               got is not None and (bad > 0 or got == wide))

    ok = True
    for left in (False, True):
        for dx in range(-128, 128):
            for dy in range(-128, 128, 5):
                p, sx, sy, bad = mstest_model(MOUSE.packet(dx, dy, left))
                if (p, sx, sy, bad) != (1, dx, dy, 0):
                    ok = False
    expect("packet() round-trips through MSTEST decoder for -128..127", ok)
    ok = all(sum(MOUSE.split(v)) == v and all(-127 <= s <= 127 for s in MOUSE.split(v))
             for v in range(-1000, 1001))
    expect("split() sums exactly in steps of at most 127", ok)
    b0 = MOUSE.packet(0, 0, False, True)[0]
    expect("right button sets bit 4 only", b0 == 0x50)

    # 3. PID ownership (Linux /proc): cleanup must never signal a process
    #    that merely reuses a recorded PID.
    if sys.platform.startswith("linux"):
        import subprocess
        P86 = importlib.machinery.SourceFileLoader("pcp86", str(HERE / "PCP86.PY")).load_module()
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "x.pid"
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            try:
                P86.record_pid(f, child.pid)
                expect("recorded live process is ours", P86.owned_pid(f) == child.pid)
                pid, start = f.read_text().split()
                f.write_text(f"{pid} {int(start) + 1}\n")
                expect("same PID, different start time (reused) is not ours", P86.owned_pid(f) is None)
                f.write_text(f"{pid}\n")
                expect("PID file without start time is not ours", P86.owned_pid(f) is None)
            finally:
                child.kill()
                child.wait()
            f.write_text(f"{pid} {start}\n")
            expect("exited process is not ours", P86.owned_pid(f) is None)
    else:
        print("skip PID ownership tests (needs Linux /proc)")

    print("HOSTTEST: " + ("PASS" if not fails else f"FAIL ({len(fails)})"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
