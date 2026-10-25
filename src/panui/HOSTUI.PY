#!/usr/bin/env python3
"""Host tests for the shared panning settings (src/panui/PANSET.C).

  python src/panui/HOSTUI.PY [--crlf]

1. SETTEST.C, compiled with PANSET.C by the host cc, prints the results of
   defaults, validation, PanParseInt, capability gating, persistence, the
   dialog model and the routing tables. They are checked here against the
   PANSET.H contract.
2. Source checks: the sync_helper transform of BUILDAPP.PY on XTPAN.C, the
   existing FollowTop host test (HOSTPAN.PY), the ordering rules in PANCFG.C,
   XYCTL.C and XTPAN.C, and PANDLG.C (skipped while the file is missing).
3. Lint of the panning files: comments, tabs, line length, ASCII, endings.
4. Optional 16-bit compile with C:\\WATCOM\\BINNT\\wcc.exe (skipped if absent).
"""
import argparse
import importlib.machinery
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WCC = Path(r"C:\WATCOM\BINNT\wcc.exe")
fails = []

VERT_DEF = {"step": 50, "dwell": 400, "edge": 3, "follow": 1}
XY_DEF = {"edgeOn": 0, "repeat": 100, "followDlg": 0, "mode": 0}
VERT_KEYS = {"XTPan.Step", "XTPan.Dwell", "XTPan.Edge", "XTPan.FollowActive"}
XY_KEYS = {"XYPan.EdgeOn", "XYPan.RepeatMs", "XYPan.FollowDialogs"}
FORBIDDEN_KEYS = {"Enabled", "KeyMods", "KeyDown", "KeyUp", "KeyTop",
                  "LogKeys", "LogFile"}
COMMENT = "/* The driver can reset its viewport on a Windows/DOS switch. */"
ANCHOR = "    DWORD now = GetCurrentTime();\n    Keys();"

PANUI_LINT = ["src/panui/PANSET.H", "src/panui/PANSET.C",
              "src/panui/PANDLG.H", "src/panui/PANDLG.C",
              "src/panui/SETTEST.C", "src/panui/HOSTUI.PY"]
OTHER_LINT = ["src/xtpan/XTPAN.C", "src/softpan/PANCFG.C",
              "experiments/XYOVERVIEW/XYCTL.C"]
COMMENT_LINT = ["src/panui/PANSET.H", "src/panui/PANSET.C",
                "src/panui/PANDLG.H", "src/panui/PANDLG.C",
                "src/panui/SETTEST.C", "src/xtpan/XTPAN.C",
                "src/softpan/PANCFG.C", "experiments/XYOVERVIEW/XYCTL.C"]


def expect(label, ok):
    print(("ok   " if ok else "FAIL ") + label)
    if not ok:
        fails.append(label)


def skip(label):
    print("skip " + label)


def text_of(path):
    return path.read_bytes().decode("latin-1").replace("\r\n", "\n")


def first_before(text, a, b):
    i, j = text.find(a), text.find(b)
    return i >= 0 and (j < 0 or i < j)


def eq(label, got, want):
    expect(label, got == want)


# ---------------------------------------------------------------- harness

def run_harness(tmp):
    if not (HERE / "PANSET.C").exists():
        expect("src/panui/PANSET.C exists (needed by SETTEST.C)", False)
        return None
    exe = Path(tmp) / "settest.exe"
    srcs = [str(HERE / "PANSET.C"), str(HERE / "SETTEST.C")]
    r = subprocess.run(["cc", "-std=c89", "-pedantic", "-Wall", "-Werror",
                        "-O1", "-o", str(exe)] + srcs,
                       capture_output=True, text=True)
    expect("SETTEST.C + PANSET.C compile as C89 (-pedantic -Wall -Werror)",
           r.returncode == 0)
    if r.returncode:
        print(r.stdout + r.stderr)
        return None
    r = subprocess.run([str(exe)], capture_output=True, text=True,
                       timeout=120)
    expect("SETTEST.C runs to completion", r.returncode == 0)
    R, T = {}, {}
    for line in r.stdout.splitlines():
        if line.startswith("TEXT "):
            parts = (line.split(" ", 2) + ["", ""])[1:3]
            T[parts[0]] = parts[1]
        elif " " in line:
            name, val = line.rsplit(" ", 1)
            R[name] = int(val)
    return R, T


