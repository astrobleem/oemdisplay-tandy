#!/usr/bin/env python3
"""Grabber switch test on the emulated PCjr (DOSBox-X; emulator evidence only).

  python3 src/pcjr/INSTALL/JRGRTEST.PY --installed <C dir of a JRSESS install> \\
      --grabber <file.GR2> --tools <dir with JRMODE.COM> --out <new dir> [--expect-jrgrab]

Copies the installed drive C:, puts --grabber in C:\\WINDOWS\\SYSTEM and sets
only SYSTEM.INI [boot] 286grabber= to its name (test configuration, not an
install step), starts Windows through C:\\PCJREXP\\JRWIN and, for every PCjr
BIOS mode m in 0 1 2 3 4 5 6 8 9 A, runs C:\\JRMODE.COM m from File > Run:

  - JRMODE sets mode m, draws its pattern through the BIOS and waits;
  - capture 'before'; Alt+Tab; capture 'after';
  - switched = 'after' is a decodable 320x200 frame (the Windows desktop);
    if it switched: Alt+Tab back and up to 8 captures must include one that
    equals 'before' (restored; text modes blink a cursor);
    if it did not: 'after' must equal 'before' (screen undisturbed);
  - a key ends JRMODE, which reads its pattern back through the BIOS and
    writes C:\\JRMODEm.TXT ('MODE m OK' only if every cell is intact);
  - the Windows desktop after the program must equal the one before.

Mode 7 (monochrome) does not exist on the PCjr and is not tested.
Writes <out>/RESULT.JSN (per-mode observations, the grabber and every input
hash) and captures in <out>/raw. Exit 0 when the run completed; with
--expect-jrgrab exit 0 also requires JRGRAB's intended behaviour:
modes 0-6 switch and restore exactly, modes 8, 9 and A refuse the switch
with the screen undisturbed, every JRMODE file says OK and every desktop
after a program equals the first one.
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
J = importlib.machinery.SourceFileLoader("jrdbx", str(HERE / "JRDBX.PY")).load_module()
S = importlib.machinery.SourceFileLoader("jrsess", str(HERE / "JRSESS.PY")).load_module()

MODES = ["0", "1", "2", "3", "4", "5", "6", "8", "9", "A"]
PCJR_ONLY = {"8", "9", "A"}


def raw_bytes(run, name):
    from PIL import Image
    with Image.open(Path(run) / "raw" / (name + ".png")) as im:
        return im.size, im.convert("RGB").tobytes()


def frame(run, name):
    data, bad = J.decode(Path(run) / "raw" / (name + ".png"))
    if data and not bad:
        J.save_frame(run, name, data)
        return data
    return None


def capture_matching(run, ref, name, tries=8):
    """Up to `tries` captures ~0.4 s apart; True if one equals <ref>."""
    want = raw_bytes(run, ref)
    for _ in range(tries):
        J.shot(run, name, settle=0.3)
        if raw_bytes(run, name) == want:
            return True
    return False


def set_grabber(c, grabber):
    sysdir = c / "WINDOWS" / "SYSTEM"
    shutil.copyfile(grabber, sysdir / grabber.name.upper())
    ini = c / "WINDOWS" / "SYSTEM.INI"
    lines = ini.read_bytes().decode("latin-1").split("\r\n")
    hits = [i for i, l in enumerate(lines) if l.lower().startswith("286grabber=")]
    if len(hits) != 1:
        raise SystemExit("JRGRTEST: SYSTEM.INI has no single 286grabber=")
    lines[hits[0]] = "286grabber=" + grabber.name.upper()
    ini.write_bytes("\r\n".join(lines).encode("latin-1"))


def run_cmd(cmd, wait):
    J.key("alt+f", wait=2)
    J.key("r", wait=3)
    J.text(cmd)
    J.key("Return", wait=wait)


def one_mode(run, c, m, d0):
    r = {}
    run_cmd(f"C:\\JRMODE.COM {m}", wait=12)
    J.shot(run, f"m{m}_before")
    r["program_screen_shown"] = frame(run, f"m{m}_before") != d0
    J.key("alt+Tab", wait=12)
    J.shot(run, f"m{m}_after")
    away = frame(run, f"m{m}_after")
    r["switched_to_windows"] = away is not None and raw_bytes(run, f"m{m}_after") != raw_bytes(run, f"m{m}_before")
    if r["switched_to_windows"]:
        J.key("alt+Tab", wait=12)
        r["restored_exact"] = capture_matching(run, f"m{m}_before", f"m{m}_back")
    else:
        r["screen_undisturbed"] = capture_matching(run, f"m{m}_before", f"m{m}_after2")
    J.key("space", wait=14)
    J.shot(run, f"m{m}_desk")
    r["desktop_after_equals_first"] = frame(run, f"m{m}_desk") == d0
    f = c / f"JRMODE{m}.TXT"
    r["program_result"] = f.read_bytes().decode("latin-1").strip() if f.exists() else None
    r["program_intact"] = r["program_result"] == f"MODE {m} OK"
    return r


def jrgrab_expected(modes):
    bad = {}
    for m, r in modes.items():
        ok = r["program_intact"] and r["desktop_after_equals_first"] and r["program_screen_shown"]
        if m in PCJR_ONLY:
            ok = ok and not r["switched_to_windows"] and r.get("screen_undisturbed") is True
        else:
            ok = ok and r["switched_to_windows"] and r.get("restored_exact") is True
        if not ok:
            bad[m] = r
    return bad


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--installed", type=Path, required=True)
    ap.add_argument("--grabber", type=Path, required=True)
    ap.add_argument("--tools", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--expect-jrgrab", action="store_true")
    a = ap.parse_args(argv)
    run = a.out.resolve()
    if run.exists():
        raise SystemExit(f"JRGRTEST: {run} exists")
    run.mkdir(parents=True)
    c = run / "C"
    shutil.copytree(a.installed, c)
    for f in c.glob("JRMODE*.TXT"):
        f.unlink()
    set_grabber(c, a.grabber)
    shutil.copyfile(a.tools / "JRMODE.COM", c / "JRMODE.COM")
    res = S.provenance(c / "PCJREXP", c / "WIN30SRC")
    res.update(grabber=a.grabber.name.upper(), grabber_sha256=hashlib.sha256(a.grabber.read_bytes()).hexdigest(),
               jrmode_sha256=hashlib.sha256((a.tools / "JRMODE.COM").read_bytes()).hexdigest(),
               installed_win_com_sha256=S.sha(c / "WINDOWS" / "WIN.COM"),
               untested=["7 (monochrome text: not a PCjr mode)"], modes={})
    J.start(run, 3000)
    try:
        J.mouse(run, "ident", "on")
        J.text("C:\\PCJREXP\\JRWIN")
        J.key("Return", wait=40)
        J.mouse(run, "ident", "off")
        J.mouse(run, "step", "2")
        J.mouse(run, "move", "400", "300")          # park the pointer bottom right
        time.sleep(8)
        J.shot(run, "desk0")
        d0 = frame(run, "desk0")
        res["first_desktop_exact_frame"] = d0 is not None
        for m in MODES:
            res["modes"][m] = one_mode(run, c, m, d0)
            print(m, json.dumps(res["modes"][m]), flush=True)
        J.key("alt+F4", wait=4)
        J.key("Return", wait=12)
        J.shot(run, "dos")
    finally:
        J.stop(run)
    bad = jrgrab_expected(res["modes"]) if d0 is not None else {"desk0": "not an exact frame"}
    res["matches_jrgrab_design"] = not bad
    res["differs_from_jrgrab_design"] = sorted(bad)
    (run / "RESULT.JSN").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("grabber", "matches_jrgrab_design", "differs_from_jrgrab_design")}))
    return 0 if (not bad or not a.expect_jrgrab) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
