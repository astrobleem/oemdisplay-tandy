#!/usr/bin/env python3
"""Focused BYTECOL staging tests; not a Windows/runtime acceptance test."""
from pathlib import Path
import argparse, hashlib, importlib.machinery, json, tempfile

HERE = Path(__file__).resolve().parent
col = importlib.machinery.SourceFileLoader("bytecol_test", str(HERE/"BYTECOL.PY")).load_module()
DIRS = {"320x200x16": "build32016", "640x200x4": "build6404",
        "160x200x16": "build16016", "320x200x4": "build3204", "640x200x2": "build6402"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        cases.append({"case": name, "result": "PASS"})
    with tempfile.TemporaryDirectory(prefix="bytecol-tests-") as tmp:
        for mode, dirname in DIRS.items():
            renderer = Path(tmp)/dirname
            (renderer/"EGA").mkdir(parents=True)
            source = args.baseline/dirname/"renderer/EGA/TSOFT.ASM"
            target = renderer/"EGA/TSOFT.ASM"
            target.write_bytes(source.read_bytes())
            old = col.normalized(target)
            sentinel = renderer/"UNCHANGED.INC"
            sentinel.write_bytes(b"unchanged\r\n")
            audit = col.port(renderer, mode)
            text = col.normalized(target)
            check(mode+" exact input pin", col.sha(old) == col.EXPECTED[mode])
            check(mode+" output report", col.sha(text) == audit["output_normalized_sha256"])
            check(mode+" CRLF", b"\n" not in target.read_bytes().replace(b"\r\n", b""))
            check(mode+" only staged TSOFT", sentinel.read_bytes() == b"unchanged\r\n")
            old_flush = old[old.index("public FlushShadow,FlushRows"):old.index("FlushShadow endp")+len("FlushShadow endp")]
            check(mode+" full-width source unchanged", old_flush in text)
            # Remove the only three allowed changes; require exact remainder.
            restored = text.replace(col.helper(old, mode), "")
            for begin, end in (("cProc TBitBlt,", "cProc TOutput,"), ("cProc TPixel,", "cProc TScanLR,")):
                i,j = restored.index(begin), restored.index(end)
                a,b = old.index(begin), old.index(end)
                restored = restored[:i] + old[a:b] + restored[j:]
            check(mode+" unrelated source unchanged", restored == old)
            check(mode+" no new CLI", not any(line.split(";",1)[0].strip().lower()=="cli" for line in col.helper(old,mode).splitlines()))
            original_bytes = target.read_bytes()
            try:
                col.port(renderer, mode)
            except RuntimeError:
                pass
            else:
                raise AssertionError("second application accepted")
            check(mode+" double application rejected before write", target.read_bytes() == original_bytes)
            target.write_bytes(source.read_bytes()+b"; unexpected source\r\n")
            wrong = target.read_bytes()
            try:
                col.port(renderer, mode)
            except RuntimeError:
                pass
            else:
                raise AssertionError("changed pinned input accepted")
            check(mode+" wrong pin rejected before write", target.read_bytes() == wrong)
    report = {"result": "PASS", "case_count": len(cases), "cases": cases,
              "scope": "Exact-pinned source transformation, independent full-width/unrelated preservation, CRLF and fail-closed behavior; not runtime correctness or speed"}
    args.out.write_bytes((json.dumps(report,indent=2)+"\n").replace("\n","\r\n").encode())
    print(json.dumps({"result": "PASS", "case_count": len(cases)}))


if __name__ == "__main__":
    main()
