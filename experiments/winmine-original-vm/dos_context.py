"""Explicit, deterministic DOS launch-memory slice for host-only probes."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cpu_subset import CPU, UnsupportedOpcode
from ne_loader import LoadedNE
if TYPE_CHECKING:
    from win16_host import InitTaskRegisters


class DosContextError(ValueError):
    """The declared synthetic DOS launch slice is malformed or overlaps guest memory."""


def _ascii_text(value: str, label: str, *, allow_empty: bool = False) -> bytes:
    if not isinstance(value, str) or (not value and not allow_empty):
        raise DosContextError(f"{label} must be a non-empty ASCII string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise DosContextError(f"{label} must contain ASCII only") from exc
    if any(byte == 0 or byte < 0x20 or byte == 0x7F for byte in encoded):
        raise DosContextError(f"{label} must not contain NUL or control bytes")
    return encoded


def build_dos_environment_block(entries: tuple[str, ...], program_path: str) -> bytes:
    """Build the explicitly supplied DOS environment and one-entry path trailer."""
    if not isinstance(entries, tuple):
        raise DosContextError("environment_entries must be a tuple of strings")
    encoded_entries = []
    for entry in entries:
        encoded = _ascii_text(entry, "environment entry")
        if "=" not in entry or entry.startswith("="):
            raise DosContextError("environment entries must be NAME=value strings")
        encoded_entries.append(encoded)
    path = _ascii_text(program_path, "program_path")
    variables = b"\0".join(encoded_entries) + b"\0\0"
    block = variables + b"\x01\x00" + path + b"\0"
    if len(block) > 0x8000:
        raise DosContextError("synthetic environment exceeds the guest's 8000h-byte scan bound")
    validate_dos_environment_block(block)
    return block


def validate_dos_environment_block(block: bytes) -> tuple[tuple[str, ...], str]:
    """Validate and decode the bounded DOS environment format used by the fixture."""
    if not isinstance(block, bytes) or not block:
        raise DosContextError("environment block must be non-empty bytes")
    if len(block) > 0x8000:
        raise DosContextError("environment block exceeds the guest's 8000h-byte scan bound")
    boundary = block.find(b"\0\0")
    if boundary < 0:
        raise DosContextError("environment strings are missing the double-NUL terminator")
    raw_entries = block[:boundary]
    entries_bytes = [] if not raw_entries else raw_entries.split(b"\0")
    entries: list[str] = []
    for raw in entries_bytes:
        try:
            entry = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise DosContextError("environment entry is not ASCII") from exc
        _ascii_text(entry, "environment entry")
        if "=" not in entry or entry.startswith("="):
            raise DosContextError("environment entries must be NAME=value strings")
        entries.append(entry)

    trailer = boundary + 2
    if len(block) < trailer + 3:
        raise DosContextError("environment path trailer is truncated")
    count = int.from_bytes(block[trailer:trailer + 2], "little")
    if count != 1:
        raise DosContextError("synthetic DOS environment trailer must declare one path string")
    path_bytes = block[trailer + 2:]
    if not path_bytes.endswith(b"\0") or path_bytes.count(b"\0") != 1:
        raise DosContextError("environment path trailer must contain one NUL-terminated path")
    try:
        path = path_bytes[:-1].decode("ascii")
    except UnicodeDecodeError as exc:
        raise DosContextError("environment program path is not ASCII") from exc
    _ascii_text(path, "program_path")
    return tuple(entries), path


@dataclass(frozen=True)
class SyntheticDosLaunchContext:
    """A small, caller-declared PSP/environment/IVT slice; not a DOS process."""

    psp_segment: int
    environment_segment: int
    environment_entries: tuple[str, ...]
    program_path: str
    command_tail: str
    interrupt_vectors: tuple[tuple[int, int, int], ...]

    def __post_init__(self) -> None:
        for label, value in (("psp_segment", self.psp_segment),
                             ("environment_segment", self.environment_segment)):
            if not isinstance(value, int) or not 0 <= value <= 0xFFFF:
                raise DosContextError(f"{label} must be a 16-bit unsigned value")
        tail = _ascii_text(self.command_tail, "command_tail", allow_empty=True)
        if len(tail) > 126:
            raise DosContextError("command_tail exceeds the 126-byte PSP limit")
        build_dos_environment_block(self.environment_entries, self.program_path)
        if not isinstance(self.interrupt_vectors, tuple) or not self.interrupt_vectors:
            raise DosContextError("interrupt_vectors must explicitly include at least INT 00h")
        seen: set[int] = set()
        for row in self.interrupt_vectors:
            if (not isinstance(row, tuple) or len(row) != 3
                    or any(not isinstance(value, int) for value in row)):
                raise DosContextError("interrupt vector rows must be (number, segment, offset) tuples")
            number, segment, offset = row
            if not 0 <= number <= 0xFF or not 0 <= segment <= 0xFFFF or not 0 <= offset <= 0xFFFF:
                raise DosContextError("interrupt vector values are outside their 8/16-bit ranges")
            if number in seen:
                raise DosContextError(f"interrupt vector {number:02X}h is declared more than once")
            seen.add(number)
        if 0 not in seen:
            raise DosContextError("the current DOS3Call trace requires an explicit INT 00h vector")

    @property
    def environment_block(self) -> bytes:
        return build_dos_environment_block(self.environment_entries, self.program_path)

    @property
    def dos_interrupt_vectors(self) -> dict[int, tuple[int, int]]:
        return {number: (segment, offset) for number, segment, offset in self.interrupt_vectors}

    @classmethod
    def from_json_file(cls, path: Path) -> "SyntheticDosLaunchContext":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DosContextError(f"cannot read synthetic DOS context JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise DosContextError("synthetic DOS context must be a JSON object")
        expected = {
            "format", "notice", "psp_segment", "environment_segment",
            "environment_entries", "program_path", "command_tail", "interrupt_vectors",
        }
        if set(value) != expected:
            raise DosContextError("synthetic DOS context has missing or unknown fields")
        if value["format"] != "winmine-synthetic-dos-launch-v1":
            raise DosContextError("unsupported synthetic DOS context format")
        if not isinstance(value["notice"], str) or "synthetic" not in value["notice"].lower():
            raise DosContextError("context notice must clearly label the values synthetic")
        if not isinstance(value["environment_entries"], list):
            raise DosContextError("environment_entries must be a JSON array")
        if not isinstance(value["interrupt_vectors"], dict):
            raise DosContextError("interrupt_vectors must be a JSON object")
        vectors = []
        for number, pointer in value["interrupt_vectors"].items():
            if not isinstance(pointer, dict) or set(pointer) != {"segment", "offset"}:
                raise DosContextError("each interrupt vector must declare segment and offset")
            try:
                vectors.append((int(number, 16), int(pointer["segment"], 16),
                                int(pointer["offset"], 16)))
            except (TypeError, ValueError) as exc:
                raise DosContextError("interrupt vector values must be hexadecimal strings") from exc
        try:
            psp = int(value["psp_segment"], 16)
            environment = int(value["environment_segment"], 16)
        except (TypeError, ValueError) as exc:
            raise DosContextError("PSP and environment segments must be hexadecimal strings") from exc
        if any(not isinstance(value[name], str) for name in ("program_path", "command_tail")):
            raise DosContextError("program_path and command_tail must be strings")
        if any(not isinstance(entry, str) for entry in value["environment_entries"]):
            raise DosContextError("environment_entries must contain strings")
        return cls(
            psp_segment=psp,
            environment_segment=environment,
            environment_entries=tuple(value["environment_entries"]),
            program_path=value["program_path"],
            command_tail=value["command_tail"],
            interrupt_vectors=tuple(vectors),
        )

    def validate_for(self, cpu: CPU, loaded: LoadedNE,
                     task_registers: InitTaskRegisters) -> None:
        if len(cpu.memory) != 1 << 20:
            raise DosContextError("the synthetic real-mode context requires exactly 1 MiB guest memory")
        if cpu.memory is not loaded.memory:
            raise DosContextError("CPU and loaded NE must share the same guest memory object")
        if self.psp_segment != task_registers.psp_segment:
            raise DosContextError("InitTask PSP segment disagrees with the synthetic PSP context")
        if task_registers.command_tail_offset != 0x0080:
            raise DosContextError("the DOS context models only the standard PSP command-tail offset 80h")
        psp_start = self.psp_segment << 4
        psp_end = psp_start + 0x100
        environment_start = self.environment_segment << 4
        environment = self.environment_block
        environment_end = environment_start + len(environment)
        environment_scan_end = environment_start + 0x8000
        if psp_start < 0x400:
            raise DosContextError("PSP region overlaps the IVT")
        if psp_start < 0x10000 or psp_end > len(cpu.memory):
            raise DosContextError("PSP region is outside guest memory or overlaps low DOS memory")
        if environment_start < 0x400:
            raise DosContextError("environment scan window overlaps the IVT")
        if environment_start < 0x10000 or environment_scan_end > len(cpu.memory):
            raise DosContextError(
                "environment scan window is outside guest memory or overlaps low DOS memory"
            )
        if max(psp_start, environment_start) < min(psp_end, environment_scan_end):
            raise DosContextError("PSP and environment scan window overlap")
        for selector in set(loaded.segment_selectors.values()):
            segment_start = selector << 4
            segment_end = min(segment_start + 0x10000, len(cpu.memory))
            for label, start, end in (("PSP", psp_start, psp_end),
                                      ("environment scan window", environment_start,
                                       environment_scan_end)):
                if max(start, segment_start) < min(end, segment_end):
                    raise DosContextError(
                        f"synthetic {label} overlaps loaded selector window {selector:04X}"
                    )

    def install(self, cpu: CPU, loaded: LoadedNE,
                task_registers: InitTaskRegisters) -> None:
        """Install only explicitly described bytes and guard other DOS memory reads."""
        self.validate_for(cpu, loaded, task_registers)
        psp_start = self.psp_segment << 4
        environment_start = self.environment_segment << 4
        environment = self.environment_block
        allowed_psp = set(range(0x2C, 0x2E))
        tail = self.command_tail.encode("ascii")
        allowed_psp.update(range(0x80, 0x82 + len(tail)))

        cpu.memory[psp_start + 0x2C:psp_start + 0x2E] = self.environment_segment.to_bytes(2, "little")
        cpu.memory[psp_start + 0x80] = len(tail)
        cpu.memory[psp_start + 0x81:psp_start + 0x81 + len(tail)] = tail
        cpu.memory[psp_start + 0x81 + len(tail)] = 0x0D
        cpu.memory[environment_start:environment_start + len(environment)] = environment

        allowed_ivt: set[int] = set()
        for number, segment, offset in self.interrupt_vectors:
            address = number * 4
            cpu.memory[address:address + 2] = offset.to_bytes(2, "little")
            cpu.memory[address + 2:address + 4] = segment.to_bytes(2, "little")
            allowed_ivt.update(range(address, address + 4))

        written_since_install: set[int] = set()
        cpu.memory_write_observer = written_since_install.add

        def guard(address: int, segment: int, offset: int) -> None:
            if address in written_since_install:
                return
            if psp_start <= address < psp_start + 0x100 and address - psp_start not in allowed_psp:
                raise UnsupportedOpcode(
                    f"uninitialized synthetic PSP read at {segment:04X}:{offset:04X}"
                )
            if address < 0x400 and address not in allowed_ivt:
                raise UnsupportedOpcode(
                    f"uninitialized synthetic IVT read at physical {address:05X}"
                )
            if 0x400 <= address < 0x10000:
                raise UnsupportedOpcode(
                    f"uninitialized synthetic low DOS memory read at physical {address:05X}"
                )
            if (environment_start <= address < environment_start + 0x8000
                    and address >= environment_start + len(environment)):
                raise UnsupportedOpcode(
                    f"unterminated or out-of-range synthetic environment read at {segment:04X}:{offset:04X}"
                )

        cpu.memory_read_guard = guard

    def report(self) -> dict[str, Any]:
        return {
            "synthetic": True,
            "psp_segment": f"{self.psp_segment:04X}",
            "environment_segment": f"{self.environment_segment:04X}",
            "environment_entries": list(self.environment_entries),
            "program_path": self.program_path,
            "command_tail": self.command_tail,
            "environment_block_bytes": len(self.environment_block),
            "initial_interrupt_vectors": {
                f"{number:02X}": {"segment": f"{segment:04X}", "offset": f"{offset:04X}"}
                for number, segment, offset in self.interrupt_vectors
            },
            "scope": "explicit partial PSP/environment/IVT fixture; not a DOS process or Windows task",
        }