def keys_of(T, name):
    return set(T.get(name, "").split())


def harness_checks(R, T):
    for k, d in VERT_DEF.items():
        eq(f"defaults VERT {k} = {d}", R.get("def.v." + k), d)
    for k, d in XY_DEF.items():
        eq(f"defaults XY {k} = {d}", R.get("def.x." + k), d)

    xtpan = text_of(REPO / "src/xtpan/XTPAN.C")
    for key, val in (("Step", 50), ("Dwell", 400), ("Edge", 3),
                     ("FollowActive", 1)):
        pat = r'GetProfileInt\("XTPan",\s*"%s",\s*%d\)' % (key, val)
        expect(f'XTPAN.C literal GetProfileInt("XTPan", "{key}", {val})',
               re.search(pat, xtpan) is not None)
    for k, d in VERT_DEF.items():
        eq(f"empty store, VERT load: {k} = default {d}",
           R.get("load.empty.v." + k), d)
    for k, d in XY_DEF.items():
        eq(f"empty store, XY load: {k} = default {d}",
           R.get("load.empty.x." + k), d)

    # Validation: (key, label, PS_E_* code or 0)
    val_rows = [
        ("val.v.step8", "VERT Step 8 ok", 0),
        ("val.v.step7", "VERT Step 7 bad (PS_E_STEP)", 2),
        ("val.v.step400", "VERT Step = workH ok", 0),
        ("val.v.step401", "VERT Step workH+1 bad (PS_E_STEP)", 2),
        ("val.v.step57", "VERT Step 57 ok (no 8/4 alignment)", 0),
        ("val.v.edge1", "VERT Edge 1 ok", 0),
        ("val.v.edge0", "VERT Edge 0 bad (PS_E_EDGE)", 3),
        ("val.v.edge100", "VERT Edge viewH/2 ok", 0),
        ("val.v.edge101", "VERT Edge viewH/2+1 bad (PS_E_EDGE)", 3),
        ("val.v.dwell0", "VERT Dwell 0 ok", 0),
        ("val.v.dwell10000", "VERT Dwell 10000 ok", 0),
        ("val.v.dwell10001", "VERT Dwell 10001 bad (PS_E_DWELL)", 4),
        ("val.v.dwellm1", "VERT Dwell -1 bad (PS_E_DWELL)", 4),
        ("val.v.follow2", "VERT Follow 2 bad (PS_E_FOLLOW)", 5),
        ("val.v.follow0", "VERT Follow 0 ok", 0),
        ("val.x.repeat100", "XY Repeat 100 ok", 0),
        ("val.x.repeat200", "XY Repeat 200 ok", 0),
        ("val.x.repeat500", "XY Repeat 500 ok", 0),
        ("val.x.repeat150", "XY Repeat 150 bad (PS_E_REPEAT)", 7),
        ("val.x.repeat0", "XY Repeat 0 bad (PS_E_REPEAT)", 7),
        ("val.x.repeat1000", "XY Repeat 1000 bad (PS_E_REPEAT)", 7),
        ("val.x.edgeOn0", "XY EdgeOn 0 ok", 0),
        ("val.x.edgeOn1", "XY EdgeOn 1 ok", 0),
        ("val.x.edgeOn2", "XY EdgeOn 2 bad (PS_E_EDGEON)", 6),
        ("val.x.followDlg0", "XY FollowDlg 0 ok", 0),
        ("val.x.followDlg1", "XY FollowDlg 1 ok", 0),
        ("val.x.followDlg2", "XY FollowDlg 2 bad (PS_E_FOLLOWD)", 8),
        ("val.x.mode0", "XY mode 0 ok (PS_CAP_MODE)", 0),
        ("val.x.mode1", "XY mode 1 ok (PS_CAP_MODE)", 0),
        ("val.x.mode2", "XY mode 2 REJECTED (PS_E_MODE)", 9),
        ("val.x.modem1", "XY mode -1 rejected (PS_E_MODE)", 9),
        ("val.x.mode3", "XY mode 3 rejected (PS_E_MODE)", 9),
        ("val.x.mode255", "XY mode 255 rejected (PS_E_MODE)", 9),
    ]
    for key, label, code in val_rows:
        eq("validate: " + label, R.get(key), code)

    pi_in = ["12", "  7 ", "", " ", "1x", "-5", "+5", "123456", "1 2",
             "12345"]
    pi_want = [(0, 12), (0, 7), (10, 999), (10, 999), (10, 999), (10, 999),
               (10, 999), (10, 999), (10, 999), (0, 12345)]
    for i, (src, (rc, val)) in enumerate(zip(pi_in, pi_want)):
        eq(f"PanParseInt {src!r}: returns {rc}", R.get(f"pi{i}.rc"), rc)
        eq(f"PanParseInt {src!r}: value {val}", R.get(f"pi{i}.val"), val)

    # Capability gating.
    eq("gate: VERT caps, garbage XY fields do not fail validation",
       R.get("gate.v.validate"), 0)
    eq("gate: VERT caps, Save returns PS_OK", R.get("gate.v.save"), 0)
    eq("gate: VERT caps, Save writes exactly the 4 XTPan keys",
       keys_of(T, "gate.v.log"), VERT_KEYS)
    eq("gate: VERT caps, Save put count is 4", R.get("gate.v.puts"), 4)
    eq("gate: XY caps, garbage vertical fields do not fail validation",
       R.get("gate.x.validate"), 0)
    eq("gate: XY caps, Save returns PS_OK", R.get("gate.x.save"), 0)
    eq("gate: XY caps, Save writes exactly the 3 XYPan keys",
       keys_of(T, "gate.x.log"), XY_KEYS)
    eq("gate: XY caps, Save put count is 3", R.get("gate.x.puts"), 3)
    eq("gate: BACK_NONE validate -> PS_E_BACKEND (1)",
       R.get("gate.none.validate"), 1)
    eq("gate: BACK_NONE save -> PS_E_BACKEND (1)", R.get("gate.none.save"), 1)
    eq("gate: VERT with caps 0 save -> PS_E_BACKEND (1)",
       R.get("gate.zero.save"), 1)
    eq("gate: XY readback 0 has no PS_CAP_MODE", R.get("gate.x0.hasMode"), 0)
    eq("gate: XY readback 0, mode 1 ignored by validate",
       R.get("gate.x0.validateMode1"), 0)
    eq("gate: XY readback 0, mode 2 ignored by validate (not exposed)",
       R.get("gate.x0.validateMode2"), 0)
    eq("gate: XY readback 0, Save returns PS_OK", R.get("gate.x0.save"), 0)
    eq("gate: XY readback 0, Save writes exactly the 3 XYPan keys",
       keys_of(T, "gate.x0.log"), XY_KEYS)
    eq("gate: XY readback 0, no mode key ever saved",
       any("mode" in k.lower() for k in keys_of(T, "gate.x0.log")), False)
    eq("gate: XY readback 1 has PS_CAP_MODE", R.get("gate.x1.hasMode"), 1)
    eq("gate: VERT caps have no MODE/EDGEON/REPEAT/FOLLOWD (readback 1)",
       R.get("gate.v.badcaps"), 0)
    eq("gate: VERT caps have no MODE/EDGEON/REPEAT/FOLLOWD (readback 0)",
       R.get("gate.v0.badcaps"), 0)
    eq("gate: VERT caps offer STEP|EDGE|DWELL|FOLLOW",
       R.get("gate.v.goodcaps"), 0x0F)
    eq("gate: XY caps have no STEP/EDGE/DWELL/FOLLOW",
       R.get("gate.x.badcaps"), 0)
    eq("gate: XY caps offer EDGEON|REPEAT|FOLLOWD",
       R.get("gate.x.goodcaps"), 0x70)
    eq("gate: XY readback 0 offers EDGEON|REPEAT|FOLLOWD",
       R.get("gate.x0.goodcaps"), 0x70)

    # Persistence.
    eq("round trip VERT: Save returns PS_OK", R.get("rt.v.save"), 0)
    eq("round trip VERT: Save writes exactly XTPan Step/Dwell/Edge/Follow",
       keys_of(T, "rt.v.log"), VERT_KEYS)
    eq("round trip VERT: put count 4", R.get("rt.v.puts"), 4)
    eq("round trip VERT: Load step 120", R.get("rt.v.step"), 120)
    eq("round trip VERT: Load dwell 700", R.get("rt.v.dwell"), 700)
    eq("round trip VERT: Load edge 5", R.get("rt.v.edge"), 5)
    eq("round trip VERT: Load follow 0", R.get("rt.v.follow"), 0)
    eq("round trip XY: Save returns PS_OK", R.get("rt.x.save"), 0)
    eq("round trip XY: Save writes exactly XYPan EdgeOn/RepeatMs/FollowDlg",
       keys_of(T, "rt.x.log"), XY_KEYS)
    eq("round trip XY: put count 3", R.get("rt.x.puts"), 3)
    eq("round trip XY: Load edgeOn 1", R.get("rt.x.edgeOn"), 1)
    eq("round trip XY: Load repeat 200", R.get("rt.x.repeat"), 200)
    eq("round trip XY: Load followDlg 1", R.get("rt.x.followDlg"), 1)
    eq("round trip XY: mode is never loaded (stays 0)",
       R.get("rt.x.mode"), 0)
    for name in ("rt.v.log", "rt.x.log"):
        keys = keys_of(T, name)
        bad = sorted(k for k in keys
                     if k.split(".", 1)[1] in FORBIDDEN_KEYS
                     or "mode" in k.lower())
        eq(f"{name}: no Enabled/KeyMods/KeyDown/KeyUp/KeyTop/LogKeys/"
           "LogFile/mode key", bad, [])
    eq("save of invalid settings: PS_E_STEP (2)", R.get("save.invalid.rc"), 2)
    eq("save of invalid settings: writes nothing",
       R.get("save.invalid.puts"), 0)
    eq("failing put: Save returns PS_E_STORE (11)", R.get("save.fail.rc"), 11)
    eq("clamp: stored VERT Step 3 loads as 8", R.get("clamp.v.step"), 8)
    eq("clamp: stored VERT Edge 0 loads as 1", R.get("clamp.v.edge"), 1)
    eq("clamp: stored VERT Follow 7 loads as 1", R.get("clamp.v.follow"), 1)
    eq("clamp: stored XY RepeatMs 150 loads as 100",
       R.get("clamp.x.repeat"), 100)
    eq("clamp: stored XY EdgeOn 5 loads as default 0",
       R.get("clamp.x.edgeOn"), 0)
    eq("load never sets mode (stored XYPan Mode 1 ignored)",
       R.get("load.x.mode"), 0)
    eq("load never reads a mode key",
       any("mode" in k.lower()
           for k in T.get("load.x.getlog", "").split()), False)

    # Dialog model.
    eq("open: work equals live", R.get("open.workEqLive"), 1)
    eq("cancel: work equals live again", R.get("cancel.workEqLive"), 1)
    eq("cancel: no apply calls", R.get("cancel.apply"), 0)
    eq("cancel: no puts", R.get("cancel.puts"), 0)
    eq("apply invalid: returns PS_E_STEP (2)", R.get("apply.invalid.rc"), 2)
    eq("apply invalid: no apply calls", R.get("apply.invalid.apply"), 0)
    eq("apply invalid: no puts", R.get("apply.invalid.puts"), 0)
    eq("apply invalid: live unchanged", R.get("apply.invalid.liveSame"), 1)
    eq("apply invalid: status set", R.get("apply.invalid.statusSet"), 1)
    eq("apply engine refusal: returns PS_E_APPLY (12)",
       R.get("apply.enginefail.rc"), 12)
    eq("apply engine refusal: no puts", R.get("apply.enginefail.puts"), 0)
    eq("apply engine refusal: live unchanged",
       R.get("apply.enginefail.liveSame"), 1)
    eq("apply PS_E_LOST: returns PS_E_LOST (13)", R.get("apply.lost.rc"), 13)
    eq("apply PS_E_LOST: caps.backend becomes NONE (0)",
       R.get("apply.lost.backend"), 0)
    eq("apply PS_E_LOST: no puts", R.get("apply.lost.puts"), 0)
    eq("apply PS_E_LOST: live unchanged", R.get("apply.lost.liveSame"), 1)
    eq("apply ok: returns PS_OK", R.get("apply.ok.rc"), 0)
    eq("apply ok: apply called exactly once", R.get("apply.ok.calls"), 1)
    eq("apply ok: apply received the validated work",
       R.get("apply.ok.wantIsWork"), 1)
    eq("apply ok: no puts before apply", R.get("apply.ok.putsAtApply"), 0)
    eq("apply ok: 4 puts after apply", R.get("apply.ok.puts"), 4)
    eq("apply ok: live equals what the engine reports",
       R.get("apply.ok.liveEqActual"), 1)
    eq("apply ok: live step 120", R.get("apply.ok.liveStep"), 120)
    eq("apply ok: differs 0", R.get("apply.ok.differs"), 0)
    eq("apply ok: store Step 120", R.get("apply.ok.storeStep"), 120)
    eq("apply ok: store Dwell 500", R.get("apply.ok.storeDwell"), 500)
    eq("apply ok: store Edge 4", R.get("apply.ok.storeEdge"), 4)
    eq("apply ok: store FollowActive 0", R.get("apply.ok.storeFollow"), 0)
    eq("hardware refused: returns PS_OK", R.get("hw.refused.rc"), 0)
    eq("hardware refused: differs 1", R.get("hw.refused.differs"), 1)
    eq("hardware refused: live mode 0", R.get("hw.refused.liveMode"), 0)
    eq("hardware refused: mode 1 was requested", R.get("hw.refused.wantMode"),
       1)
    eq("hardware refused: status shows the engine note",
       "HW REFUSED" in T.get("hw.refused.status", ""), True)
    eq("hardware refused: mode never saved",
       any("mode" in k.lower()
           for k in T.get("hw.refused.log", "").split()), False)
    eq("hardware granted: returns PS_OK", R.get("hw.granted.rc"), 0)
    eq("hardware granted: differs 0", R.get("hw.granted.differs"), 0)
    eq("hardware granted: live mode 1", R.get("hw.granted.liveMode"), 1)
    eq("save failure after apply: returns PS_E_STORE (11)",
       R.get("apply.savefail.rc"), 11)
    eq("save failure after apply: live updated",
       R.get("apply.savefail.liveStep"), 90)
    eq("home: returns PS_OK", R.get("home.rc"), 0)
    eq("home: calls home once", R.get("home.calls"), 1)
    eq("home: re-queries the driver once", R.get("home.queryDelta"), 1)
    eq("home: viewport origin re-read (0)", R.get("home.viewX"), 0)
    eq("home: typed work values kept", R.get("home.workKept"), 1)
    eq("home failure: returns PS_E_APPLY (12)", R.get("home.fail.rc"), 12)

    # Routing decision tables.
    cmd_rows = [("''", 0), ("NULL", 0), ("'OFF'", 1), ("'off'", 1),
                ("'Off'", 1), ("'SETTINGS'", 2), ("'settings'", 2),
                ("'/SETTINGS'", 2), ("'/settings'", 2), ("' OFF'", 0),
                ("'OFFX'", 0), ("'x'", 0), ("'SETTINGS now'", 0)]
    for i, (src, want) in enumerate(cmd_rows):
        eq(f"PanCmdParse({src}) = {want}", R.get(f"cmd.{i}"), want)
    route_rows = [("10", 0, "POST"), ("11", 0, "POST"), ("01", 1, "START"),
                  ("00", 2, "OFF")]
    for key, want, name in route_rows:
        eq(f"PanRoute(running={key[0]}, enabled={key[1]}) = {name}",
           R.get("route." + key), want)
    own_rows = [("00", 0, "RUN"), ("01", 0, "RUN"), ("11", 1, "FORWARD"),
                ("10", 2, "EXIT")]
    for key, want, name in own_rows:
        eq(f"PanOwnerStart(other={key[0]}, settings={key[1]}) = {name}",
           R.get("own." + key), want)
    for n in range(14):
        expect(f"PanSetErrorText({n}) is non-empty", R.get(f"errtext.{n}") == 1)


