"""Generate vectors and build the real-mode decoder DOS test executable."""

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WATCOM = Path(r"C:\WATCOM\BINNT")


def run(argv):
    print("+", " ".join(str(part) for part in argv), flush=True)
    subprocess.run([str(part) for part in argv], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overflow-events", type=int, default=65570)
    args = parser.parse_args()
    if not (WATCOM / "wasm.exe").is_file() or not (WATCOM / "wlink.exe").is_file():
        raise SystemExit(f"Open Watcom tools not found under {WATCOM}")

    run([sys.executable, "make_vectors.py", "--output", "VECTORS.BIN",
         "--overflow-events", str(args.overflow_events)])
    run([WATCOM / "wasm.exe", "decoder.asm"])
    run([WATCOM / "wasm.exe", "dostest.asm"])
    run([WATCOM / "wlink.exe", "system", "dos", "name", "DTEST.EXE",
         "file", "dostest.obj", "file", "decoder.obj"])
    print("Built DTEST.EXE (DOS 8.3 name) and VECTORS.BIN; build only, not executed.")


if __name__ == "__main__":
    main()
