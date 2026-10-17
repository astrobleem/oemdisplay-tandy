#!/usr/bin/env python3
"""Grabber switch test on the emulated PCjr (DOSBox-X; emulator evidence only).

  python3 src/pcjr/INSTALL/JRGRTEST.PY --installed <C dir of a JRSESS install> \
      --grabber <file.GR2> --tools <dir with JRMODE9.COM> --out <new dir>

Copies the installed drive C:, puts --grabber in C:\\WINDOWS\\SYSTEM and sets
only SYSTEM.INI [boot] 286grabber= to its name (test configuration, not an
install step), then starts Windows through C:\\PCJREXP\\JRWIN and runs:

  text  COMMAND.COM from File > Run, a known line typed, Alt+Tab to Windows
        (grabber SaveScreen), Alt+Tab back (RestoreScreen): the DOS screen
        must come back pixel-identical; EXIT returns to Windows, whose
        desktop must equal the one before the DOS program started.
  mode9 JRMODE9.COM (BIOS mode 09h, PCjr 320x200x16) from File > Run, then
        Alt+Tab. Recorded: whether Windows switched away or stayed in the
        program, and whether the program's screen survived. A key ends it.

Writes <out>/RESULT.JSN with the observations and the captures in
<out>/raw and <out>/dec. Exit 0 when the run completed (the verdicts are
data for docs/PCJR.MD; --expect-safe makes exit 0 require: text restore
exact, desktop restored, and mode9 not switched with its screen intact).
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


def same_raw(a, b):
    from PIL import Image
    with Image.open(a) as x, Image.open(b) as y:
        return x.convert("RGB").tobytes() == y.convert("RGB").tobytes()


def same_text_screen(run, ref, name, tries=8):
    """Capture <name> up to `tries` times about 0.4 s apart and report whether
    any capture equals <ref>: the DOS cursor blinks, so one capture can catch
    it in the other phase."""
    for _ in range(tries):
        J.shot(run, name, settle=0.3)
        if same_raw(Path(run) / "raw" / (ref + ".png"), Path(run) / "raw" / (name + ".png")):
            return True
    return False


def frame(run, name):
    data, bad = J.decode(Path(run) / "raw" / (name + ".png"))
    if data and not bad:
        J.save_frame(run, name, data)
        return data
    return None


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


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--installed", type=Path, required=True)
    ap.add_argument("--grabber", type=Path, required=True)
    ap.add_argument("--tools", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--expect-safe", action="store_true")
    a = ap.parse_args(argv)
    run = a.out.resolve()
    if run.exists():
        raise SystemExit(f"JRGRTEST: {run} exists")
    run.mkdir(parents=True)
    c = run / "C"
    shutil.copytree(a.installed, c)
    set_grabber(c, a.grabber)
    shutil.copyfile(a.tools / "JRMODE9.COM", c / "JRMODE9.COM")
    res = {"grabber": a.grabber.name.upper(), "grabber_sha256": hashlib.sha256(a.grabber.read_bytes()).hexdigest()}
    J.start(run, 1200)
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
        # text: switch away from and back to a text-mode DOS program
        run_cmd("COMMAND.COM", wait=12)
        J.text("ECHO PCjr grabber test 0123456789")
        J.key("Return", wait=3)
        J.shot(run, "text1")
        J.key("alt+Tab", wait=12)
        J.shot(run, "away1")
        away = frame(run, "away1")
        J.key("alt+Tab", wait=12)
        res["text_switched_to_windows"] = away is not None
        res["text_restored_exact"] = same_text_screen(run, "text1", "text2")
        J.text("EXIT")
        J.key("Return", wait=12)
        J.shot(run, "desk1")
        d1 = frame(run, "desk1")
        res["desktop_after_exit_equals_before"] = d0 is not None and d1 == d0
        # mode9: switch attempt from a PCjr-only graphics mode
        run_cmd("C:\\JRMODE9.COM", wait=10)
        J.shot(run, "g1")
        g1 = frame(run, "g1")
        J.key("alt+Tab", wait=12)
        J.shot(run, "g2")
        g2 = frame(run, "g2")
        res["mode9_shown"] = g1 is not None
        res["mode9_stayed_in_program"] = g1 is not None and g2 == g1
        res["mode9_switched_to_windows"] = g2 is not None and g2 != g1
        if res["mode9_switched_to_windows"]:
            J.key("alt+Tab", wait=12)
            J.shot(run, "g3")
            g3 = frame(run, "g3")
            res["mode9_restored_exact"] = g3 == g1
        J.key("space", wait=12)
        J.shot(run, "desk2")
        d2 = frame(run, "desk2")
        res["desktop_after_mode9_equals_before"] = d2 == d0
        J.key("alt+F4", wait=4)
        J.key("Return", wait=12)
        J.shot(run, "dos")
    finally:
        J.stop(run)
    safe = (res.get("text_restored_exact") and res.get("desktop_after_exit_equals_before") and
            res.get("mode9_stayed_in_program") and res.get("desktop_after_mode9_equals_before"))
    res["safe_on_this_emulator"] = bool(safe)
    (run / "RESULT.JSN").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0 if (safe or not a.expect_safe) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
