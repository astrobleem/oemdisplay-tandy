#!/usr/bin/env python3
"""Convert an existing Windows 3.0 install to the PCjr driver (emulated PCjr).

  python3 src/pcjr/INSTALL/JRCONV.PY --packet <JRPACK folder> --win30 <folder> --out <new dir>

Emulator evidence only (JRDBX.PY). Everything is typed into the guest:
 1. A stock Windows 3.0 Setup with the display Setup detects (CGA),
    keyboard PC/XT (84 keys), no network; Return to DOS.
 2. A user change made from DOS: a [PCjrTest] section appended to WIN.INI.
    The INI files and group files are then snapshotted from the host.
 3. C:\\PCJREXP\\JRGUARD; CD \\WINDOWS; SETUP; Display = Other, C:\\PCJREXP,
    the PCjr selector; ENTER; at the CONFIG.SYS question the default
    "Setup can make NO changes for you"; ENTER.
 4. Checks: in SYSTEM.INI only Setup's display, grabber and font entries
    (and [boot.description] display.drv) changed; WIN.INI, CONTROL.INI,
    PROGMAN.INI and every .GRP file are byte-identical, including the user's
    section; the PCjr files are installed.
 5. C:\\PCJREXP\\JRWIN starts Windows: the desktop is an exact 320x200 frame
    and Program Manager's saved window is reported (it was saved at CGA
    640x200 coordinates); Exit Windows.
Results: <out>/RESULT.JSN. Exit 0 only if every check passes.
"""
import argparse
import importlib.machinery
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
J = importlib.machinery.SourceFileLoader("jrdbx", str(HERE / "JRDBX.PY")).load_module()
S = importlib.machinery.SourceFileLoader("jrsess", str(HERE / "JRSESS.PY")).load_module()

EXPECTED_CHANGES = {("boot", "display.drv"), ("boot", "286grabber"), ("boot", "fonts.fon"),
                    ("boot", "fixedfon.fon"), ("boot", "oemfonts.fon"), ("boot.description", "display.drv")}


def ini_text(data):
    """{(section, key): value} of INI bytes, sections and keys lower case."""
    out, sec = {}, None
    for line in data.decode("latin-1").splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            sec = line[1:-1].lower()
        elif "=" in line and sec:
            k, v = line.split("=", 1)
            out[(sec, k.strip().lower())] = v.strip()
    return out


def stock_setup(r):
    r.dos("CD \\WIN30SRC")
    r.dos("SETUP", wait=8)
    J.key("Return", wait=4)
    J.key("Return", wait=6)
    J.key(*["Up"] * 4, wait=1)
    J.key("Return", wait=3)                          # Keyboard
    J.key(*["Down"] * 12, wait=1)
    J.key("Up", wait=0.5)
    J.key("Return", wait=3)                          # PC/XT - Type keyboard (84 keys)
    J.key("Up", wait=0.5)
    J.key("Return", wait=3)                          # Network
    J.key(*["Down"] * 20, wait=1)
    J.key("Up", "Up", "Up", wait=0.5)
    J.key("Return", wait=3)                          # No Network Installed
    r.shot("c01_stock_list")
    J.key("Return", wait=75)
    J.key("alt+p", wait=2)
    J.key("alt+a", wait=2)
    J.key("alt+d", wait=2)
    J.key("Return", wait=60)
    J.key("Down", "Down", wait=1)
    J.key("Return", wait=8)
    J.key("alt+d", wait=40)
    r.shot("c02_stock_done")
    J.key("alt+d", wait=12)                          # Return to DOS


