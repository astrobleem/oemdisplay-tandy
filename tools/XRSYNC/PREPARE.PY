"""Prepare the XRSYNC OEM disk using your matching Windows 3.0 CGA grabber."""
import argparse
import importlib.util
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def media_module():
    path = HERE / "XRMEDIA.PY"
    if not path.exists():
        path = HERE.parent / "XR1PACK" / "PREPARE.PY"
    loader = SourceFileLoader("xrmedia", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def prepare(windows, payload, output, manifest=None):
    media = media_module()
    spec = manifest or json.loads((HERE / "INPUTS.JSN").read_bytes())
    if spec["schema"] != 1 or spec["profile"] != "XRSYNC":
        raise media.Refused("Unsupported OEM preparation manifest")
    inputs = media.Inputs({"windows": windows, "components": payload})
    target = output.resolve()
    if target.exists():
        raise media.Refused("Output must be a new directory")
    for root in inputs.roots.values():
        if media.inside(target, root) or media.inside(root, target):
            raise media.Refused("Input and output directories must be separate")
    files = {}
    for name, pin in spec["payload"].items():
        media.safe_relative(name)
        files[name] = inputs.read("components", name, pin)
    files["CGA.GR2"] = inputs.read("windows", "CGA.GR2", spec["grabber"])
    target.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (target / name).write_bytes(data)
        media.exact((target / name).read_bytes(), media.identity(data), name)
    result = {"schema": 1, "status": "PASS_XRSYNC_OEM_PREPARATION",
              "files": {n: media.identity(d) for n, d in sorted(files.items())},
              "contains_owned_windows_bytes": True,
              "redistributable_output": False, "CF_access": False}
    (target / "SHA256.JSN").write_bytes(
        (json.dumps(result, indent=2) + "\n").replace("\n", "\r\n").encode("ascii"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windows-media", required=True, type=Path,
                        help="Flat matching media folder or owned WINDOWS/SYSTEM folder")
    parser.add_argument("--payload", default=HERE / "PAYLOAD", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.windows_media, args.payload, args.out)
        print(result["status"] + ": " + str(args.out))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, "Refused: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
