"""Run a bounded, read-only WinMine original-entry probe on the host.

This command reads a caller-supplied NE file, loads only its NE segments and
known fixups, models the first imported InitTask call, and follows the guest
code through a narrow DOS3Call subset when explicit synthetic inputs are
provided. It does not write or patch the input image. The InitTask and DOS
contexts are synthetic; no Windows task or general DOS environment is
implemented.
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
from dos_context import DosContextError, SyntheticDosLaunchContext
from ne_loader import ImportTarget, NELoadError, NELoader
from win16_host import (
    InitTaskRegisters,
    SyntheticDosVersion,
    UnsupportedImport,
    Win16Host,
)


class ProbeError(RuntimeError):
    """The original entrypoint did not fit the explicitly bounded probe."""


def _trace_to_dependency(
    cpu: CPU,
    loaded: Any,
    instruction_limit: int,
    *,
    import_handler=None,
) -> dict[str, Any]:
    """Continue through the bounded DOS3Call slice to the next dependency."""
    if instruction_limit <= 0:
        raise ValueError("instruction_limit must be positive")
    code_selectors = set(loaded.segment_selectors.values())
    history: list[dict[str, str]] = []
    serviced_imports: list[dict[str, Any]] = []

    def state() -> dict[str, str]:
        return {name: f"{getattr(cpu, name):04X}" for name in (
            "CS", "IP", "SS", "SP", "AX", "BX", "CX", "DX", "SI", "DI",
            "BP", "DS", "ES"
        )} | {"FLAGS": f"{cpu.flags:04X}"}

    def bytes_at(cs: int, ip: int, count: int = 8) -> str:
        return " ".join(f"{cpu.read8(cs, ip + i):02X}" for i in range(count))

    def result(status: str, steps: int, **details: Any) -> dict[str, Any]:
        return {
            "status": status,
            "instruction_limit": instruction_limit,
            "instructions_executed": steps,
            "last_instructions": history[-16:],
            "state_at_stop": state(),
            "serviced_imports": serviced_imports,
            **details,
        }

    for steps in range(instruction_limit):
        cs, ip = cpu.CS, cpu.IP
        encoded = bytes_at(cs, ip, 8)
        try:
            event = cpu.step()
        except UnsupportedOpcode as exc:
            return result(
                "unsupported_instruction",
                steps,
                location=f"{cs:04X}:{ip:04X}",
                bytes=encoded,
                error=str(exc),
            )

        history.append({"location": f"{cs:04X}:{ip:04X}", "bytes": encoded})
        if event[0] == "host_interrupt":
            return result(
                "host_interrupt",
                steps + 1,
                location=f"{cs:04X}:{ip:04X}",
                interrupt=f"{event[1]:02X}",
            )
        if event[0] == "far_call":
            target_cs, target_ip = event[1], event[2]
            target = loaded.import_targets.get((target_cs, target_ip))
            if target is not None:
                if (import_handler is not None and target.module.upper() == "KERNEL"
                        and target.kind == "ordinal" and target.ordinal == 102):
                    service_input = {
                        name: f"{getattr(cpu, name):04X}"
                        for name in ("AX", "BX", "CX", "DX", "DS", "ES", "SS", "SP")
                    }
                    try:
                        service_returned = import_handler(cpu, target_cs, target_ip)
                    except UnsupportedImport as exc:
                        return result(
                            "unsupported_import_service",
                            steps + 1,
                            call_site=f"{cs:04X}:{ip:04X}",
                            target_location=f"{target_cs:04X}:{target_ip:04X}",
                            **{
                                "import": {
                                    "module": target.module,
                                    "kind": target.kind,
                                    "ordinal": target.ordinal,
                                    "name": target.name,
                                },
                            },
                            error=str(exc),
                        )
                    if service_returned is not True:
                        cpu.far_return()
                    serviced_imports.append({
                        "module": target.module,
                        "ordinal": target.ordinal,
                        "call_site": f"{cs:04X}:{ip:04X}",
                        "target_location": f"{target_cs:04X}:{target_ip:04X}",
                        "input_registers": service_input,
                        "return_registers": {
                            name: f"{getattr(cpu, name):04X}"
                            for name in ("AX", "BX", "CX", "DX", "DS", "ES", "SS", "SP")
                        },
                    })
                    continue
                return result(
                    "next_import",
                    steps + 1,
                    **{
                        "call_site": f"{cs:04X}:{ip:04X}",
                        "target_location": f"{target_cs:04X}:{target_ip:04X}",
                        "import": {
                            "module": target.module,
                            "kind": target.kind,
                            "ordinal": target.ordinal,
                            "name": target.name,
                        },
                    },
                )
            if target_cs not in code_selectors:
                return result(
                    "unmapped_far_call",
                    steps + 1,
                    call_site=f"{cs:04X}:{ip:04X}",
                    target_location=f"{target_cs:04X}:{target_ip:04X}",
                )

    return result("instruction_limit", instruction_limit)


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
              task_registers: InitTaskRegisters | None = None,
              dos_launch_context: SyntheticDosLaunchContext | None = None,
              dos_version: SyntheticDosVersion | None = None,
              continuation_limit: int = 256) -> dict[str, Any]:
    """Execute synthetic InitTask and bounded DOS3Call slices, then trace onward."""
    before = hashlib.sha256(image_bytes).hexdigest()
    if before.lower() != expected_sha256.lower():
        raise ProbeError(f"input SHA-256 mismatch: got {before}")

    loaded = NELoader.from_bytes(image_bytes, "WINMINE-original.EXE").load()
    task = task_registers or InitTaskRegisters()
    cpu = CPU(memory=loaded.memory)
    cpu.CS, cpu.IP = loaded.initial_cs, loaded.initial_ip
    cpu.SS, cpu.SP = loaded.initial_ss, loaded.initial_sp
    host = Win16Host(
        loaded,
        task,
        dos_launch_context=dos_launch_context,
        dos_version=dos_version,
    )
    host.install_dos_launch_context(cpu)

    # Stop exactly after the first imported call returns, then validate the
    # two guest instructions that consume InitTask's success result.
    cpu.run(3, import_handler=host.dispatch_import)
    if len(host.calls) != 1:
        raise ProbeError(f"expected one bound far import; observed {len(host.calls)}")
    expected_guest_return = (loaded.initial_ip + 8) & 0xFFFF
    if (cpu.CS, cpu.IP) != (loaded.initial_cs, expected_guest_return):
        raise ProbeError("InitTask host service did not return to the guest call site")
    entry_bytes = bytes(cpu.read8(cpu.CS, expected_guest_return + i) for i in range(4))
    if entry_bytes[:2] not in (bytes.fromhex("09 C0"), bytes.fromhex("0B C0")) or entry_bytes[2] != 0x74:
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

    guest_return = {
        "CS": f"{cpu.CS:04X}",
        "IP": f"{cpu.IP:04X}",
        "post_import_instructions": 2,
        "success_branch_taken": False,
    }
    entry_stack_sentinel = {"SS": f"{cpu.SS:04X}", "SP": f"{cpu.SP:04X}", "word": "0000"}
    post_entry_trace = _trace_to_dependency(
        cpu,
        loaded,
        continuation_limit,
        import_handler=host.dispatch_import,
    )

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
        "host_services_executed": [
            {
                "module": target.module,
                "kind": target.kind,
                "ordinal": target.ordinal,
                "name": target.name,
            }
            for target in host.calls
        ],
        "synthetic_dos_vectors": {
            f"{interrupt_number:02X}": {
                "segment": f"{segment:04X}",
                "offset": f"{offset:04X}",
            }
            for interrupt_number, (segment, offset)
            in sorted(host.dos_interrupt_vectors.items())
        },
        "synthetic_dos_launch_context": (
            None if host.dos_launch_context is None else host.dos_launch_context.report()
        ),
        "synthetic_dos_version": (
            None if host.dos_version is None else {
                "major": host.dos_version.major,
                "minor": host.dos_version.minor,
                "oem_id": host.dos_version.oem_id,
                "serial24": f"{host.dos_version.serial24:06X}",
            }
        ),
        "dos3call_records": [
            {
                "request_ax": f"{record.request_ax:04X}",
                "interrupt_number": f"{record.interrupt_number:02X}",
                "action": record.action,
                "vector_before": (
                    None if record.vector_before is None else {
                        "segment": f"{record.vector_before[0]:04X}",
                        "offset": f"{record.vector_before[1]:04X}",
                    }
                ),
                "vector_after": {
                    "segment": f"{record.vector_after[0]:04X}",
                    "offset": f"{record.vector_after[1]:04X}",
                },
                "handler_sp": f"{record.handler_sp:04X}",
                "returned_sp": f"{record.returned_sp:04X}",
            }
            for record in host.dos3call_records
        ],
        "dos_version_call_records": [
            {
                "request_ax": f"{record.request_ax:04X}",
                "major": record.major,
                "minor": record.minor,
                "oem_id": record.oem_id,
                "serial24": f"{record.serial24:06X}",
                "handler_sp": f"{record.handler_sp:04X}",
                "returned_sp": f"{record.returned_sp:04X}",
            }
            for record in host.dos_version_call_records
        ],
        "guest_return": guest_return,
        "task_register_context": {
            "AX": "0001", "BX": f"{task.command_tail_offset & 0xFFFF:04X}",
            "CX": f"{task.stack_limit & 0xFFFF:04X}",
            "DX": f"{task.show_command & 0xFFFF:04X}",
            "SI": f"{task.previous_instance & 0xFFFF:04X}",
            "DI": f"{task.instance & 0xFFFF:04X}",
            "ES": f"{task.psp_segment & 0xFFFF:04X}",
        },
        "task_stack_sentinel": entry_stack_sentinel,
        "final": {key: f"{value:04X}" for key, value in state.items()},
        "post_entry_trace": post_entry_trace,
        "reference_match": True,
        "input_bytes_unchanged": True,
        "qualification": (
            "host-only bounded entry trace; KERNEL ordinal 91 uses an explicit synthetic "
            "InitTask context; KERNEL ordinal 102 uses only DOS3Call AX=3000h/3500h/2500h "
            "when explicit synthetic DOS version and launch-context data are supplied; the "
            "PSP/environment/IVT are a guarded partial fixture, not DOS or Windows allocation; "
            "no broader startup, full-app, release, or hardware qualification"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="read-only path to a caller-supplied NE executable")
    parser.add_argument("--sha256", required=True, help="pinned SHA-256 required before any probe runs")
    parser.add_argument(
        "--synthetic-dos-context",
        type=Path,
        help="JSON file declaring every PSP/environment/IVT value used by this synthetic trace",
    )
    parser.add_argument(
        "--synthetic-dos-version",
        metavar="MAJOR.MINOR",
        help="explicit synthetic DOS version returned by the bounded DOS3Call model",
    )
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error("image path is not a regular file")
    before = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if before.lower() != args.sha256.lower():
        parser.error(f"input SHA-256 mismatch: got {before}")
    dos_launch_context = None
    if args.synthetic_dos_context:
        try:
            dos_launch_context = SyntheticDosLaunchContext.from_json_file(
                args.synthetic_dos_context
            )
        except DosContextError as exc:
            parser.error(str(exc))
    dos_version = None
    if args.synthetic_dos_version:
        try:
            major_text, minor_text = args.synthetic_dos_version.split(".", 1)
            major, minor = int(major_text, 10), int(minor_text, 10)
            dos_version = SyntheticDosVersion(major=major, minor=minor)
        except (ValueError, TypeError):
            parser.error("--synthetic-dos-version must be decimal MAJOR.MINOR byte values")
    result = run_probe(
        args.image.read_bytes(),
        args.sha256,
        dos_launch_context=dos_launch_context,
        dos_version=dos_version,
    )
    after = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if after != before:
        raise ProbeError("input file changed while the probe was running")
    result["input_file_unchanged"] = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DosContextError, NELoadError, ProbeError, UnsupportedOpcode, UnsupportedImport) as exc:
        print(f"probe failed closed: {exc}", file=sys.stderr)
        raise SystemExit(2)