# ----------------------------------------------------------- source checks

def sync_checks():
    loader = importlib.machinery.SourceFileLoader(
        "buildapp", str(REPO / "src/softpan/BUILDAPP.PY"))
    mod = loader.load_module()
    raw = (REPO / "src/xtpan/XTPAN.C").read_bytes().decode("latin-1")
    lf = raw.replace("\r\n", "\n")
    expect("XTPAN.C: anchor appears exactly once", lf.count(ANCHOR) == 1)
    block = (ANCHOR.split("\n")[0] + "\n    " + COMMENT +
             "\n    if (PanEscape(-1) < 0)\n        return;\n    Keys();")
    for label, src in (("CRLF as read", raw), ("LF form", lf)):
        out = mod.sync_helper(src)
        expect(f"sync_helper ({label}): guard comment exactly once",
               out.count(COMMENT) == 1)
        expect(f"sync_helper ({label}): PanEscape(-1) guard between "
               "'DWORD now' and 'Keys();'", out.count(block) == 1)
    for label, src in (("anchor removed", lf.replace(ANCHOR, "")),
                       ("anchor duplicated", lf + "\n" + ANCHOR + "\n")):
        try:
            mod.sync_helper(src)
            raised = False
        except ValueError:
            raised = True
        expect(f"sync_helper: {label} raises ValueError", raised)


