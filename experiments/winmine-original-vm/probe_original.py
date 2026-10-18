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
from win16_host import InitTaskRegisters, UnsupportedImport, Win16Host


class ProbeError(RuntimeError):
    """The original entrypoint did not fit the explicitly bounded probe."""


def _reference_entry_state(initial_ss: int, initial_sp: int, initial_cs: int,
                           initial_ip: int, task: InitTaskRegisters) -> dict[str, Any]:
    """Hand-calculated state for entry, modeled InitTask, and guest continuation."""
    pushed_bp_sp = (initial_sp - 2) & 0xFFFF
    sentinel_sp = (pushed_bp_sp - 2) & 0xFFFF
    call_ip_slot = (sentinel_sp - 2) & 0xFFFF
    return_ip = (initial_ip + 8) & 0xFFFF  # 2-byte XOR + 1-byte PUSH + 5-byte CALL FAR
    return {
        "AX": 1,
        "BX": task.command_tail_offset,
        "CX": task.stack_limit,
        "DX": task.show_command,
        "SP": sentinel_sp,
        "BP": 0,
        "SI": task.previous_instance,
        "DI": task.instance,
        "CS": initial_cs,
        "DS": 0,
        "ES": task.psp_segment,
        "SS": initial_ss,
        "IP": (return_ip + 4) & 0xFFFF,  # OR AX,AX; JE is not taken on success.
        "stack_words": {
            pushed_bp_sp: 0,
            sentinel_sp: 0,
            call_ip_slot: return_ip,
        },
        # OR AX,AX after InitTask returns AX=1. AF is undefined on 8086.
        "defined_flags": {"CF": 0, "PF": 0, "ZF": 0, "SF": 0, "OF": 0},
    }


def run_probe(image_bytes: bytes, expected_sha256: str, *,
              task_registers: InitTaskRegisters | None = None) -> dict[str, Any]:
    """Execute the bounded entry / KERNEL#91 / guest-return slice."""
    before = hashlib.sha256(image_bytes).hexdigest()
    if before.lower() != expected_sha256.lower():
        raise ProbeError(f"input SHA-256 mismatch: got {before}")

    loaded = NELoader.from_bytes(image_bytes, "WINMINE-original.EXE").load()
    task = task_registers or InitTaskRegisters()
    cpu = CPU(memory=loaded.memory)
    cpu.CS, cpu.IP = loaded.initial_cs, loaded.initial_ip
    cpu.SS, cpu.SP = loaded.initial_ss, loaded.initial_sp
    host = Win16Host(loaded, task)

    # Stop exactly after the first imported call returns, then validate the
    # two guest instructions that consume InitTask's success result.
    cpu.run(3, import_handler=host.dispatch_import)
    if len(host.calls) != 1:
        raise ProbeError(f"expected one bound far import; observed {len(host.calls)}")
    expected_guest_return = (loaded.initial_ip + 8) & 0xFFFF
    if (cpu.CS, cpu.IP) != (loaded.initial_cs, expected_guest_return):
        raise ProbeError("InitTask host service did not return to the guest call site")
    continuation = bytes(cpu.read8(cpu.CS, expected_guest_return + i) for i in range(4))
    if continuation[:3] != bytes.fromhex("09 C0 74"):
        raise ProbeError(
            "entry continuation is outside the bounded OR AX,AX / JE return slice"
        )
    cpu.run(2)  # Original guest OR AX,AX; JE short (success falls through).
    if cpu.IP != (expected_guest_return + 4) & 0xFFFF:
        raise ProbeError("guest did not follow the modeled InitTask success return")

    reference = _reference_entry_state(
        loaded.initial_ss, loaded.initial_sp, loaded.initial_cs, loaded.initial_ip, task
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
        "import": {"module": host.calls[0].module, "kind": host.calls[0].kind,
                   "ordinal": host.calls[0].ordinal, "name": host.calls[0].name},
        "host_service": "KERNEL ordinal 91 InitTask register-return subset",
        "guest_return": {"CS": f"{cpu.CS:04X}", "IP": f"{cpu.IP:04X}",
                         "post_import_instructions": 2, "success_branch_taken": False},
        "task_register_context": {
            "AX": "0001", "BX": f"{task.command_tail_offset & 0xFFFF:04X}",
            "CX": f"{task.stack_limit & 0xFFFF:04X}",
            "DX": f"{task.show_command & 0xFFFF:04X}",
            "SI": f"{task.previous_instance & 0xFFFF:04X}",
            "DI": f"{task.instance & 0xFFFF:04X}",
            "ES": f"{task.psp_segment & 0xFFFF:04X}",
        },
        "task_stack_sentinel": {"SS": f"{cpu.SS:04X}", "SP": f"{cpu.SP:04X}", "word": "0000"},
        "final": {key: f"{value:04X}" for key, value in state.items()},
        "reference_match": True,
        "input_bytes_unchanged": True,
        "qualification": (
            "host-only one-import bridge slice; InitTask register outputs use an explicit "
            "synthetic launch context; no Windows task/heap/PSP allocation, broader startup, "
            "full-app, release, or hardware qualification"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="read-only path to a caller-supplied NE executable")
    parser.add_argument("--sha256", required=True, help="pinned SHA-256 required before any probe runs")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error("image path is not a regular file")
    before = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if before.lower() != args.sha256.lower():
        parser.error(f"input SHA-256 mismatch: got {before}")
    result = run_probe(args.image.read_bytes(), args.sha256)
    after = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if after != before:
        raise ProbeError("input file changed while the probe was running")
    result["input_file_unchanged"] = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NELoadError, ProbeError, UnsupportedOpcode, UnsupportedImport) as exc:
        print(f"probe failed closed: {exc}", file=sys.stderr)
        raise SystemExit(2)

