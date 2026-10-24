#!/usr/bin/env python3
"""Compare two RRBENCH runs frame for frame (exact video memory).

  python3 src/rrect/RRCMP.PY <reference run> <candidate run> [--png <dir>] [--json <file>]

Each run directory holds RRBENCH.LOG and RBnn.BIN (the 32 KB B800h frame
buffer after stage nn; mode 09h: offset (y%4)*8192+(y//4)*160+x//2, even X
in the high nibble). Every stage present in either run must be present in
both with byte-identical 32,768-byte dumps (all banks, including the padding
bytes after each bank's 8,000 displayed bytes), the same stage names and the
same API success counts; for version 4 also every per-call frame of the
visible_steps stage (RVkk.BIN). Before any frame is compared, each run's log must
be complete (validate(): COMPLETE=1 last, every expected stage for its probe
version present in order, every batch's API_SUCCESSES present and equal to
its COUNT, every application found with three repaints, every dump 32,768
bytes); two equally incomplete runs fail. Differences are reported as a pixel count and
bounding box per stage; --png writes reference/candidate/difference images.
Timings are reported but never compared. Exit 0 only if everything matches.
"""
import argparse
import json
import sys
from pathlib import Path

IRGB = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0),
        (170, 170, 170), (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85),
        (255, 85, 255), (255, 255, 85), (255, 255, 255)]


