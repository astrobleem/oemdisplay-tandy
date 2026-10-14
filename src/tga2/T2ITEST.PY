"""Selector safety and native evidence regression checks; no emulator or media."""
import importlib.machinery
import json
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
I = importlib.machinery.SourceFileLoader("t2inf", str(HERE / "T2INF.PY")).load_module()


def main():
    raw = (HERE / "OEMSETUP.INF").read_bytes()
    assert I.verify(raw)["label"] == I.LABEL
    cases = {
        "missing experimental warning": raw.replace(b"EXPERIMENTAL TANDY", b"TANDY"),
        "broader family": raw.replace(b"SL/2 FAMILY ONLY", b"SL/TL/RL FAMILY"),
        "description too long": raw.replace(I.LABEL.encode(), (I.LABEL + " v2").encode()),
        "foreign driver": raw.replace(b"a:TNDYV2.DRV", b"a:TANDY88.DRV"),
        "wrong geometry": raw.replace(b"200,96,48", b"133,96,72"),
        "relative source path": raw.replace(b"C:\\T2EXP", b"."),
        "LF-only INF": raw.replace(b"\r\n", b"\n"),
        "duplicate display": raw + b"\r\n[display]\r\n",
        "Windows 3.1": raw.replace(b'Version = "3.0"', b'Version = "3.1"'),
    }
    for label, bad in cases.items():
        try:
            I.verify(bad)
        except ValueError:
            print("ok   rejects " + label)
        else:
            raise AssertionError("Accepted " + label)
    data = (HERE / "T2MODES.ASM").read_bytes()
    assert data.count(b"\n") == data.count(b"\r\n") == 122
    report = json.loads((HERE.parents[1] / "docs/tga2/T2SETUP.JSN").read_bytes())
    assert report["status"] == "PASS" and report["selector"] == I.LABEL
    assert report["Setup"]["returned_to_DOS"] and report["Setup"]["exact_full_label_written"]
    launch = report["post_Setup_SL2"]
    assert launch["PASS"] and not launch["owned_process_remaining"] and launch["owned_VM_closed"]
    for name in ("T2FIRST.LOG", "T2SECOND.LOG"):
        assert "PASS=1" in launch["guest_results"][name]
        assert "VRAM_RED_PATTERN_128_BYTES=1" in launch["guest_results"][name]
    assert not report["physical_hardware_qualified"] and not report["Windows31_qualified"]
    assert report["Setup"]["INF_sha256"] == hashlib.sha256(raw).hexdigest()
    staging = json.loads((HERE.parents[1] / "docs/tga2/T2STAGE.JSN").read_bytes())
    assert staging["status"] == "PASS" and staging["successful_stage_files"] == 6
    assert staging["missing_source_copies"] == 0 and staging["pre_existing_target_unchanged"]
    assert staging["PREPINF_sha256"] == hashlib.sha256((HERE / "PREPINF.BAT").read_bytes()).hexdigest()
    assert staging["T2MODES_binary_unchanged"] and staging["T2MODES_sha256"] == "f875b99be4df98097668b7b5b76d5521f47c22f50db91a402a9b4d589c81157a"
    print("T2ITEST: PASS (valid selector, 9 refusal cases, CRLF source and saved actual Setup/two-start evidence)")


if __name__ == "__main__":
    main()
