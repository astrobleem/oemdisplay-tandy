#!/usr/bin/env python3
"""Verify five TR5 source pipelines in an external view; no guest execution."""
import argparse
import hashlib
import importlib.machinery
import json
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", type=Path, required=True)
    parser.add_argument("--bounds-source", type=Path,
                        help="Optional staged directory containing the two bounds modules")
    args = parser.parse_args()
    repo = args.view.resolve()
    source = repo / "src/tandysw"
    modules = {}
    for name in ("build", "PORT8086", "PORTDIB", "MODEPROF", "REPCOPY88",
                 "BYTECOL", "CURKEEP", "OUTROWS", "WIDESCAN", "OUTPUTBOUNDS", "TEXTBOUNDS"):
        suffix = ".py" if name == "build" else ".PY"
        module_source = (args.bounds_source if args.bounds_source is not None and
                         name in ("OUTPUTBOUNDS", "TEXTBOUNDS") else source)
        modules[name] = importlib.machinery.SourceFileLoader(
            "external_" + name, str(module_source / (name + suffix))).load_module()
    # Exercise the real CLI staging gate without launching an emulator.
    # XY overlays depend on the default row-only 320-pixel stage.
    class StageReady(Exception):
        pass

    def stop_before_native(*args, **kwargs):
        raise StageReady()

    with patch.dict(sys.modules, {"build": modules["build"]}):
        builder = importlib.machinery.SourceFileLoader(
            "external_bounds_builder", str(source / "BUILD88.PY")).load_module()
    builder.bounded_run = stop_before_native

    def cli_stage(out, mode, all_modes):
        argv = ["BUILD88.PY", "--repo", str(repo), "--dosbox", "__not_run__",
                "--out", str(out), "--mode", mode]
        if all_modes:
            argv.append("--all-mode-bounds")
        with patch.object(sys, "argv", argv):
            try:
                builder.main()
            except StageReady:
                return (out / "renderer/EGA/TSOFT.ASM").read_bytes()
        raise AssertionError("CLI did not stop before native execution")

    baseline = json.loads((repo / "docs/TRIAL4/BUILDS.JSN").read_bytes())
    wanted = json.loads((repo / "docs/TRIAL5/BUILDS.JSN").read_bytes())
    for name, digest in baseline["source_files"].items():
        target = repo / name
        if name == "src/tandysw/BUILD88.PY":
            target = source / "BLDTR4.PY"
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name
    with tempfile.TemporaryDirectory(prefix="external-tr5-source-") as temp:
        results = []
        for mode, pin in baseline["profiles"].items():
            renderer, resources = modules["build"].prepare(repo, Path(temp) / mode)
            for name in ("PORT8086", "PORTDIB"):
                modules[name].port(renderer, repo)
            modules["MODEPROF"].port(renderer, resources, repo, mode)
            for name in ("REPCOPY88", "BYTECOL"):
                modules[name].port(renderer, mode)
            modules["CURKEEP"].port(renderer, mode, combined=True)
            modules["OUTROWS"].port(renderer, mode)
            # Canonical evidence keys use POSIX separators on every host.
            before = {p.relative_to(renderer).as_posix(): p.read_bytes()
                      for p in renderer.rglob("*") if p.is_file()}
            for name, digest in pin["staged_source_sha256"].items():
                assert hashlib.sha256(before["EGA/" + name]).hexdigest() == digest, name
            modules["WIDESCAN"].port(renderer, mode)
            for name, content in before.items():
                if name != "EGA/TSOFT.ASM":
                    assert (renderer / name).read_bytes() == content, name
            output = (renderer / "EGA/TSOFT.ASM").read_bytes()
            assert hashlib.sha256(output).hexdigest() == wanted["profiles"][mode]["staged_source_sha256"], mode
            assert b"\n" not in output.replace(b"\r\n", b""), mode
            bounds = modules["OUTPUTBOUNDS"]
            changed = bounds.port(renderer, mode)
            final = (renderer / "EGA/TSOFT.ASM").read_bytes()
            assert changed["changed"], mode
            assert final == bounds.transform(output, mode)
            assert changed["added_data_bytes"] == 0
            assert changed["extra_local_stack_bytes"] == 4
            assert changed["extra_flush_save_bytes"] == 4
            assert final.replace(bounds.NEW_GATE.encode("latin1"),
                                 bounds.OLD_GATE.encode("latin1")) == output
            for invalid in (b"", output + b"; changed\r\n", final):
                try:
                    bounds.transform(invalid, mode)
                except ValueError:
                    pass
                else:
                    raise AssertionError("Unknown or repeated Output stage accepted")
            for other in bounds.EXPECTED:
                if other != mode:
                    try:
                        bounds.transform(output, other)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Wrong-profile Output stage accepted")
            assert b"\n" not in final.replace(b"\r\n", b""), mode
            text_bounds = modules["TEXTBOUNDS"]
            checks = text_bounds.selftest(final, mode)
            assert checks["exact_inverse"]
            width = int(mode.split("x")[0])
            assert checks["clip_intervals_checked"] == (width + 1) * (width + 2) // 2
            text_changed = text_bounds.port(renderer, mode)
            text_final = (renderer / "EGA/TSOFT.ASM").read_bytes()
            assert text_changed["changed"], mode
            assert text_final == text_bounds.transform(final, mode)
            assert text_changed["added_data_bytes"] == 0
            assert text_changed["extra_local_stack_bytes"] == 4
            assert text_changed["extra_flush_save_bytes"] == 4
            for other in text_bounds.EXPECTED:
                if other != mode:
                    try:
                        text_bounds.transform(final, other)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Wrong-profile text stage accepted")
            for name, content in before.items():
                if name != "EGA/TSOFT.ASM":
                    assert (renderer / name).read_bytes() == content, name
            assert cli_stage(Path(temp) / (mode + "-default"), mode, False) == (
                text_final if mode == "640x200x4" else output), mode
            assert cli_stage(Path(temp) / (mode + "-all-bounds"), mode, True) == text_final, mode
            results.append(mode)
    print(json.dumps({"status": "PASS", "modes": results,
                      "scope": "exact dependency/source pins and staged TR5 assembly; no native build or runtime claim"}, indent=2))


if __name__ == "__main__":
    main()
