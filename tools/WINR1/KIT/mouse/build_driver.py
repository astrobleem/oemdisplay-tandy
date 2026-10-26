"""Build the standalone NE wheel-driver candidate and record checksums."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

from check_candidate_image import inspect_image
from verify_linked_ds import verify_ne

ROOT = Path(__file__).resolve().parent
WATCOM = Path(os.environ.get("WATCOM_BIN", r"C:\WATCOM\BINNT"))
SOURCES = ("driver.asm", "decoder.asm", "timestamp.asm", "WHEEL.LNK", "LICENSE",
           "README.md", "API13.md", "PROVENANCE.md",
           "check_candidate_image.py", "verify_linked_ds.py")
DECODER_SHA256 = "dd1635f38e9c2b4e90b099412d201874ce0dab226a87030cd85944cd6478add9"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                          timeout=45)
    record = {"command": command, "returncode": proc.returncode,
              "stdout": proc.stdout, "stderr": proc.stderr}
    if proc.returncode or "Warning!" in proc.stdout + proc.stderr:
        raise RuntimeError(json.dumps(record, indent=2))
    return record


def main():
    assert sha256(ROOT / "decoder.asm") == DECODER_SHA256, "decoder hash mismatch"
    records = [
        run([str(WATCOM / "wasm.exe"), "driver.asm"]),
        run([str(WATCOM / "wasm.exe"), "decoder.asm"]),
        run([str(WATCOM / "wasm.exe"), "timestamp.asm"]),
        run([str(WATCOM / "wlink.exe"), "@WHEEL.LNK"]),
    ]
    binary = inspect_image((ROOT / "WHEEL.DRV").read_bytes())
    ds = verify_ne(ROOT)
    report = {
        "status": "PASS_NE_BUILD_STATIC_CHECKS_ONLY",
        "wheel_drv_sha256": sha256(ROOT / "WHEEL.DRV"),
        "decoder_sha256": DECODER_SHA256,
        "sources": {name: sha256(ROOT / name) for name in SOURCES},
        "tool_sha256": {Path(record["command"][0]).name:
                        sha256(Path(record["command"][0])) for record in records},
        "commands": records,
        "ne_export_check": binary,
        "linked_ne_ds_check": ds,
        "map_sha256": sha256(ROOT / "WHEEL.MAP"),
        "guest_execution": "not run",
    }
    (ROOT / "BUILD.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("status", "wheel_drv_sha256", "decoder_sha256",
                       "linked_ne_ds_check", "map_sha256", "guest_execution")},
                     indent=2))


if __name__ == "__main__":
    main()
