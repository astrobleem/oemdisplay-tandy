"""Build the DIB-only candidate; the earlier solid predicate is not applied."""
from pathlib import Path
import hashlib
import importlib.machinery
import json
import sys

HERE = Path(__file__).resolve().parent
xr = importlib.machinery.SourceFileLoader(
    "dib_xr", str(HERE.parent / "XYRRECT/XRBUILD.PY")).load_module()
dib = importlib.machinery.SourceFileLoader("dib_unroll", str(HERE / "DIB.PY")).load_module()
load = importlib.machinery.SourceFileLoader.load_module


def patched(self, *args, **kwargs):
    module = load(self, *args, **kwargs)
    if self.name == "xypatch":
        original = module.patch

        def apply(renderer, **kw):
            original(renderer, **kw)
            dib.patch(renderer)

        module.patch = apply
    return module


importlib.machinery.SourceFileLoader.load_module = patched
xr.main()
out = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
p = out / "RESULT.json"
r = json.loads(p.read_text())
r.update(candidate="PRIVATE HPXY fixed-group DIB unroll", runtime="NOT_TESTED_BY_BUILD",
         dib_overlay_sha256=hashlib.sha256((HERE / "DIB.PY").read_bytes()).hexdigest(),
         source_base="c40e380e13b6e7cc6201b1958c580fd287cf4374",
         presentation="Unchanged released converter; no solid predicate",
         accepted_runtime_replaced=False)
p.write_text(json.dumps(r, indent=2) + "\n")
print(json.dumps(r))
