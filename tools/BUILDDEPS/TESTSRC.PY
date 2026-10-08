#!/usr/bin/env python3
"""Verify five TR5 source pipelines in an external view; no guest execution."""
import argparse
import hashlib
import importlib.machinery
import json
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", type=Path, required=True)
    args = parser.parse_args()
    repo = args.view.resolve()
    source = repo / "src/tandysw"
    modules = {}
    for name in ("build", "PORT8086", "PORTDIB", "MODEPROF", "REPCOPY88",
                 "BYTECOL", "CURKEEP", "OUTROWS", "WIDESCAN"):
        suffix = ".py" if name == "build" else ".PY"
        modules[name] = importlib.machinery.SourceFileLoader(
            "external_" + name, str(source / (name + suffix))).load_module()
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
            results.append(mode)
    print(json.dumps({"status": "PASS", "modes": results,
                      "scope": "exact dependency/source pins and staged TR5 assembly; no native build or runtime claim"}, indent=2))


if __name__ == "__main__":
    main()