def hostpan_check():
    if shutil.which("cc") is None:
        skip("python src/xtpan/HOSTPAN.PY: cc not on PATH")
        return
    r = subprocess.run([sys.executable, str(REPO / "src/xtpan/HOSTPAN.PY")],
                       cwd=str(REPO), capture_output=True, text=True,
                       timeout=900)
    expect("src/xtpan/HOSTPAN.PY exits 0 (FollowTop still found in XTPAN.C)",
           r.returncode == 0)
    if r.returncode:
        print(r.stdout[-2000:] + r.stderr[-2000:])


def source_order_checks():
    pc = text_of(REPO / "src/softpan/PANCFG.C")
    expect("PANCFG.C: PanCmdParse before first GetProfileString and "
           "WriteProfileString",
           first_before(pc, "PanCmdParse", "GetProfileString") and
           first_before(pc, "PanCmdParse", "WriteProfileString"))
    i = pc.find("PS_CMD_SETTINGS")
    expect("PANCFG.C: SETTINGS branch present", i >= 0)
    region = ""
    if i >= 0:
        j = pc.find("return", i)
        region = pc[i:j] if j >= 0 else pc[i:]
    expect("PANCFG.C: SETTINGS branch does not WriteProfileString",
           "WriteProfileString" not in region)
    code = re.sub(r"/\*.*?\*/", "", region, flags=re.S)
    expect("PANCFG.C: SETTINGS branch does not load (no 'load' in code, "
           "comments ignored)", "load" not in code.lower())
    for n in range(1, 7):
        expect(f"PANCFG.C: 'return {n};' still present",
               ("return %d;" % n) in pc)
    expect('PANCFG.C: "XTPan","Enabled" literal present',
           '"XTPan","Enabled"' in pc)
    expect('PANCFG.C: FindWindow("XTPan" literal present',
           'FindWindow("XTPan"' in pc)
    expect('PANCFG.C: SETTINGS also reaches a running XYCTL '
           '(XYOverviewControl + PS_MSG_XY before PanRoute)',
           first_before(pc, 'XYOverviewControl', 'PanRoute') and
           first_before(pc, 'PS_MSG_XY', 'PanRoute'))

    xc = text_of(REPO / "experiments/XYOVERVIEW/XYCTL.C")
    m = xc.find("int PASCAL WinMain")
    expect("XYCTL.C: WinMain found", m >= 0)
    w = xc[m:] if m >= 0 else ""
    po = w.find("PanOwnerStart")
    expect("XYCTL.C: PanOwnerStart in WinMain", po >= 0)
    for lit, pat in (("GetDC(", r"GetDC\("),
                     ("Escape(", r"(?<![A-Za-z_])Escape\("),
                     ("RegisterClass", r"RegisterClass")):
        mm = re.search(pat, w)
        j = mm.start() if mm else -1
        expect(f"XYCTL.C WinMain: PanOwnerStart before first {lit}",
               po >= 0 and (j < 0 or po < j))

    xt = text_of(REPO / "src/xtpan/XTPAN.C")
    m = xt.find("int PASCAL WinMain")
    expect("XTPAN.C: WinMain found", m >= 0)
    w = xt[m:] if m >= 0 else ""
    po = w.find("PanOwnerStart")
    pe = w.find('GetProfileInt("XTPan", "Enabled"')
    expect('XTPAN.C WinMain: PanOwnerStart before GetProfileInt("XTPan", '
           '"Enabled"', 0 <= po and pe >= 0 and po < pe)
    expect("XTPAN.C WinMain: no 'if (hPrev)' early exit left",
           re.search(r"if\s*\(\s*hPrev\s*\)", w) is None)
    gm = w.find("while (GetMessage")
    tm = w.find("TranslateMessage", gm) if gm >= 0 else -1
    pd = w.find("PanDlgMessage", gm) if gm >= 0 else -1
    expect("XTPAN.C: PanDlgMessage in GetMessage loop before TranslateMessage",
           gm >= 0 and pd >= 0 and (tm < 0 or pd < tm))


