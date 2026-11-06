"""Opt-in private HPXY Output/text bounds over the unchanged XR/DIB pipeline."""
from pathlib import Path
import argparse
import importlib.machinery
import json
import sys

ROOT = Path(__file__).resolve().parents[2]


def build(xr, dib, bounds):
    """Apply XR, then DIB, then the exact-source bounds; restore the loader."""
    if any(arg.split("=", 1)[0] in ("--batch", "--sync-output")
           for arg in sys.argv[1:]):
        raise ValueError("Bounds use the original XY cursor path; omit --sync-output/--batch")
    original_load = importlib.machinery.SourceFileLoader.load_module
    applied = []

    def load(loader, *args, **kwargs):
        module = original_load(loader, *args, **kwargs)
        if loader.name == "xypatch":
            original_patch = module.patch

            def patch(renderer, **options):
                if options.get("batch") or applied:
                    raise ValueError("Expected one non-batched HPXY source stage")
                original_patch(renderer, **options)
                dib.patch(renderer)
                applied.append(bounds.port(renderer))

            module.patch = patch
        return module

    importlib.machinery.SourceFileLoader.load_module = load
    try:
        xr.main()
    finally:
        importlib.machinery.SourceFileLoader.load_module = original_load
    if len(applied) != 1:
        raise RuntimeError("HPXY bounds were not applied exactly once")
    return applied[0]


def main():
    # An older source checkout can explicitly select the current XY overlays
    # without replacing its existing PAN files. The final source pin is strict.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--overlay-root", type=Path, default=ROOT)
    options, remaining = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + remaining
    overlay = options.overlay_root.resolve()
    # Load the Windows native driver only when actually building, so source
    # checks can import this module without an emulator or Windows host.
    loader = importlib.machinery.SourceFileLoader
    xr = loader("hpb_xr", str(overlay / "experiments/XYRRECT/XRBUILD.PY")).load_module()
    dib = loader("hpb_dib", str(ROOT / "src/hpxydib/DIB.PY")).load_module()
    bounds = loader("hpb_bounds", str(ROOT / "src/hpxydib/HPBOUNDS.PY")).load_module()
    result = build(xr, dib, bounds)
    out = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
    path = out / "RESULT.json"
    report = json.loads(path.read_text())
    report.update(candidate="PRIVATE HPXY synchronous Output/text columns",
                  runtime="NOT_TESTED_BY_BUILD", bounds=result,
                  presentation="Original XY copier, cursor ownership and pan",
                  accepted_runtime_replaced=False)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
