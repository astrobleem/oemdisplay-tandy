#!/usr/bin/env python3
"""Prepare an 86Box VM for the TEXT80 tests: the existing driver installed
as a user would have it, plus the TEXT80 package in C:\\T80 (not yet set up).

  python3 src/text80/T80PREP.PY --vm <new dir> --pristine <PCJSIMG output>
      --machine xtcga|tandyhx --base-drv <driver> --pkg <dir> --tools <dir>

machine xtcga:   IBM XT 4.77 MHz + IBM CGA (src/xtpan/PCP86.PY target txt40),
                 existing driver TXT40.DRV (40-column text, ai/txt40-tv)
machine tandyhx: Tandy 1000 HX 7.16 MHz, its own video (target xtbase),
                 existing driver TR53216.DRV (the shipped Windows XT driver)
Both: the first-party 8x8 system/fixed/OEM fonts (as Windows XT installs
them), WIN.INI's [fonts] list untouched, a serial mouse on a host pty.
--pkg: TEXT80.DRV, T80HELV.FON, T80COUR.FON, T80SET.EXE, T80ON.BAT,
T80OFF.BAT; T80PAN.DRV, T80VGA.DRV and XTPAN.EXE when present (+ XTTSYS.FON, XTCFIX.FON, XTCOEM.FON from distributions/WINXT).
--tools: T80SNAP.EXE (added to load= as C:\\T80\\T80SNAP.EXE, so the
installer must keep an existing load= entry), TPROF.EXE, T40ID.COM,
MSTEST.COM. Writes <vm>/T80PREP.JSN (every file's SHA-256).
"""
import argparse
import hashlib
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PCP86 = importlib.machinery.SourceFileLoader("pcp86x", str(ROOT / "src" / "xtpan" / "PCP86.PY")).load_module()
PART = "@@8704"
PKG = ["TEXT80.DRV", "T80HELV.FON", "T80COUR.FON", "T80SET.EXE", "T80ON.BAT", "T80OFF.BAT"]
OPTIONAL = ["T80PAN.DRV", "T80VGA.DRV", "XTPAN.EXE"]       # copied when the package has them
FONTS = ["XTTSYS.FON", "XTCFIX.FON", "XTCOEM.FON"]
TOOLS = ["T80SNAP.EXE", "TPROF.EXE"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vm", type=Path, required=True)
    ap.add_argument("--pristine", type=Path, required=True)
    ap.add_argument("--machine", choices=("xtcga", "tandyhx"), required=True)
    ap.add_argument("--base-drv", type=Path, required=True)
    ap.add_argument("--pkg", type=Path, required=True)
    ap.add_argument("--tools", type=Path, required=True)
    a = ap.parse_args()
    target = "txt40" if a.machine == "xtcga" else "xtbase"
    rec = PCP86.prepare(a.vm, a.pristine, a.base_drv, a.tools, mouse="pty", target=target,
                        drv_sha=sha(a.base_drv), fonts=str(ROOT / "distributions" / "WINXT"), grid=1)
    i = f"{a.vm / 'pcp.img'}{PART}"
    PCP86.mt("mmd", "-i", i, "::/T80")
    files = {}
    for n in PKG + [n for n in OPTIONAL if (a.pkg / n).is_file()]:
        PCP86.mt("mcopy", "-o", "-i", i, str(a.pkg / n), "::/T80/" + n)
        files["T80/" + n] = sha(a.pkg / n)
    for n in FONTS:
        p = ROOT / "distributions" / "WINXT" / n
        PCP86.mt("mcopy", "-o", "-i", i, str(p), "::/T80/" + n)
        files["T80/" + n] = sha(p)
    for n in TOOLS:
        PCP86.mt("mcopy", "-o", "-i", i, str(a.tools / n), "::/T80/" + n)
        files["T80/" + n] = sha(a.tools / n)
    if a.machine == "tandyhx":
        # Test harness only. At the Tandy 1000 DOS prompt the BIOS reads
        # scan code 2Bh (where 86Box puts the PC backslash key) as Left
        # arrow, which deletes the previous character: "CD \T80" arrived as
        # "CDT80". T80WIN.PY types these batch names there instead (Windows'
        # own keyboard driver is unaffected).
        bats = {"GOT80.BAT": "CD \\T80", "GOWIN.BAT": "CD \\WINDOWS",
                "T80/ONPAN.BAT": "T80ON C:\\WINDOWS PAN", "T80/ONVGA.BAT": "T80ON C:\\WINDOWS VGA"}
        for n, body in bats.items():
            tmp = a.vm / "prep" / n.split("/")[-1]
            tmp.write_bytes(("ECHO OFF\r\n" + body + "\r\n").encode("latin1"))
            PCP86.mt("mcopy", "-o", "-i", i, str(tmp), "::/" + n)
            files[n] = sha(tmp)
    win = PCP86.mt("mtype", "-i", i, "::/WINDOWS/WIN.INI").decode("latin1")
    lines = win.split("\r\n")
    k = [j for j, ln in enumerate(lines) if ln.lower().startswith("load=")]
    if len(k) != 1:
        raise SystemExit("T80PREP: WIN.INI has no single load= line")
    old = lines[k[0]]
    lines[k[0]] = old + ("" if old.endswith("=") else " ") + "C:\\T80\\T80SNAP.EXE"
    if (a.pkg / "XTPAN.EXE").is_file():
        # test harness only: the pan helper logs every pan with its time
        while lines and lines[-1] == "":
            lines.pop()
        lines += ["", "[XTPan]", "LogFile=C:\\T80\\XTPAN.LOG", ""]
    tmp = a.vm / "prep" / "WIN.INI"
    tmp.write_bytes("\r\n".join(lines).encode("latin1"))
    PCP86.mt("mcopy", "-o", "-i", i, str(tmp), "::/WINDOWS/WIN.INI")
    out = {"machine": a.machine, "harness_target": target, "base_driver": a.base_drv.name,
           "base_driver_sha256": sha(a.base_drv), "files": files,
           "win_ini_load_before": old, "win_ini_load_after": lines[k[0]],
           "fonts_list": "WIN.INI [fonts] untouched (no --only-8x8)", "harness_prep": rec}
    (a.vm / "T80PREP.JSN").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "harness_prep"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