def dialog_checks():
    dp = REPO / "src/panui/PANDLG.C"
    if not dp.exists():
        skip("src/panui/PANDLG.C missing: dialog source checks skipped")
        skip("src/panui/PANDLG.C missing: mode-2 offer scan skipped")
        return
    dl = text_of(dp)
    for api in ("SetTimer", "SetWindowsHookEx", "SetWindowsHook", "WinExec"):
        expect(f"PANDLG.C: no {api}", api not in dl)
    expect('PANDLG.C: class "PanSetDlg" present', '"PanSetDlg"' in dl)
    expect('PANDLG.C: class is not "XTPan" or "XYOverviewControl"',
           '"XTPan"' not in dl and '"XYOverviewControl"' not in dl)
    i = dl.find("PanDlgOpen")
    expect("PANDLG.C: PanDlgOpen has an already-open check (IsWindow)",
           i >= 0 and "IsWindow" in dl)
    modes = set(re.findall(r"PS_MODE_(\w+)", dl))
    expect("PANDLG.C: only PS_MODE_SOFT and PS_MODE_HARD are offered",
           modes <= {"SOFT", "HARD"})
    expect("PANDLG.C: no 'mode = 2' literal",
           re.search(r"mode\s*=\s*2", dl, re.I) is None)


# -------------------------------------------------------------------- lint

