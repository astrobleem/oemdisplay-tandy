#!/usr/bin/env python3
"""Emit a hash-addressed removal proposal; never stage, delete or modify refs."""
import argparse
import importlib.machinery
import json
from pathlib import Path

deps = importlib.machinery.SourceFileLoader(
    "cleanup_deps", str(Path(__file__).with_name("DEPS.PY"))).load_module()

OBSOLETE = ("src/tandy16/", "src/tandy4/", "win2/", "tanvidasm/", "disk1/")
ROOT_LEGACY = {"BLDTNDY.BAT", "build_driver.bat", "BUILD.BAT", "dosbox-x.conf",
               "TNDY16.DRV", "TNDY16.MAP", "handoff.md", "task.md"}
ROOT_SOURCE = {"COMPAT.H", "DLLENTRY.C", "ENABLE.C", "STDBOOL.H", "STDINT.H",
               "STRING.H", "TGAVID.ASM", "TGAVID.H", "TNDY16.H", "WINDOWS.H",
               "WINDOWS.INC"}
LEGACY_IDLE = {
    "examples/TSHELL/IDLE/TESTS/HOSTTEST.C": "894b1ff599bf802c3162bfc2e8c3f48d0bd3a8af",
    "examples/TSHELL/IDLE/TESTS/VERIFY.PY": "0280d44693b2261764619056627c1ec2e04bfa0a",
    "examples/TSHELL/IDLE/TESTS/WINSTUB.H": "5d2a89506d8548b772221f86748767f83d76b27c",
}
EXTERNAL = ("BIN/", "DDK/", "INCLUDE/", "LIB/", "DOSBOX/", "DOSBox-X/")
KEEP = ("tools/FLASHDISK/", "distributions/WINXT/", "examples/", "docs/",
        "src/tandysw/", "src/tandyk3/", "src/splash/", "experiments/", "oemdisk/")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = deps.fresh_out(args.out, (args.repo,))
    rows = deps.tree(args.repo, args.commit)
    phases = {"obsolete-source": {}, "external-build-inputs": {}}
    for name, row in rows.items():
        if name in LEGACY_IDLE and row[2] != LEGACY_IDLE[name]:
            raise deps.Refusal("Historical idle-suite blob changed; re-review its role")
        if (name in ROOT_LEGACY or name in LEGACY_IDLE or name in {"src/" + n for n in ROOT_SOURCE} or
                any(name.startswith(p) for p in OBSOLETE)):
            phases["obsolete-source"][name] = row
        elif any(name.startswith(p) for p in EXTERNAL):
            phases["external-build-inputs"][name] = row
    plan = {"schema": 1, "source_commit": args.commit,
            "preservation": "DEV must preserve exact source_commit locally and remotely before cleanup merge",
            "execution": "proposal only; no deletion, staging or remote mutation",
            "keep_prefixes": list(KEEP),
            "keep_release_assets": ["TANDY88.ZIP", "TNDY16.ZIP", "existing remote tags/assets"],
            "case_collision_gate": "Archive the pinned older uppercase suite; retain unchanged lowercase Hold-capable suite; validate host runner on a case-sensitive filesystem",
            "phases": {}}
    for phase, selected in phases.items():
        if any(any(n.startswith(p) for p in KEEP) and n not in LEGACY_IDLE for n in selected):
            raise deps.Refusal("Proposal intersects current-source preservation roots")
        payload = deps.blobs(args.repo, selected)
        plan["phases"][phase] = {
            "files": {n: {"blob": selected[n][2], "bytes": len(b), "sha256": deps.sha(b)}
                      for n, b in sorted(payload.items())},
            "bytes": sum(map(len, payload.values())),
            "gates": (["preserved DEV snapshot", "update legacy/provenance links",
                       "final include closure for eleven root src stubs",
                       "current CI and package identities unchanged"] if phase == "obsolete-source"
                      else ["settled dependency lock", "external input integrity verification",
                            "all retained build entrypoints mapped to documented views",
                            "allocated native reproduction", "external emulator documentation"])}
    collisions = {}
    for name in rows:
        collisions.setdefault(name.casefold(), []).append(name)
    plan["case_collisions"] = [names for names in collisions.values() if len(names) > 1]
    plan["manual_followups"] = [
        "Rewrite stale CLAUDE.md to the current build instructions; do not delete guidance blindly",
        "Retain published experiment packets until supersession/source and public links are audited",
        "Archive/remove orphan dosfetch gitlink separately; preserve its exact Git commit identity",
        "DEV preserves both TSHELL test versions; main retains unchanged lowercase Hold-capable suite",
        "Regenerate this proposal after the installer owner settles main; re-review every changed blob"]
    out.write_bytes((json.dumps(plan, indent=2, sort_keys=True).replace("\n", "\r\n") + "\r\n").encode("ascii"))
    print(json.dumps({phase: {"files": len(x["files"]), "bytes": x["bytes"]}
                      for phase, x in plan["phases"].items()}, indent=2))


if __name__ == "__main__":
    main()
