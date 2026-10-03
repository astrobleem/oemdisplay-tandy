#!/usr/bin/env python3
"""Verify the exact GUI-tested V1 and its resource structure."""
from pathlib import Path
import hashlib, runpy, sys
HERE = Path(__file__).resolve().parent
p = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "bin/TANDYV1.DRV"
data = p.read_bytes()
assert len(data) == 46288, "Wrong driver size"
assert hashlib.sha256(data).hexdigest() == "995d0079278a42254d997684fb51bd4285bd19bedc2e32cca3bf5065d3cfc61a", "Wrong driver hash"
helpers = runpy.run_path(str(HERE / "PACKRES.PY"))
assert len(helpers["inspect_ne"](data)) == 74, "Wrong resource count"
print("PASS: exact GUI-tested V1, 46288 bytes, 74 resources")