def has_line_comment(text):
    """True when a '//' starts outside a string or character literal."""
    for line in text.split("\n"):
        i, quote = 0, None
        while i < len(line):
            c = line[i]
            if quote:
                if c == "\\":
                    i += 2
                    continue
                if c == quote:
                    quote = None
            elif c in "\"'":
                quote = c
            elif line.startswith("//", i):
                return True
            i += 1
    return False


def lint_file(rel, crlf_only, panui, comments):
    p = REPO / rel
    if not p.exists():
        skip(f"lint {rel}: missing")
        return
    data = p.read_bytes()
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    expect(f"{rel}: line endings all-CRLF or all-LF", not (crlf and lf))
    if crlf_only:
        expect(f"{rel}: all-CRLF (--crlf)", crlf > 0 and lf == 0)
    expect(f"{rel}: ends with a newline", data.endswith(b"\n"))
    expect(f"{rel}: no tab characters", b"\t" not in data)
    text = data.decode("latin-1").replace("\r\n", "\n")
    if comments:
        expect(f"{rel}: no // comment outside string literals",
               not has_line_comment(text))
    if panui:
        long_lines = [n for n, ln in enumerate(text.split("\n"), 1)
                      if len(ln) > 110]
        expect(f"{rel}: no line over 110 chars (first: {long_lines[:5]})",
               not long_lines)
        expect(f"{rel}: ASCII only", all(b < 128 for b in data))


