"""Opt-in bounds: --fixed uses the pinned TR5 builder; default uses HPXY."""
from pathlib import Path
import argparse
import importlib.machinery
import importlib.util
import hashlib
import types
import json
import sys

ROOT = Path(__file__).resolve().parents[2]


FIXED_SOURCE_SHA256 = "5a6938d6b86758ccf34bea7c67efb10713477929c2e49f100900b789ed271a55"
FIXED_ANCHOR = b"    wide_audit = wide_module.port(renderer, args.mode)\r\n"
FIXED_INSERT = b"    _fixed_bounds(renderer, args.mode)\r\n"


def adapt_fixed(source):
    """Add one callback to the exact historical builder, only in memory."""
    if hashlib.sha256(source).hexdigest() != FIXED_SOURCE_SHA256:
        raise ValueError("Fixed bounds require the exact historical BUILD88 source")
    if source.count(FIXED_ANCHOR) != 1 or FIXED_INSERT in source:
        raise ValueError("Fixed builder anchor mismatch")
    result = source.replace(FIXED_ANCHOR, FIXED_ANCHOR + FIXED_INSERT)
    if result.replace(FIXED_INSERT, b"") != source:
        raise ValueError("Fixed adaptation changed historical builder bytes")
    return result


def _load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixed_builder(path=None, bounds_source=None):
    """Load isolated fixed staging without changing the frozen BUILD88 file."""
    path = Path(path or ROOT / "src/tandysw/BUILD88.PY").resolve()
    bounds_source = Path(bounds_source or ROOT / "src/tandysw").resolve()
    adapted = adapt_fixed(path.read_bytes())
    baseline = _load_module("hpb_fixed_base", path.with_name("build.py"))
    output = _load_module("hpb_fixed_output", bounds_source / "OUTPUTBOUNDS.PY")
    text = _load_module("hpb_fixed_text", bounds_source / "TEXTBOUNDS.PY")
    applied = []

    def apply(renderer, mode):
        if applied:
            raise ValueError("Expected one fixed bounds source stage")
        output_audit = output.port(renderer, mode)
        text_audit = text.port(renderer, mode)
        applied.append({"output_bounds": output_audit, "text_bounds": text_audit})

    module = types.ModuleType("hpb_fixed_builder")
    module.__file__ = str(path)
    module._fixed_bounds = apply
    module.fixed_stages = applied
    missing = object()
    previous = sys.modules.get("build", missing)
    old_path = sys.path[:]
    try:
        # The historical import must not reuse another checkout's build.py.
        sys.modules["build"] = baseline
        sys.path.insert(0, str(path.parent))
        exec(compile(adapted, str(path), "exec"), module.__dict__)
    finally:
        sys.path[:] = old_path
        if previous is missing:
            sys.modules.pop("build", None)
        else:
            sys.modules["build"] = previous
    return module


def output_path(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--out", type=Path, required=True)
    options, unused = parser.parse_known_args(argv)
    return options.out.resolve() / "RESULT.json"


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
    # The original builder remains pinned for historical hardware proofs.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--fixed", action="store_true")
    parser.add_argument("--overlay-root", type=Path, default=ROOT)
    options, remaining = parser.parse_known_args()
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0]] + remaining
    try:
        if options.fixed:
            # Route before importing Windows-only XRBUILD/msvcrt.
            builder = fixed_builder()
            builder.main()
            if len(builder.fixed_stages) != 1:
                raise RuntimeError("Fixed bounds were not applied exactly once")
            path = output_path(remaining)
            report = json.loads(path.read_text())
            report.update(builder.fixed_stages[0])
            report.update(candidate="PRIVATE fixed-profile Output/text columns",
                          runtime="NOT_TESTED_BY_BUILD", accepted_runtime_replaced=False)
        else:
            overlay = options.overlay_root.resolve()
            loader = importlib.machinery.SourceFileLoader
            xr = loader("hpb_xr", str(overlay / "experiments/XYRRECT/XRBUILD.PY")).load_module()
            dib = loader("hpb_dib", str(ROOT / "src/hpxydib/DIB.PY")).load_module()
            bounds = loader("hpb_bounds", str(ROOT / "src/hpxydib/HPBOUNDS.PY")).load_module()
            result = build(xr, dib, bounds)
            path = output_path(sys.argv[1:])
            report = json.loads(path.read_text())
            report.update(candidate="PRIVATE HPXY synchronous Output/text columns",
                          runtime="NOT_TESTED_BY_BUILD", bounds=result,
                          presentation="Original XY copier, cursor ownership and pan",
                          accepted_runtime_replaced=False)
        path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()