def pixels(dump):
    """320x200 colour indices from a mode 09h dump."""
    out = bytearray(64000)
    for y in range(200):
        base = (y % 4) * 8192 + (y // 4) * 160
        for x in range(320):
            v = dump[base + x // 2]
            out[y * 320 + x] = (v >> 4) if x % 2 == 0 else (v & 15)
    return bytes(out)


def marker_oracle(directory, identity):
    """Independent full-viewport expectation for the eight direct Output cases.

    Software presents at bank offset zero. Existing XR1 hardware panning
    rotates each 8K bank by (panY/4)*160 + panX/2, with wrap inside the bank.
    The two scan rows are at viewport Y=144/145, X=4..44. Case 3 also writes
    a pixel; case 7 draws a third row through the rejected bounded gate.
    """
    hardware = identity.get("hardware") == ["1"]
    px, py = (int(x[0]) for x in identity["pan"])
    start = ((py // 4) * 160 + px // 2) & 8191 if hardware else 0
    rows = []
    for k in range(1, 10 if identity.get("version") == 6 else 9):
        path = directory / f"RM{k:02d}.BIN"
        if not path.exists() or path.stat().st_size != 32768:
            rows.append({"step": k, "pass": False, "error": "marker frame missing or truncated"})
            continue
        raw = path.read_bytes()
        got = bytearray(64000)
        for y in range(200):
            bank = (y % 4) * 8192
            base = start + (y // 4) * 160
            for x in range(320):
                byte = raw[bank + ((base + x // 2) & 8191)]
                got[y * 320 + x] = byte >> 4 if x % 2 == 0 else byte & 15
        want = bytearray([15]) * 64000
        for y in range(144, 147 if k == 7 else 146):
            for x in range(4, 45): want[y * 320 + x] = 0
        if k == 3: want[144 * 320 + 100] = 0
        count = sum(a != b for a, b in zip(got, want))
        rows.append({"step": k, "pass": count == 0, "differing_pixels": count, "pixels_compared": 64000})
    return rows


BATCHES = ("roundrect_key", "rectangle_key", "roundrect_large", "roundrect_hollow", "roundrect_nopen",
           "roundrect_xor", "roundrect_overlap", "roundrect_clipped", "ellipse_12")
APPS = ("calc", "reversi", "pbrush")


def expected_names(version, shots):
    """The stages RRBENCH runs, in order, for a given probe version."""
    if version == 1:
        return BATCHES + ("calc",)
    if version == 7:
        return ("visible_steps",)
    if version in (5, 6, 7):
        return BATCHES + ("cursor_overlap", "visible_steps", "marker_steps") + APPS
    if version in (2, 3, 4):
        if shots:
            return APPS
        return BATCHES + ("cursor_overlap",) + (("visible_steps",) if version >= 4 else ()) + APPS
    return None


def parse(log_text):
    """Header keys, then one dict per STAGE (every value list-valued, in order)."""
    head, rows = {}, []
    cur = head
    for line in log_text.replace("\r", "").split("\n"):
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k == "STAGE":
            cur = {"STAGE": [v]}
            rows.append(cur)
            continue
        cur.setdefault(k, []).append(v)
    return head, rows


def stages(log_text):
    """Per-stage summary (timings included) keyed by stage number."""
    out = {}
    for r in parse(log_text)[1]:
        try:
            n = int(r["STAGE"][0])
        except ValueError:
            continue
        s = out.setdefault(n, {"repaint_ms": [int(x) for x in r.get("REPAINT_MS", [])]})
        for k in ("NAME", "TITLE"):
            if k in r:
                s[k.lower()] = r[k][0]
        for k in ("ELAPSED_MS", "API_SUCCESSES", "COUNT", "LAUNCH_TO_PAINTED_MS", "APP_FOUND", "CALC_FOUND",
                  "STEP_DUMPS"):
            if k in r and r[k][0].lstrip("-").isdigit():
                s[k.lower()] = int(r[k][0])
    return out


def validate(log_text):
    """Return (identity, problems). A run is usable only if problems is empty:
    COMPLETE=1 last, every expected stage present in order, every batch with
    COUNT, ELAPSED_MS and API_SUCCESSES equal to COUNT, every application
    found with three repaint timings, every dump created with 32,768 bytes
    and every pre-stage clear successful."""
    bad = []
    head, rows = parse(log_text)
    lines = [x for x in log_text.replace("\r", "").split("\n") if x.strip()]

    def one_int(d, k, where):
        v = d.get(k)
        if not v or len(v) != 1 or not v[0].lstrip("-").isdigit():
            bad.append(f"{where}: {k} missing or malformed ({v})")
            return None
        return int(v[0])

    version = one_int(head, "VERSION", "header")
    one_int(head, "MULTIPLIER", "header")
    shots = one_int(head, "SHOTS", "header") if version and version >= 3 else 0
    if not lines or lines[-1] != "COMPLETE=1" or log_text.count("COMPLETE=") != 1:
        bad.append("run not complete (COMPLETE=1 must be the last line, once)")
    names = [r.get("NAME", ["?"])[0] for r in rows]
    if version in (5, 6, 7):
        if head.get("LOGICAL_WIDTH") != ["640"] or head.get("LOGICAL_HEIGHT") != ["256"]:
            bad.append("XR probe requires the current 640x256 dual-band driver")
        if head.get("PAN_RESULT") != ["1"]:
            bad.append("XR pan escape failed")
        for r in rows:
            if r.get("NAME") == ["marker_steps"] and r.get("RAW_OUTPUT_FOUND") != ["1"]:
                bad.append("direct driver Output entry was not found")
            if version == 6 and r.get("NAME") == ["marker_steps"]:
                for key in ("IDLE_VRAM_NOW", "IDLE_VRAM_LATER"):
                    if one_int(r, key, "idle observation") not in (0, 1):
                        bad.append("idle VRAM observation must be 0 or 1")
                ticks = one_int(r, "IDLE_BIOS_TICKS", "idle observation")
                if ticks is None or ticks < 9:
                    bad.append("idle observation must span nine BIOS clock ticks")
    want = expected_names(version, shots)
    if want is None:
        bad.append(f"unknown probe version {version}")
    elif tuple(names) != want:
        bad.append(f"stages {names} != expected {list(want)}")
    if [r["STAGE"][0] for r in rows] != [str(i + 1) for i in range(len(rows))]:
        bad.append("stage numbers are not 1..N")
    clears = head.get("CLEAR_SUCCESS", []) + [v for r in rows for v in r.get("CLEAR_SUCCESS", [])]
    if len(clears) < len(rows) or any(v != "1" for v in clears):    # cursor_overlap clears twice
        bad.append(f"clears {clears} for {len(rows)} stages")
    for r in rows:
        where = f"stage {r['STAGE'][0]} {r.get('NAME', ['?'])[0]}"
        if "KIND" in r:
            count = one_int(r, "COUNT", where)
            one_int(r, "ELAPSED_MS", where)
            api = one_int(r, "API_SUCCESSES", where)
            if count is not None and api is not None and (count <= 0 or api != count):
                bad.append(f"{where}: API_SUCCESSES {api} of COUNT {count}")
        else:
            found = r.get("APP_FOUND", r.get("CALC_FOUND"))
            if found != ["1"]:
                bad.append(f"{where}: application not found ({found})")
            if version and version >= 2 and not r.get("TITLE", [""])[0]:
                bad.append(f"{where}: no window title")
            one_int(r, "LAUNCH_TO_PAINTED_MS", where)
            if len(r.get("REPAINT_MS", [])) != 3 or not all(x.isdigit() for x in r["REPAINT_MS"]):
                bad.append(f"{where}: REPAINT_MS {r.get('REPAINT_MS')} (need three)")
        if "STEP_DUMPS" in r or r.get("NAME") == ["visible_steps"]:
            steps = one_int(r, "STEP_DUMPS", where)
            made, size = r.get("STEP_DUMP_CREATED", []), r.get("STEP_DUMP_BYTES", [])
            if (not steps or steps != len(made) or steps != one_int(r, "COUNT", where) or any(v != "1" for v in made)
                    or len(size) != len(made) or any(v != "32768" for v in size)):
                bad.append(f"{where}: step dumps {steps}, created {made} bytes {size}")
        made, size = r.get("DUMP_CREATED", []), r.get("DUMP_BYTES", [])
        if not made or any(v != "1" for v in made) or len(size) != len(made) or any(v != "32768" for v in size):
            bad.append(f"{where}: dumps created {made} bytes {size}")
    ident = {"version": version, "shots": shots, "multiplier": head.get("MULTIPLIER"),
             "screen": (head.get("SCREEN_WIDTH"), head.get("SCREEN_HEIGHT"))}
    if version in (5, 6, 7):
        ident["pan"] = (head.get("PAN_X"), head.get("PAN_Y"))
        ident["hardware"] = head.get("HARDWARE")
    return ident, bad


def compare_dumps(a, b):
    if len(a) != 32768 or len(b) != 32768:
        return {"equal": False, "error": f"dump sizes {len(a)}, {len(b)}"}
    if a == b:
        return {"equal": True, "differing_pixels": 0, "differing_bytes": 0}
    pa, pb = pixels(a), pixels(b)
    d = [i for i in range(64000) if pa[i] != pb[i]]
    box = None
    if d:
        xs, ys = [i % 320 for i in d], [i // 320 for i in d]
        box = [min(xs), min(ys), max(xs), max(ys)]
    return {"equal": False, "differing_bytes": sum(x != y for x, y in zip(a, b)),
            "differing_pixels": len(d), "bbox": box}


def image(px, path, diff_with=None):
    from PIL import Image
    im = Image.new("RGB", (320, 200))
    data = []
    for i, c in enumerate(px):
        if diff_with is not None:
            data.append((255, 0, 0) if c != diff_with[i] else tuple(v // 3 for v in IRGB[c]))
        else:
            data.append(IRGB[c])
    im.putdata(data)
    im.resize((640, 400), Image.NEAREST).save(path)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ref", type=Path)
    ap.add_argument("cand", type=Path)
    ap.add_argument("--png", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    problems = {}
    logs = {}
    oracles = {}
    for side, d in (("reference", a.ref), ("candidate", a.cand)):
        f = d / "RRBENCH.LOG"
        logs[side] = f.read_text(errors="replace") if f.exists() else ""
        ident, bad = validate(logs[side])
        logs[side + "_ident"] = ident
        if bad:
            problems[side] = bad
            for b in bad:
                print(f"INCOMPLETE {side}: {b}")
        elif ident.get("version") in (5, 6):
            oracles[side] = marker_oracle(d, ident)
            if not all(x["pass"] for x in oracles[side]):
                problems[side] = ["direct Output frames failed the independent pixel oracle"]
    if logs["reference_ident"] != logs["candidate_ident"]:
        problems["setup"] = [f"probe setup differs: {logs['reference_ident']} vs {logs['candidate_ident']}"]
        print("INCOMPLETE " + problems["setup"][0])
    sa, sb = stages(logs["reference"]), stages(logs["candidate"])
    ok = not problems and bool(sa) and sorted(sa) == sorted(sb)
    rows = []
    for n in sorted(set(sa) | set(sb)):
        ra, rb = sa.get(n, {}), sb.get(n, {})
        fa, fb = a.ref / f"RB{n:02d}.BIN", a.cand / f"RB{n:02d}.BIN"
        if fa.exists() and fb.exists():
            c = compare_dumps(fa.read_bytes(), fb.read_bytes())
        else:
            c = {"equal": False, "error": "dump missing"}
        keys = ("name", "count", "api_successes", "app_found", "calc_found", "title", "step_dumps")
        same_meta = bool(ra) and all(ra.get(k) == rb.get(k) for k in keys)
        row = {"stage": n, "name": ra.get("name"), "frame": c, "same_name_and_api_results": same_meta,
               "api_successes": ra.get("api_successes", ra.get("app_found", ra.get("calc_found"))),
               "ref_ms": ra.get("elapsed_ms", ra.get("repaint_ms")),
               "cand_ms": rb.get("elapsed_ms", rb.get("repaint_ms"))}
        ok = ok and c["equal"] and same_meta
        if ra.get("step_dumps"):
            # Frame after every single call of the stage (RVkk.BIN), compared like the final frame.
            row["steps"] = []
            for k in range(1, ra["step_dumps"] + 1):
                prefix = "RM" if ra.get("name") == "marker_steps" else "RV"
                ga, gb = a.ref / f"{prefix}{k:02d}.BIN", a.cand / f"{prefix}{k:02d}.BIN"
                sc = compare_dumps(ga.read_bytes(), gb.read_bytes()) if ga.exists() and gb.exists() \
                    else {"equal": False, "error": "step dump missing"}
                row["steps"].append(sc)
                ok = ok and sc["equal"]
                if not sc["equal"]:
                    print(f"   step {k:2d} DIFFERS {sc.get('differing_pixels', '-')} px {sc.get('bbox', '')}")
                    if a.png and "error" not in sc:
                        a.png.mkdir(parents=True, exist_ok=True)
                        image(pixels(gb.read_bytes()), a.png / f"V{k:02d}_DIFF.PNG", diff_with=pixels(ga.read_bytes()))
            print(f"   {sum(s['equal'] for s in row['steps'])} of {len(row['steps'])} per-call frames equal")
        rows.append(row)
        print(f"{n:2d} {str(ra.get('name')):18s} {'EQUAL' if c['equal'] else 'DIFFERS'} "
              f"{c.get('differing_pixels', '-')} px {c.get('bbox', '')}  ref {row['ref_ms']}  cand {row['cand_ms']}")
        if a.png and not c["equal"] and "error" not in c:
            a.png.mkdir(parents=True, exist_ok=True)
            pa, pb = pixels(fa.read_bytes()), pixels(fb.read_bytes())
            image(pa, a.png / f"S{n:02d}_REF.PNG")
            image(pb, a.png / f"S{n:02d}_CAND.PNG")
            image(pb, a.png / f"S{n:02d}_DIFF.PNG", diff_with=pa)
    res = {"reference": str(a.ref.name), "candidate": str(a.cand.name), "runs_complete": not problems,
           "problems": problems, "all_frames_equal": ok, "stages": rows, "marker_oracle": oracles}
    if a.json:
        a.json.write_text(json.dumps(res, indent=1) + "\n")
    print("ALL FRAMES EQUAL" if ok else ("RUNS INCOMPLETE" if problems else "FRAMES DIFFER"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