def snapshot(c):
    w = c / "WINDOWS"
    names = ["SYSTEM.INI", "WIN.INI", "CONTROL.INI", "PROGMAN.INI"] + sorted(p.name for p in w.glob("*.GRP"))
    return {n: (w / n).read_bytes() for n in names}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packet", type=Path, required=True)
    ap.add_argument("--win30", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    out = a.out.resolve()
    if out.exists():
        raise SystemExit(f"JRCONV: {out} exists")
    r = S.Run(out)
    (out / "C").mkdir(parents=True)
    shutil.copytree(a.packet, r.c / "PCJREXP")
    shutil.copytree(a.win30, r.c / "WIN30SRC")
    res = {}
    J.start(out, 3600)
    try:
        stock_setup(r)
        r.dos("ECHO [PCjrTest]>>C:\\WINDOWS\\WIN.INI")
        r.dos("ECHO Keep=this user setting>>C:\\WINDOWS\\WIN.INI")
        before = snapshot(r.c)
        stock = S.ini(r.c / "WINDOWS" / "SYSTEM.INI")
        res["stock_display"] = stock.get("boot", {}).get("display.drv")
        r.dos("C:\\PCJREXP\\JRGUARD", wait=3)
        r.log_rc("GUARD")
        r.dos("CD \\WINDOWS")
        r.dos("SETUP", wait=8)
        r.shot("c03_maint_list")
        J.key(*["Up"] * 6, wait=1)
        J.key("Return", wait=3)                      # Display
        J.key(*["Down"] * 20, wait=1)
        J.key("Return", wait=3)                      # Other
        J.key("BackSpace", "BackSpace", "BackSpace", wait=0.5)
        J.text("C:\\PCJREXP")
        J.key("Return", wait=4)
        J.key("Return", wait=5)                      # the PCjr selector
        r.shot("c04_maint_selected")
        J.key("Return", wait=40)                     # accept: copy the PCjr files
        r.shot("c05_maint_config")
        J.key("Return", wait=30)                     # CONFIG.SYS: 3.) make NO changes (default)
        r.shot("c06_maint_done")
        after = snapshot(r.c)
        r.start_windows()
        d = r.shot("c07_desktop")
        r.check("converted_desktop_exact_frame", d is not None)
        r.exit_windows("WIN1")
        r.shot("c08_exit")
    finally:
        J.stop(out)
    sb, sa = ini_text(before["SYSTEM.INI"]), ini_text(after["SYSTEM.INI"])
    keys = set(sb) | set(sa)
    changed = sorted(k for k in keys if sb.get(k) != sa.get(k))
    r.check("system_ini_only_display_entries_changed", set(changed) <= EXPECTED_CHANGES and
            sa.get(("boot", "display.drv")) == "TNDYJR.DRV" and sa.get(("boot", "286grabber")) == "JRGRAB.GR2",
            changed={f"[{s}] {k}": [sb.get((s, k)), sa.get((s, k))] for s, k in changed})
    same = {n: before[n] == after.get(n) for n in before if n != "SYSTEM.INI"}
    r.check("other_ini_and_group_files_byte_identical", all(same.values()), files=same)
    r.check("user_section_kept", b"[PCjrTest]\r\nKeep=this user setting" in after["WIN.INI"])
    w = r.c / "WINDOWS" / "SYSTEM"
    inst = {n: (w / n).exists() and S.sha(w / n) == S.sha(a.packet / n)
            for n in ("TNDYJR.DRV", "JRGRAB.GR2", "XTESYS.FON", "XTEFIX.FON", "XTEOEM.FON")}
    r.check("pcjr_files_installed", all(inst.values()), files=inst)
    lines = [l for l in (r.c / "JRLOG.TXT").read_text(errors="replace").splitlines() if l.strip()] \
        if (r.c / "JRLOG.TXT").exists() else []
    r.check("guard_and_launch_logged", lines == ["GUARD RC=0", "WIN1 RC=0"], lines=lines)
    res["progman_window_after"] = S.ini(r.c / "WINDOWS" / "PROGMAN.INI").get("settings", {}).get("window")
    res["checks"] = r.checks
    res["passed"] = sum(c["result"] == "PASS" for c in r.checks)
    res["failed"] = sum(c["result"] == "FAIL" for c in r.checks)
    res["verdict"] = "PASS" if not res["failed"] else "FAIL"
    (out / "RESULT.JSN").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("verdict", "passed", "failed")}))
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
