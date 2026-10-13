#!/usr/bin/env python3
"""Exact checks of TEXT80 screens from T80SNAP records (SNAPS.BIN).

Library for T80WIN.PY, and a self-test:  python3 src/text80/T80CHK.PY --check

A record: 16-byte header (T8, number, columns, rows, pointer x, y in screen
pixels, viewport top, pointer-visible flag) and the text buffer twice,
pointer hidden then shown. Cells are 8x8 logical pixels: the hot spot
(x, y) is cell (y - top) >> 3, x >> 3 (rows of the viewport).
"""
import struct
import sys

HDR = struct.Struct("<8H")


def parse(data):
    out, i = [], 0
    while i + HDR.size <= len(data):
        magic, num, cols, rows, px, py, top, vis = HDR.unpack_from(data, i)
        if magic != 0x3854:
            raise ValueError(f"bad record at {i}")
        n = cols * rows
        if i + HDR.size + 4 * n > len(data):
            break                                    # still being written
        hid = list(struct.unpack_from(f"<{n}H", data, i + HDR.size))
        shown = list(struct.unpack_from(f"<{n}H", data, i + HDR.size + 2 * n))
        out.append({"n": num, "cols": cols, "rows": rows, "x": px, "y": py if py < 32768 else py - 65536,
                    "top": top, "visible": vis, "hidden": hid, "shown": shown})
        i += HDR.size + 4 * n
    return out


def rows(words, cols):
    text = bytes(w & 0xFF for w in words).decode("cp437")
    text = "".join(ch if ch.isprintable() else "." for ch in text)
    return [text[r * cols:(r + 1) * cols] for r in range(len(words) // cols)]


def find(words, cols, s):
    """(row, column) of every place s appears."""
    hits = []
    for r, line in enumerate(rows(words, cols)):
        c = line.find(s)
        while c >= 0:
            hits.append((r, c))
            c = line.find(s, c + 1)
    return hits


def cells_at(words, cols, r, c, n):
    return [words[r * cols + c + k] for k in range(n)]


def cursor(rec):
    """(ok, detail): hidden and shown buffers differ exactly in the hot spot
    cell, by attribute XOR 77h with the character unchanged (or not at all
    when the pointer is hidden or outside the screen)."""
    cols, nrows = rec["cols"], rec["rows"]
    diff = [k for k in range(cols * nrows) if rec["hidden"][k] != rec["shown"][k]]
    r, c = (rec["y"] - rec["top"]) >> 3, rec["x"] >> 3
    inside = 0 <= r < nrows and 0 <= c < cols and rec["y"] >= rec["top"]
    if not rec["visible"] or not inside:
        return diff == [], {"expected": None, "differs": diff}
    k = r * cols + c
    ok = diff == [k] and rec["hidden"][k] ^ rec["shown"][k] == 0x7700
    return ok, {"expected_cell": [r, c], "differs": [[d // cols, d % cols] for d in diff],
                "xor": hex(rec["hidden"][k] ^ rec["shown"][k]) if diff else None}


def same(a, b, allow=()):
    """Cells (row, col) where two buffers differ, except the allowed ones."""
    cols = len(a) // 25 if len(a) in (1000, 2000) else 80
    return [(k // cols, k % cols) for k in range(len(a)) if a[k] != b[k] and (k // cols, k % cols) not in allow]


def check():
    """Self-test: correct footprints pass; deliberately broken ones fail."""
    base = [0x7020 + (k % 50) for k in range(2000)]
    def rec(shown, x=100, y=50, vis=1, top=0):
        return {"cols": 80, "rows": 25, "x": x, "y": y, "top": top, "visible": vis,
                "hidden": list(base), "shown": shown}
    k = (50 >> 3) * 80 + (100 >> 3)
    good = list(base)
    good[k] ^= 0x7700
    results = {"correct footprint": cursor(rec(good))[0]}
    bad = list(base); bad[k + 1] ^= 0x7700
    results["shifted one cell right"] = not cursor(rec(bad))[0]
    bad = list(base); bad[k + 80] ^= 0x7700
    results["shifted one row down"] = not cursor(rec(bad))[0]
    bad = list(base); bad[k] ^= 0x7000
    results["wrong attribute change"] = not cursor(rec(bad))[0]
    bad = list(good); bad[k + 2] ^= 0x0001
    results["an extra changed cell"] = not cursor(rec(bad))[0]
    results["no pointer drawn"] = not cursor(rec(list(base)))[0]
    bad = list(base); bad[k] ^= 0x0077
    results["character changed instead"] = not cursor(rec(bad))[0]
    results["hidden pointer, no change"] = cursor(rec(list(base), vis=0))[0]
    k2 = ((90 - 40) >> 3) * 80 + (100 >> 3)
    good2 = list(base); good2[k2] ^= 0x7700
    results["viewport top 40"] = cursor(rec(good2, y=90, top=40))[0]
    results["viewport top ignored is caught"] = not cursor(rec(good2, y=90, top=0))[0]
    txt = list(base)
    for i, ch in enumerate("Hello"):
        txt[3 * 80 + 7 + i] = 0xF000 | ord(ch)
    results["find text"] = find(txt, 80, "Hello") == [(3, 7)]
    for name, ok in results.items():
        print(("ok   " if ok else "FAIL ") + name)
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else 0)
