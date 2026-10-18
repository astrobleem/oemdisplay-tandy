"""Run a bounded, read-only WinMine original-entry probe on the host.

This command reads a caller-supplied NE file, loads only its NE segments and
known fixups, executes at most three original instructions, and traps the first
far imported call. It does not write or patch the input image. The import stub
returns a chosen AX value; it does not implement Windows or the imported API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cpu_subset import CPU, UnsupportedOpcode
from ne_loader import ImportTarget, NELoadError, NELoader


class ProbeError(RuntimeError):
    """The original entrypoint did not fit the explicitly bounded probe."""


def _reference_entry_state(initial_ss: int, initial_sp: int, initial_cs: int,
                           initial_ip: int, return_ax: int) -> dict[str, Any]:
    """Independent expected state for XOR BP,BP; PUSH BP; CALL FAR; RETF.

    This is a hand-calculated trace for the exact three-instruction prefix and
    a synthetic far-import return. It is not another general x86 interpreter.
    """
    pushed_bp_sp = (initial_sp - 2) & 0xFFFF
    call_cs_slot = (pushed_bp_sp - 2) & 0xFFFF
    call_ip_slot = (call_cs_slot - 2) & 0xFFFF
    return_ip = (initial_ip + 8) & 0xFFFF  # 2-byte XOR + 1-byte PUSH + 5-byte CALL FAR
    return {
        "AX": return_ax & 0xFFFF,
        "BX": 0,
        "CX": 0,
        "DX": 0,
        "SP": pushed_bp_sp,
        "BP": 0,
        "SI": 0,
        "DI": 0,
        "CS": initial_cs,
        "DS": 0,
        "ES": 0,
        "SS": initial_ss,
        "IP": return_ip,
        "stack_words": {
            pushed_bp_sp: 0,
            call_cs_slot: initial_cs,
            call_ip_slot: return_ip,
        },
        # XOR's defined flags for zero XOR zero. AF is undefined on 8086 and
        # intentionally excluded from the comparison.
        "defined_flags": {"CF": 0, "PF": 1, "ZF": 1, "SF": 0, "OF": 0},
    }


def run_probe(image_bytes: bytes, expected_sha256: str, *, return_ax: int = 0) -> dict[str, Any]:
    """Execute a bounded first-entry block and compare it to a separate trace."""
    before = hashlib.sha256(image_bytes).hexdigest()
    if before.lower() != expected_sha256.lower():
        raise ProbeError(f"input SHA-256 mismatch: got {before}")

    loaded = NELoader.from_bytes(image_bytes, "WINMINE-original.EXE").load()
    cpu = CPU(memory=loaded.memory)
    cpu.CS, cpu.IP = loaded.initial_cs, loaded.initial_ip
    cpu.SS, cpu.SP = loaded.initial_ss, loaded.initial_sp
    calls: list[ImportTarget] = []

    def intercept(cpu_state: CPU, selector: int, offset: int) -> None:
        target = loaded.resolve_import(selector, offset)
        calls.append(target)
        # A deterministic synthetic return only. No Windows API side effects
        # are claimed or modeled by this probe.
        cpu_state.AX = return_ax

    cpu.run(3, import_handler=intercept)
    if len(calls) != 1:
        raise ProbeError(f"expected one intercepted far import; observed {len(calls)}")

    reference = _reference_entry_state(
        loaded.initial_ss, loaded.initial_sp, loaded.initial_cs, loaded.initial_ip, return_ax
    )
    state = {name: getattr(cpu, name) for name in (
        "AX", "BX", "CX", "DX", "SP", "BP", "SI", "DI", "CS", "DS", "ES", "SS", "IP"
    )}
    for name, value in reference.items():
        if name in state and state[name] != value:
            raise ProbeError(f"CPU/reference mismatch for {name}: {state[name]:04X} != {value:04X}")
    for offset, value in reference["stack_words"].items():
        actual = cpu.read16(cpu.SS, offset)
        if actual != value:
            raise ProbeError(f"CPU/reference stack mismatch at SS:{offset:04X}: {actual:04X} != {value:04X}")
    flags = {name: int(cpu.flag(name)) for name in reference["defined_flags"]}
    if flags != reference["defined_flags"]:
        raise ProbeError(f"CPU/reference flag mismatch: {flags!r}")

    after = hashlib.sha256(image_bytes).hexdigest()
    if after != before:
        raise ProbeError("immutable input bytes changed during probe")

    return {
        "input_sha256": before,
        "input_bytes": len(image_bytes),
        "loaded_segment_bytes": loaded.loaded_bytes,
        "segment_selectors": {str(key): f"{value:04X}" for key, value in loaded.segment_selectors.items()},
        "initial": {"CS": f"{loaded.initial_cs:04X}", "IP": f"{loaded.initial_ip:04X}",
                    "SS": f"{loaded.initial_ss:04X}", "SP": f"{loaded.initial_sp:04X}"},
        "import": {"module": calls[0].module, "kind": calls[0].kind,
                   "ordinal": calls[0].ordinal, "name": calls[0].name},
        "synthetic_return_ax": f"{return_ax & 0xFFFF:04X}",
        "final": {key: f"{value:04X}" for key, value in state.items()},
        "reference_match": True,
        "input_bytes_unchanged": True,
        "qualification": "host-only three-instruction entry probe; no Windows API behavior or full-app support",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="read-only path to a caller-supplied NE executable")
    parser.add_argument("--sha256", required=True, help="pinned SHA-256 required before any probe runs")
    parser.add_argument("--return-ax", type=lambda value: int(value, 0), default=0,
                        help="synthetic intercepted-import return value (default: 0)")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error("image path is not a regular file")
    before = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if before.lower() != args.sha256.lower():
        parser.error(f"input SHA-256 mismatch: got {before}")
    result = run_probe(args.image.read_bytes(), args.sha256, return_ax=args.return_ax)
    after = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if after != before:
        raise ProbeError("input file changed while the probe was running")
    result["input_file_unchanged"] = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NELoadError, ProbeError, UnsupportedOpcode) as exc:
        print(f"probe failed closed: {exc}", file=sys.stderr)
        raise SystemExit(2)

