#!/usr/bin/env python3
"""Host tests for JRCHECK.PY and T2CHECK.PY (no emulator needed).

Usage: python3 src/pcjr/CHKTEST.PY

Builds synthetic probe outputs in a temporary directory and checks that
each verifier passes only the cases it should. Also re-runs both verifiers
on the recorded emulator evidence that ships no dumps (report-only cases).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JRCHECK = ROOT / "src" / "pcjr" / "JRCHECK.PY"
T2CHECK = ROOT / "src" / "tga2" / "T2CHECK.PY"


def jr_page():
    v = bytearray(0x8000)
    for y in range(200):
        base = (y & 3) * 8192 + (y >> 2) * 160
        for xb in range(160):
            c = ((xb >> 3) + y) & 15
            v[base + xb] = (c << 4) | (c ^ 15)
    return bytes(v)


def t2_page():
    v = bytearray(0x10000)
    for y in range(200):
        for xb in range(320):
            c = ((xb >> 4) + y) & 15
            v[y * 320 + xb] = (c << 4) | (c ^ 15)
    return bytes(v)


JR_REPORT = ("MODEL=FD TANDYTAG=00\r\nMODE_BEFORE=03 MODE_AFTER=09\r\n"
             "PAGE_OK=01 WROTE=01 CONTROL=00\r\nCOMPLETE=1\r\n")
T2_SAFE = ("MODEL=FF TANDYTAG=21\r\nMAPPED_PARAS=1000 MAP_INCONSISTENT=00\r\n"
           "SAFE_TO_WRITE=01 PATTERN_RAN=01\r\nCOMPLETE=1\r\n")


def run(tool, d, *extra):
    return subprocess.run([sys.executable, "-I", str(tool), str(d), *extra],
                          capture_output=True, text=True).returncode


def case(tmp, name, files):
    d = Path(tmp) / name
    d.mkdir()
    for fn, data in files.items():
        (d / fn).write_bytes(data.encode() if isinstance(data, str) else data)
    return d


def main():
    page = jr_page()
    t2 = t2_page()
    fails = []

    def expect(label, got, want):
        ok = got == want
        print(("ok   " if ok else "FAIL ") + f"{label}: exit {got}, want {want}")
        if not ok:
            fails.append(label)

    with tempfile.TemporaryDirectory() as tmp:
        # JRCHECK
        expect("JR alias of a page half passes", run(JRCHECK, case(tmp, "j1", {
            "JRPROBE.TXT": JR_REPORT, "JRVRAM.BIN": page,
            "JRB800.BIN": page[:0x4000] * 2})), 0)
        expect("JR full 32KB window passes", run(JRCHECK, case(tmp, "j2", {
            "JRPROBE.TXT": JR_REPORT, "JRVRAM.BIN": page, "JRB800.BIN": page})), 0)
        expect("JR all-zero B800 fails", run(JRCHECK, case(tmp, "j3", {
            "JRPROBE.TXT": JR_REPORT, "JRVRAM.BIN": page,
            "JRB800.BIN": bytes(0x8000)})), 1)
        expect("JR all-FF B800 fails", run(JRCHECK, case(tmp, "j4", {
            "JRPROBE.TXT": JR_REPORT, "JRVRAM.BIN": page,
            "JRB800.BIN": b"\xff" * 0x8000})), 1)
        other = bytes((b + 1) & 255 for b in page[:0x4000])
        expect("JR alias of unrelated data fails", run(JRCHECK, case(tmp, "j5", {
            "JRPROBE.TXT": JR_REPORT, "JRVRAM.BIN": page,
            "JRB800.BIN": other * 2})), 1)
        bad = bytearray(page)
        bad[100] ^= 1
        expect("JR one wrong pattern byte fails", run(JRCHECK, case(tmp, "j6", {
            "JRPROBE.TXT": JR_REPORT, "JRVRAM.BIN": bytes(bad),
            "JRB800.BIN": bytes(bad)})), 1)
        expect("JR missing dumps fail", run(JRCHECK, case(tmp, "j7", {
            "JRPROBE.TXT": JR_REPORT})), 1)

        # T2CHECK
        expect("T2 safe report + good image passes", run(T2CHECK, case(tmp, "t1", {
            "T2PROBE.TXT": T2_SAFE, "T2VRAM.BIN": t2})), 0)
        for label, rep in (
                ("SAFE_TO_WRITE=00", T2_SAFE.replace("SAFE_TO_WRITE=01", "SAFE_TO_WRITE=00")),
                ("MAPPED_PARAS=0FFF", T2_SAFE.replace("MAPPED_PARAS=1000", "MAPPED_PARAS=0FFF")),
                ("MAP_INCONSISTENT=01", T2_SAFE.replace("MAP_INCONSISTENT=00", "MAP_INCONSISTENT=01")),
                ("SAFE_TO_WRITE missing", T2_SAFE.replace("SAFE_TO_WRITE=01 ", "")),
                ("PATTERN_RAN=00", T2_SAFE.replace("PATTERN_RAN=01", "PATTERN_RAN=00"))):
            expect(f"T2 good image under {label} fails", run(T2CHECK, case(
                tmp, "t_" + label.split("=")[0].split()[0] + label[-2:].strip(),
                {"T2PROBE.TXT": rep, "T2VRAM.BIN": t2})), 1)
        bad2 = bytearray(t2)
        bad2[5] ^= 0x10
        expect("T2 one wrong byte fails", run(T2CHECK, case(tmp, "t7", {
            "T2PROBE.TXT": T2_SAFE, "T2VRAM.BIN": bytes(bad2)})), 1)
        expect("T2 safe report, no dump is NOT TESTED", run(T2CHECK, case(tmp, "t8", {
            "T2PROBE.TXT": T2_SAFE})), 2)
        unm = ("MODEL=FF TANDYTAG=21\r\nMAPPED_PARAS=0000 MAP_INCONSISTENT=00\r\n"
               "SAFE_TO_WRITE=00 PATTERN_RAN=00\r\nCOMPLETE=1\r\n")
        expect("T2 unmapped control passes --expect-unmapped", run(T2CHECK, case(
            tmp, "t9", {"T2PROBE.TXT": unm}), "--expect-unmapped"), 0)
        expect("T2 safe report fails --expect-unmapped", run(T2CHECK, case(
            tmp, "t10", {"T2PROBE.TXT": T2_SAFE}), "--expect-unmapped"), 1)

        # Recorded TGA-II negative-control evidence (report only, no dump).
        for name in ("DTNT2.TXT", "XTNT2.TXT"):
            src = ROOT / "docs" / "tga2" / name
            expect(f"recorded {name} --expect-unmapped", run(T2CHECK, case(
                tmp, "r" + name[:5], {"T2PROBE.TXT": src.read_bytes()}),
                "--expect-unmapped"), 0)

    print("CHKTEST: " + ("PASS" if not fails else f"FAIL ({len(fails)})"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
