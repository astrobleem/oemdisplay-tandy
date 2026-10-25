"""Build a separate opt-in PCjr software panning candidate under the shared lease."""
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent


def load(name, path):
    return importlib.machinery.SourceFileLoader(name, str(path)).load_module()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True, help="current-source view with existing build dependencies")
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--adapter", choices=("pcjr", "colorplus"), default="pcjr")
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    if out.exists():
        raise SystemExit("Choose a fresh output directory")
    out.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repo / "src/tandysw"))
    b = load("sp_build88", repo / "src/tandysw/BUILD88.PY")
    patch = load("sp_patch", HERE / "SPPATCH.PY")
    runner = load("sp_runner", HERE / "WINRUN.PY").Runner(out.with_suffix(".LEASE.JSON"))
    state = {}
    prepare, run = b.baseline.prepare, b.bounded_run

    def stage(r, o):
        renderer, resources = prepare(r, o)
        state["ega"] = renderer / "EGA"
        return renderer, resources

    def assemble(command, env, path, timeout=120):
        if "edits" not in state:
            state["edits"] = {n: hashlib.sha256(t.encode("latin1")).hexdigest()
                              for n, t in patch.patch_staged(state["ega"], a.adapter).items()}
        return runner.run(command, env, path, min(timeout, 120))

    b.baseline.prepare, b.bounded_run = stage, assemble
    try:
        with runner.lease():
            sys.argv = ["BUILD88.PY", "--repo", str(repo), "--dosbox", str(a.dosbox.resolve()), "--out", str(out)]
            b.main()
    finally:
        b.baseline.prepare, b.bounded_run = prepare, run
    result = json.loads((out / "RESULT.json").read_text())
    assert result["build"] == "PASS"
    driver = out / ("JRPAN.DRV" if a.adapter == "pcjr" else "CPPAN.DRV")
    shutil.copyfile(out / "TANDY88.DRV", driver)
    summary = {"adapter": a.adapter, "driver": driver.name, "bytes": driver.stat().st_size,
               "sha256": hashlib.sha256(driver.read_bytes()).hexdigest(),
               "logical": [320, 400], "viewport": [320, 200], "pan_top": [0, 200],
               "shadow_bytes": 64000, "video_page_bytes": 32768,
               "new_shadow_bytes_vs_fixed": 32000, "hardware_panning": False,
               "staged_sha256": state["edits"], "runtime": "NOT_TESTED"}
    (out / "SPRESULT.JSON").write_bytes((json.dumps(summary, indent=2) + "\r\n").encode())
    # BUILD88's report describes the source profile before this compositor.
    # Preserve that detail explicitly and report the effective geometry here.
    result["base_mode"] = result.pop("mode")
    result["mode"] = summary
    result["candidate"] = a.adapter + " 320x400 software desktop / 320x200 viewport"
    (out / "RESULT.json").write_bytes((json.dumps(result, indent=2) + "\r\n").encode())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
