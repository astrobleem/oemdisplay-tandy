#!/usr/bin/env python3
"""Mutation check for T40TEST: every listed one-line change to T40PRES.ASM
must make T40TEST.PY fail, or the test is not sensitive to that rule.

A mutant counts as caught only when T40TEST built and ran it and its
comparison with the model found a difference: exit code 1 and a RESULT.JSN
with verdict FAIL. A build or tool failure (exit 3) or a harness failure
(exit 4, emulator or timeout) is "invalid", never "caught", and fails the
whole check. Before the mutants, the unmutated presenter must pass, and a
deliberately unassemblable control must come back invalid (proving that the
classification works).

  python3 src/txt40/T40MUT.PY --deps <inputs> --dosbox <dosbox-x> --out <fresh-dir>
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (name, exact original line, replacement); the first occurrence is changed.
# Not listed, because no test can tell them apart: changes that make the
# presenter re-verify MORE cells (a wider touch test, a verify range beyond
# the output range). With every pixel change flushed, which T40TEST.PY
# enforces for its scenes, re-verifying a cell whose kept state is current
# gives the same state.
MUTANTS = [
    ("light-shade-threshold", "    cmp ax,2", "    cmp ax,1"),
    ("half-block-count", "    cmp di,36", "    cmp di,27"),
    ("box-junction-table", "    db 0C4h,0BFh,0D9h,0B4h,0C4h,0C2h,0C1h,0C5h",
     "    db 0C4h,0BFh,0D9h,0C3h,0C4h,0C2h,0C1h,0C5h"),
    ("right-edge-mask", "    sub ax,T40_W-8", "    sub ax,T40_W-9"),
    ("claim-window-rows", "    cmp ax,8\r\n    jae tcf_skip", "    cmp ax,7\r\n    jae tcf_skip"),
    ("background-tie-order", "    jbe tc_bg_next", "    jb tc_bg_next"),
    ("foreground-tie-order", "    jbe tc_fg_next", "    jb tc_fg_next"),
    ("two-colour-tie", "    ja tw_a_bg", "    jae tw_a_bg"),
    ("two-colour-third", "    jz tw_two", "    jmp tw_two"),
    ("box-down-edge", "    cmp t40_rl,7", "    cmp t40_rl,6"),
    ("thin-line-stray", "    jle tp_thin", "    jl tp_thin"),
    ("half-block-tolerance", "    ja tp_density", "    jae tp_density"),
    ("hint-bottom-edge", "    cmp bx,T40_H-4", "    cmp bx,T40_H-5"),
    ("blit-row-order", "    jle tb_rdir", "    jmp tb_rdir"),
    ("blit-inside-test", "    jg tbo_done\r\n    mov bx,word ptr t40_snap[di+2]",
     "    jge tbo_done\r\n    mov bx,word ptr t40_snap[di+2]"),
    ("same-place-replace", "    je ta_write                 ; same place: the newer replaces", "    jmp short ta_push"),
    ("no-second-check", "    mov t40_rows,07Eh", "    mov t40_rows,0"),
    ("second-check-any-glyph", "    or al,[si+10]\r\n    jz tvf_fail", "    or al,[si+10]\r\n    jmp short $+2"),
    ("stale-after-add", "    or t40_vst[bx],80h          ; next flush whose output range holds it",
     "    or t40_vst[bx],00h"),
    ("touch-never", "    stc\r\n    ret\r\ntch_no:", "    clc\r\n    ret\r\ntch_no:"),
    ("touch-narrow-window", "    cmp ax,t40_px1\r\n    jge tch_no\r\n    add ax,8", "    cmp ax,t40_px1\r\n    jge tch_no\r\n    add ax,7"),
    ("touch-short-window", "    cmp ax,t40_py1\r\n    jge tch_no\r\n    add ax,8", "    cmp ax,t40_py1\r\n    jge tch_no\r\n    add ax,7"),
    ("underline-row", "    cmp byte ptr [si+11],0\r\n    jne tv_normal",
     "    cmp byte ptr [si+11],1\r\n    jne tv_normal"),
    ("second-slot", "    add di,4\r\n    call t40_unpack\r\n    cmp byte ptr [si+13],0",
     "    add di,8\r\n    call t40_unpack\r\n    cmp byte ptr [si+13],0"),
    # compact hints (TEXT80): unpacking and the glyph dictionary
    ("unpack-x-off-by-one", "    sub ax,4\r\n    mov cl,dl\r\n    and cl,7", "    sub ax,3\r\n    mov cl,dl\r\n    and cl,7"),
    ("unpack-y-uses-dx", "    shr cl,1\r\n    shr cl,1\r\n    shr cl,1\r\n    and cl,7", "    nop\r\n    shr cl,1\r\n    shr cl,1\r\n    and cl,7"),
    ("gfind-half-compare", "    mov cx,8\r\ntgf_cmp:", "    mov cx,4\r\ntgf_cmp:"),
    ("gfind-never-full", "    cmp t40_gcnt,T40_GLIMIT", "    cmp t40_gcnt,0FFFFh"),
    ("add-push-keeps-older", "    mov ax,[di+2]\r\n    mov [di+6],ax", "    mov ax,[di+6]\r\n    mov [di+6],ax"),
    ("output-margin-top", "    sub ax,1\r\n    jge tpr_r0", "    sub ax,0\r\n    jge tpr_r0"),
    ("output-margin-left", "    sub si,1\r\n    jge tpr_c0", "    sub si,0\r\n    jge tpr_c0"),
    ("output-margin-bottom", "    add bx,1\r\n    cmp bx,T40_NROWS-1\r\n    jle tpr_r1",
     "    add bx,0\r\n    cmp bx,T40_NROWS-1\r\n    jle tpr_r1"),
    # snapshot-diff flushes (TEXT80)
    ("diff-ignores-stale", "    test t40_vst[bx],80h\r\n    jz tpd_cmp", "    test t40_vst[bx],00h\r\n    jz tpd_cmp"),
    ("diff-never-changed", "    jnc tpd_no\r\n    jmp tpd_yes", "    jmp tpd_no\r\n    jmp tpd_yes"),
    ("diff-skips-plane-3", "    cmp al,es:[di+3*T40_COLS]", "    cmp al,al"),
    ("diff-first-row-only", "    loop tch2_row", "    nop"),
    ("diff-run-half-rows", "    add bx,8\r\n    mov cx,t40_drun", "    add bx,4\r\n    mov cx,t40_drun"),
    ("diff-no-left-margin", "    sub si,1\r\n    jge tpd_c0", "    sub si,0\r\n    jge tpd_c0"),
    ("diff-any-rectangle", "    je tpd_go", "    jmp short tpd_go"),
    ("diff-ignores-rect-rows", "    cmp ax,t40_sy0\r\n    jne tpd_full", "    cmp ax,ax\r\n    jne tpd_full"),
    ("diff-snapshot-columns", "    sub dx,cx\r\n    mov t40_snc,dx", "    sub dx,cx\r\n    mov t40_snc,cx"),
]


CONTROL_BROKEN = ("control-unassemblable", "    cmp ax,2", "    cmp ax,t40_no_such_symbol")


def classify(rc, out):
    res = out / "RESULT.JSN"
    if rc == 0:
        return "survived"
    if rc == 1 and res.exists() and json.loads(res.read_text()).get("verdict") == "FAIL":
        return "caught"
    return "invalid"


def run_test(a, out, name, asm=None):
    cmd = [sys.executable, str(HERE / "T40TEST.PY"), "--deps", str(a.deps), "--dosbox", str(a.dosbox),
           "--out", str(out / name), "--scenes", str(a.scenes), "--cols", str(a.cols),
           "--glimit", str(a.glimit)]
    if asm:
        cmd += ["--pres", str(asm)]
    rc = subprocess.run(cmd, capture_output=True, text=True).returncode
    return rc, classify(rc, out / name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deps", type=Path, required=True)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--scenes", type=int, default=12)
    ap.add_argument("--cols", type=int, default=40, choices=(40, 80))
    ap.add_argument("--glimit", type=int, default=64,
                    help="glyph dictionary limit for the tests (64: the scenes overflow it)")
    a = ap.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    src = (HERE / "T40PRES.ASM").read_bytes().decode("ascii")
    base_rc, base = run_test(a, out, "unmutated")
    print("unmutated", base)
    controls = {"unmutated": {"test_exit": base_rc, "class": base, "want": "survived"}}
    name, old, new = CONTROL_BROKEN
    mut = out / f"{name}.ASM"
    mut.write_bytes(src.replace(old + "\r\n", new + "\r\n", 1).encode("ascii"))
    rc, cls = run_test(a, out, name, mut)
    print(name, cls)
    controls[name] = {"test_exit": rc, "class": cls, "want": "invalid"}
    results = []
    for name, old, new in MUTANTS:
        old_t, new_t = old + "\r\n", new + "\r\n"
        if old_t not in src:
            raise SystemExit(f"T40MUT: {name}: original text not found")
        mut = out / f"{name}.ASM"
        mut.write_bytes(src.replace(old_t, new_t, 1).encode("ascii"))
        rc, cls = run_test(a, out, name, mut)
        results.append({"mutant": name, "test_exit": rc, "class": cls, "killed": cls == "caught"})
        print(name, cls)
    survived = [r["mutant"] for r in results if r["class"] == "survived"]
    invalid = [r["mutant"] for r in results if r["class"] == "invalid"]
    controls_ok = all(c["class"] == c["want"] for c in controls.values())
    summary = {"mutants": len(results), "killed": sum(r["killed"] for r in results),
               "survived": survived, "invalid": invalid, "controls": controls,
               "verdict": "PASS" if not survived and not invalid and controls_ok else "FAIL"}
    (out / "RESULT.JSN").write_text(json.dumps({"summary": summary, "results": results}, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0 if summary["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
