#!/usr/bin/env python3
"""Decode and check CGAPAN native captures. Host-side developer tool.

  python -B src/cga/PANVIEW.PY --run RUN-DIR --out NEW-DIR

RUN-DIR is an owned native run that drove PANMET: its PANMET.LOG gives each
step's viewport origin and its NNN.VRM files are 16 KB IBM CGA VRAM captures
(capture NNN follows step NNN-1). Frames are decoded with CGAMODEL, checked
against the tile pattern PANMET paints, stamped into a logical canvas to prove
overlapping frames agree, and written as one PNG per step. The PNGs are host
renderings of decoded VRAM at the 5:6 pixel aspect (4:3 picture), not
Windows screenshots of scanout and not a composite desktop. No hardware I/O.
"""
import argparse
import json
import re
import sys
from pathlib import Path
import CGAMODEL as M

VIEW_W, VIEW_H, LOGICAL_W, LOGICAL_H = 160, 100, 320, 200
# Windows parks its pointer at the desktop centre (the startup hourglass, then
# the arrow), so frames legitimately differ there; cursor tests cover it.
POINTER_ZONE = (148, 88, 172, 112)
# CGA RGBI as displayed by an RGB monitor (color 6 is brown).
PALETTE = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0),
           (170, 170, 170), (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85),
           (255, 85, 255), (255, 255, 85), (255, 255, 255)]
CURSOR_STEPS = (13, 14, 15)          # frames that include the pointer
CHANGED_STEPS = (8, 9, 10, 11, 12)   # the probe edits the logical desktop here


def tile_color(tx, ty):
    c = (tx + ty * 3 + 1) & 15
    return c or 15


def steps_from_log(text):
    """Map step number -> viewport origin in effect when it finished."""
    origin, result = (0, 0), {}
    for line in text.splitlines():
        m = re.match(r'PAN req=\S+ ret=\S+ now=(\d+),(\d+) ', line)
        if m:
            origin = (int(m[1]), int(m[2]))
        m = re.match(r'STEP (\d+) DONE', line)
        if m:
            result[int(m[1])] = origin
    return result


def load_frames(run, steps):
    frames = {}
    for step in sorted(steps):
        path = run / ('%03d.VRM' % (step + 1))
        if path.exists():
            frames[step] = M.decode(bytearray(path.read_bytes()))
    return frames


def check_pattern(frame, left, top):
    """Tile interiors (clear of the 2-digit labels) hold the painted color."""
    wrong = []
    for y in range(VIEW_H):
        for x in range(VIEW_W):
            lx, ly = left + x, top + y
            tx, ty = lx // 40, ly // 40
            if lx % 40 >= 20 and ly % 40 >= 20 and lx % 40 < 38 and ly % 40 < 38:
                if frame[y][x] != tile_color(tx, ty):
                    wrong.append((lx, ly, frame[y][x], tile_color(tx, ty)))
    return wrong


def stamp(canvas, frame, left, top):
    """Return conflicting logical pixels; fill empty canvas cells."""
    bad = []
    for y in range(VIEW_H):
        for x in range(VIEW_W):
            if POINTER_ZONE[0] <= left + x < POINTER_ZONE[2] and POINTER_ZONE[1] <= top + y < POINTER_ZONE[3]:
                continue
            cell, v = canvas[top + y][left + x], frame[y][x]
            if cell is None:
                canvas[top + y][left + x] = v
            elif cell != v:
                bad.append((left + x, top + y, cell, v))
    return bad


def png(frame, path, label):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (VIEW_W, VIEW_H))
    im.putdata([PALETTE[v] for row in frame for v in row])
    im = im.resize((VIEW_W * 5, VIEW_H * 6), Image.Resampling.NEAREST)
    ImageDraw.Draw(im).text((4, 584), label, fill=(255, 255, 255))
    im.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    steps = steps_from_log((a.run / 'PANMET.LOG').read_text(errors='replace'))
    frames = load_frames(a.run, steps)
    report = {'frames': {}, 'conflicts': 0, 'pattern_errors': 0, 'roundtrip': None,
              'rendering': 'host rendering of decoded VRAM; not scanout, not a composite'}
    canvas = [[None] * LOGICAL_W for _ in range(LOGICAL_H)]
    for step, frame in sorted(frames.items()):
        left, top = steps[step]
        entry = {'origin': [left, top], 'vram': '%03d.VRM' % (step + 1)}
        if step not in CHANGED_STEPS + CURSOR_STEPS:
            wrong = check_pattern(frame, left, top)
            conflicts = stamp(canvas, frame, left, top)
            entry.update(pattern_errors=len(wrong), conflicts=len(conflicts))
            report['pattern_errors'] += len(wrong)
            report['conflicts'] += len(conflicts)
        else:
            entry['note'] = 'pointer visible' if step in CURSOR_STEPS else 'logical desktop edited by the probe'
        png(frame, a.out / ('STEP%02d-%d-%d.PNG' % (step, left, top)), 'step %d origin %d,%d' % (step, left, top))
        report['frames'][str(step)] = entry
    if 10 in frames and 12 in frames:
        report['roundtrip'] = 'identical' if frames[10] == frames[12] else 'DIFFERENT'
    covered = sum(1 for row in canvas for v in row if v is not None)
    report['canvas_pixels_covered'] = covered
    (a.out / 'PANVIEW.JSON').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'frames'}, indent=2))
    return 0 if not report['conflicts'] and not report['pattern_errors'] and report['roundtrip'] != 'DIFFERENT' else 1


if __name__ == '__main__':
    sys.exit(main())