def lint_checks(crlf_only):
    for rel in PANUI_LINT:
        lint_file(rel, crlf_only, True, rel not in ("src/panui/HOSTUI.PY"))
    for rel in OTHER_LINT:
        lint_file(rel, crlf_only, False, True)


# --------------------------------------------------------------- 16-bit gate

def wcc_checks(tmp):
    if not WCC.exists():
        skip(f"wcc: {WCC} absent, 16-bit compile gate skipped")
        return
    files = ["src/panui/PANSET.C", "src/panui/PANDLG.C", "src/xtpan/XTPAN.C",
             "src/softpan/PANCFG.C", "experiments/XYOVERVIEW/XYCTL.C"]
    for rel in files:
        p = REPO / rel
        if not p.exists():
            skip(f"wcc {rel}: missing")
            continue
        obj = Path(tmp) / (p.stem + "_wcc.obj")
        r = subprocess.run([str(WCC), "-zW", "-0", "-ms",
                            r"-IC:\WATCOM\H", r"-IC:\WATCOM\H\WIN",
                            "-I" + str(REPO / "src" / "panui"), f"-fo={obj}", str(p)],
                           cwd=str(tmp), capture_output=True, text=True)
        out = r.stdout + r.stderr
        errors = out.count("Error!")
        warns = out.count("Warning!")
        expect(f"wcc: {rel} compiles without errors",
               r.returncode == 0 and errors == 0)
        if rel.startswith("src/panui/"):
            expect(f"wcc: {rel} has no new warnings", warns == 0)
            if warns:
                print(out)
        else:
            print(f"     {rel}: {warns} warning(s) (pre-existing ones "
                  "accepted)")
    # The file softpan really builds is XTPAN.C after sync_helper().
    mod = importlib.machinery.SourceFileLoader(
        "buildapp_wcc", str(REPO / "src/softpan/BUILDAPP.PY")).load_module()
    synced = mod.sync_helper((REPO / "src/xtpan/XTPAN.C").read_text(encoding="latin-1"))
    sp = Path(tmp) / "XTPAN_SYNC.C"
    sp.write_text(synced, encoding="latin-1")
    r = subprocess.run([str(WCC), "-zW", "-0", "-ms",
                        r"-IC:\WATCOM\H", r"-IC:\WATCOM\H\WIN",
                        "-I" + str(REPO / "src" / "panui"),
                        "-fo=" + str(Path(tmp) / "XTPAN_SYNC.obj"), str(sp)],
                       cwd=str(tmp), capture_output=True, text=True)
    expect("wcc: sync_helper-transformed XTPAN.C compiles without errors",
           r.returncode == 0 and (r.stdout + r.stderr).count("Error!") == 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crlf", action="store_true",
                    help="require all-CRLF line endings")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        got = run_harness(tmp)
        if got:
            harness_checks(*got)
        sync_checks()
        hostpan_check()
        source_order_checks()
        dialog_checks()
        lint_checks(a.crlf)
        wcc_checks(tmp)
    if fails:
        print(f"HOSTUI: {len(fails)} failed")
        for f in fails:
            print("  - " + f)
        return 1
    print("HOSTUI: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
