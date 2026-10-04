#!/usr/bin/env python3
"""Focused fail-closed source and emitted-prefix audit regression tests.

No emulator is invoked. This is not an 8088 hardware/interrupt proof.
Usage: python TSTREP88.PY --original-listings <recovered build/EGA>
"""
from pathlib import Path
import argparse, importlib.machinery, json, shutil, tempfile

HERE = Path(__file__).resolve().parent
rep = importlib.machinery.SourceFileLoader("test_repcopy88", str(HERE/"REPCOPY88.PY")).load_module()


def row(address, code, source):
    return f" {address:04X}  {code:<25}{source}\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-listings", type=Path)
    parser.add_argument("--staged-profiles", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    cases = {
        "inline_rep_es": (row(0,"F3/ 26: A4","rep movs byte ptr es:[di],es:[si]"), False),
        "inline_cs_rep": (row(0,"2E: F3/ A5","rep movs word ptr es:[di],cs:[si]"), False),
        "rep_then_es": (row(0,"F3/","rep")+row(1,"26: A4","movs byte ptr es:[di],es:[si]"), False),
        "es_then_rep": (row(0,"26:","rep")+row(1,"F3/ A4","rep movsb"), False),
        "two_standalone": (row(0,"F3/","rep")+row(1,"26:","rep")+row(2,"A4","movsb"), False),
        "rep_lock": (row(0,"F3/ F0/ A5","rep movsw"), False),
        "single_rep": (row(0,"F3/ A5","rep movsw"), True),
        "split_single_rep": (row(0,"F3/","rep")+row(1,"A5","movsw"), True),
        "single_segment": (row(0,"26: A4","movs byte ptr es:[di],es:[si]"), True),
        "rep_like_immediate": (row(0,"B9 F326","mov cx,0f326h")+row(3,"F3/ A5","rep movsw"), True),
        "rep_like_data": (row(0,"F3 26 A4","template db 0f3h,026h,0a4h"), True),
        "dangling_prefix": (row(0,"F3/","rep"), False),
        "prefix_gap": (row(0,"F3/","rep")+row(2,"A4","movsb"), False),
    }
    results = {}
    with tempfile.TemporaryDirectory(prefix="repcopy88-") as temp:
        temp = Path(temp)
        for name,(source,expected) in cases.items():
            path=temp/(name+".LST"); rep.write_dos(path,source)
            try:
                rep.audit_listings([path], require_replacements=False)
                passed=True
            except AssertionError:
                passed=False
            if passed != expected:
                raise AssertionError("Audit regression failed: " + name)
            results[name]="PASS"
        # Exact replacement byte guard: an altered JCXZ displacement must fail.
        for displacement, expected in (("04",True),("03",False)):
            path=temp/"copy.LST"
            source=(row(0,"E3 "+displacement,"jcxz rc88_test_1_done")+
                    row(2,"26: A4","movs byte ptr es:[di],es:[si]")+
                    row(4,"E2 FC","loop rc88_test_1_copy"))
            rep.write_dos(path,source)
            try:
                rep.audit_listings([path], require_replacements=False)
                passed=True
            except AssertionError:
                passed=False
            if passed != expected:
                raise AssertionError("Replacement-byte regression failed")
            results["replacement_jcxz_"+displacement]="PASS"
        if args.staged_profiles:
            for mode in rep.EXPECTED:
                source=args.staged_profiles/mode/"renderer"
                stage=temp/mode;stage.mkdir()
                for name in (*rep.COUNTS,"GENCONST.INC"):
                    shutil.copyfile(source/name,stage/name)
                audit=rep.port(stage,mode)
                if audit["source_site_count"] != 11:
                    raise AssertionError("Source replacement count")
                for name in rep.COUNTS:
                    data=(stage/name).read_bytes()
                    if b"\n" in data.replace(b"\r\n",b""):
                        raise AssertionError("Non-CRLF output: " + name)
                snapshot={p.name:p.read_bytes() for p in stage.iterdir()}
                try:
                    rep.port(stage,mode)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Reapplication must fail closed")
                if snapshot != {p.name:p.read_bytes() for p in stage.iterdir()}:
                    raise AssertionError("Failed pass changed stage")
                # Independently alter an original pinned file; the whole stage
                # must stay unchanged when pre-write input validation rejects it.
                for name in (*rep.COUNTS,"GENCONST.INC"):
                    shutil.copyfile(source/name,stage/name)
                with (stage/"BMC_ITE.ASM").open("ab") as stream:
                    stream.write(b"; unaudited change\r\n")
                snapshot={p.name:p.read_bytes() for p in stage.iterdir()}
                try:
                    rep.port(stage,mode)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Changed pinned input must fail closed")
                if snapshot != {p.name:p.read_bytes() for p in stage.iterdir()}:
                    raise AssertionError("Pin failure partially changed stage")
                results["staged_profile_"+mode]="PASS"
    original = None
    if args.original_listings:
        try:
            rep.audit_listings(sorted(args.original_listings.glob("*.LST")), require_replacements=False)
        except AssertionError as error:
            original=json.loads(str(error))
            counts={name:sum(item["file"]==name for item in original["multi_prefix_rep"]) for name in rep.COMPILED_COUNTS}
            if counts != rep.COMPILED_COUNTS or len(original["multi_prefix_rep"]) != 10:
                raise AssertionError("Unexpected original vulnerable-site counts")
            results["original_recovered_driver_rejected_at_10_sites"]="PASS"
        else:
            raise AssertionError("Original vulnerable driver passed the new audit")
    report={"status":"PASS", "tests":results,
            "original_multi_prefix_sites":None if original is None else original["multi_prefix_rep"],
            "scope":"Source/pin/CRLF and static listing-audit tests only; no execution or native interrupt claim"}
    if args.out:
        rep.write_dos(args.out,json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
