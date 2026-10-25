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
    assert report["Setup"]["INF_sha256"] == hashlib.sha256((HERE / "HISTORY/OEMR2.INF").read_bytes()).hexdigest()
    staging = json.loads((HERE.parents[1] / "docs/tga2/T2STAGE.JSN").read_bytes())
    assert staging["status"] == "PASS" and staging["successful_stage_files"] == 6
    assert staging["missing_source_copies"] == 0 and staging["pre_existing_target_unchanged"]
    assert staging["PREPINF_sha256"] == hashlib.sha256((HERE / "HISTORY/PREPR2.BAT").read_bytes()).hexdigest()
    assert staging["T2MODES_binary_unchanged"] and staging["T2MODES_sha256"] == "f875b99be4df98097668b7b5b76d5521f47c22f50db91a402a9b4d589c81157a"
    current = json.loads((HERE.parents[1] / "docs/tga2/T2SUP.JSN").read_bytes())
    assert current["status"] == "PASS_NATIVE_SETUP_SUPPORT"
    native = current["native"]
    assert native["complete"] and native["setup_returned"]
    assert native["owned_stopped"] and native["lease_released"]
    assert native["desktop_mode"] == 10 and native["desktop_settle_seconds"] == 40
    assert native["selected_boot"] == {"286grabber": "CGA.GR2", "fixedfon.fon": "XTCFIX.FON",
        "oemfonts.fon": "XTCOEM.FON", "fonts.fon": "XTCSYS.FON", "display.drv": "TNDYV2.DRV"}
    assert native["startup_logo_in_wincom"] == {"XTSTATIC.LGO": True, "WXTSPL01.RLE": True}
    assert current["external_driver_support_inputs"] == []
    assert current["source_fixture"]["unchanged_after_test"]
    for name, pin in current["integration_sources"].items():
        snapshot = {"src/tga2/T2PACK.PY": "PACKSUP1.PY",
                    "src/tga2/INSTALL.TXT": "INSSUP1.TXT",
                    "src/tga2/PREPINF.BAT": "PRPSUP1.BAT"}.get(name)
        value = (HERE / "HISTORY" / snapshot if snapshot else HERE.parents[1] / name).read_bytes()
        assert pin == {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}, name
    capture = current["capture"]
    value = (HERE.parents[1] / capture["path"]).read_bytes()
    assert capture["bytes"] == len(value) and capture["sha256"] == hashlib.sha256(value).hexdigest()
    assert not current["physical_hardware_qualified"] and not current["Windows31_qualified"]
    automatic = json.loads((HERE.parents[1] / "docs/tga2/T2LAUNCH.JSN").read_bytes())
    assert automatic["status"] == "PASS_NATIVE_AUTOMATIC_ENTRIES"
    assert automatic["native"]["complete"] and automatic["refusal"]["complete"]
    assert automatic["native"]["reservation_before_setup"]["resident_id"] == "TNDYV2R1"
    assert automatic["native"]["desktop_mode"] == 10
    assert automatic["native"]["desktop_settle_seconds"] == 40
    assert automatic["refusal"]["both_entries_returned"] and automatic["refusal"]["windows_unchanged"]
    assert automatic["harness"]["manual_T2RESV_calls"] == 0
    assert automatic["source_fixture_unchanged"]
    for result in (automatic["native"], automatic["refusal"]):
        assert result["owned_stopped"] and result["lease_released"]
    for name, pin in automatic["integration_sources"].items():
        relocation = automatic.get("source_relocations", {}).get(name)
        if relocation:
            assert relocation["native_snapshot"] == pin, name
            pin = relocation["current_source"]
        value = (HERE.parents[1] / name).read_bytes()
        assert pin == {"bytes":len(value),"sha256":hashlib.sha256(value).hexdigest()},name
    value = (HERE.parents[1] / "downloads/experimental/TGA2/TNDYV2.ZIP").read_bytes()
    assert automatic["packet"] == {"bytes":len(value),"sha256":hashlib.sha256(value).hexdigest()}
    capture = automatic["capture"]
    value = (HERE.parents[1] / capture["path"]).read_bytes()
    assert capture["bytes"] == len(value) and capture["sha256"] == hashlib.sha256(value).hexdigest()
    print("T2ITEST: PASS (current support/native receipt; historical source bindings; selector refusals)")


if __name__ == "__main__":
    main()
