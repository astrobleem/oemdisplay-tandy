#!/usr/bin/env python3
"""Conservative host-side analyzer for 16-bit Windows NE executables.

This module reads NE metadata, import fixups, and disassembles reachable 16-bit
x86 code with Capstone. It never executes the input file. A static result can
be BLOCKED, CANDIDATE, or UNKNOWN; COMPATIBLE requires explicit runtime evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


class NEFormatError(ValueError):
    """The input is truncated, malformed, or not a supported NE image."""


class AnalyzerError(RuntimeError):
    """The analyzer cannot run because a required host dependency is missing."""


def _u16(data: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise NEFormatError(f"truncated {label} at file offset 0x{offset:X}")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise NEFormatError(f"truncated {label} at file offset 0x{offset:X}")
    return struct.unpack_from("<I", data, offset)[0]


def _slice(data: bytes, offset: int, size: int, label: str) -> bytes:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise NEFormatError(f"truncated {label} at file offset 0x{offset:X}")
    return data[offset : offset + size]


def _decode_name(raw: bytes) -> str:
    return raw.decode("cp437", errors="replace")


def _read_pascal(data: bytes, offset: int, limit: int, label: str) -> tuple[str, int]:
    if offset >= limit or limit > len(data):
        raise NEFormatError(f"invalid {label} string offset 0x{offset:X}")
    length = data[offset]
    end = offset + 1 + length
    if end > limit:
        raise NEFormatError(f"truncated {label} string at file offset 0x{offset:X}")
    return _decode_name(data[offset + 1 : end]), end


@dataclass(frozen=True)
class Segment:
    number: int
    file_offset: int
    file_length: int
    flags: int
    minimum_allocation: int
    data: bytes
    relocations: tuple[dict[str, int], ...]

    @property
    def is_data(self) -> bool:
        return bool(self.flags & 0x0001)


@dataclass(frozen=True)
class Import:
    module: str
    kind: str
    name: str | None
    ordinal: int | None
    segment: int
    source_offset: int
    source_type: int


@dataclass(frozen=True)
class EntryPoint:
    ordinal: int
    segment: int
    offset: int
    source: str


class NEImage:
    """Bounds-checked reader for DOS-wrapped Windows NE files."""

    HEADER_SIZE = 0x40
    TARGET_OS = {
        1: "OS/2",
        2: "Windows",
        3: "European MS-DOS 4.x",
        4: "Windows 386",
        5: "BOSS",
    }
    SEGMENT_RELOCATIONS = 0x0100
    RELOCATION_ADDITIVE = 0x04
    RELOCATION_WIDTHS = {0: 1, 2: 2, 3: 4, 5: 2, 11: 6, 13: 4}

    def __init__(self, data: bytes, source: str = "<memory>") -> None:
        self.data = data
        self.source = source
        if len(data) < 0x40 or data[:2] != b"MZ":
            raise NEFormatError("missing or truncated DOS MZ header")
        self.ne_offset = _u32(data, 0x3C, "DOS e_lfanew")
        if self.ne_offset + self.HEADER_SIZE > len(data):
            raise NEFormatError("NE header lies outside the file")
        if data[self.ne_offset : self.ne_offset + 2] != b"NE":
            raise NEFormatError("DOS e_lfanew does not point to an NE signature")

        h = self.ne_offset
        self.linker_version = (data[h + 2], data[h + 3])
        self.entry_table_offset = _u16(data, h + 4, "NE entry table offset")
        self.entry_table_length = _u16(data, h + 6, "NE entry table length")
        self.program_flags = data[h + 0x0C]
        self.application_flags = data[h + 0x0D]
        self.auto_data_segment = _u16(data, h + 0x0E, "NE auto-data segment")
        self.heap_size = _u16(data, h + 0x10, "NE heap size")
        self.stack_size = _u16(data, h + 0x12, "NE stack size")
        self.initial_ip = _u16(data, h + 0x14, "NE initial IP")
        self.initial_cs = _u16(data, h + 0x16, "NE initial CS")
        self.initial_sp = _u16(data, h + 0x18, "NE initial SP")
        self.initial_ss = _u16(data, h + 0x1A, "NE initial SS")
        self.segment_count = _u16(data, h + 0x1C, "NE segment count")
        self.module_count = _u16(data, h + 0x1E, "NE module reference count")
        self.nonresident_names_length = _u16(data, h + 0x20, "NE nonresident names length")
        self.segment_table_offset = _u16(data, h + 0x22, "NE segment table offset")
        self.resource_table_offset = _u16(data, h + 0x24, "NE resource table offset")
        self.resident_names_offset = _u16(data, h + 0x26, "NE resident names offset")
        self.module_table_offset = _u16(data, h + 0x28, "NE module table offset")
        self.import_table_offset = _u16(data, h + 0x2A, "NE import-name table offset")
        self.nonresident_names_file_offset = _u32(data, h + 0x2C, "NE nonresident names file offset")
        self.movable_entry_count = _u16(data, h + 0x30, "NE movable entry count")
        self.alignment_shift = _u16(data, h + 0x32, "NE alignment shift")
        self.target_os_id = data[h + 0x36]
        self.other_flags = data[h + 0x37]
        self.expected_windows_version = _u16(data, h + 0x3E, "NE expected Windows version")

        if self.alignment_shift > 15:
            raise NEFormatError(f"invalid NE alignment shift {self.alignment_shift}")
        self.target_os = self.TARGET_OS.get(self.target_os_id, f"unknown ({self.target_os_id})")
        self.windows_version = (self.expected_windows_version >> 8, self.expected_windows_version & 0xFF)

        self.segments = self._read_segments()
        self.import_name_table, self.import_name_offsets = self._read_import_name_table()
        self.modules = self._read_module_refs()
        self.imports = self._read_imports()
        resident_start = self.ne_offset + self.resident_names_offset if self.resident_names_offset else 0
        self.resident_exports = self._read_name_table(resident_start, None, "resident names")
        self.nonresident_exports = self._read_name_table(
            self.nonresident_names_file_offset,
            self.nonresident_names_file_offset + self.nonresident_names_length,
            "nonresident names",
        )
        self.entry_points, self.constant_entry_ordinals, self.entry_table_complete = self._read_entry_table()

    def _relative(self, relative: int, length: int, label: str) -> int:
        absolute = self.ne_offset + relative
        _slice(self.data, absolute, length, label)
        return absolute

    def _next_table_limit(self, relative: int, *, include_entry_table: bool = True) -> int:
        """Return the first known NE structure after a relative table offset."""
        start = self.ne_offset + relative
        candidates: list[int] = []
        offsets = (
            (self.entry_table_offset, include_entry_table and self.entry_table_length > 0),
            (self.segment_table_offset, self.segment_count > 0),
            (self.resource_table_offset, self.resource_table_offset > 0),
            (self.resident_names_offset, self.resident_names_offset > 0),
            (self.module_table_offset, self.module_count > 0),
        )
        for offset, present in offsets:
            absolute = self.ne_offset + offset
            if present and absolute > start and absolute <= len(self.data):
                candidates.append(absolute)
        if self.nonresident_names_length:
            absolute = self.nonresident_names_file_offset
            if absolute > start and absolute <= len(self.data):
                candidates.append(absolute)
        for segment in self.segments:
            if segment.file_offset > start:
                candidates.append(segment.file_offset)
        return min(candidates, default=len(self.data))

    def _read_segments(self) -> tuple[Segment, ...]:
        if self.segment_count and self.segment_table_offset < self.HEADER_SIZE:
            raise NEFormatError("NE segment table overlaps the NE header")
        table = self._relative(self.segment_table_offset, self.segment_count * 8, "NE segment table")
        result: list[Segment] = []
        for index in range(self.segment_count):
            p = table + index * 8
            sector = _u16(self.data, p, "segment file sector")
            stored_length = _u16(self.data, p + 2, "segment file length")
            flags = _u16(self.data, p + 4, "segment flags")
            minimum = _u16(self.data, p + 6, "segment minimum allocation")
            length = stored_length or 0x10000
            file_offset = sector << self.alignment_shift if sector else 0
            segment_data = b"" if sector == 0 else _slice(self.data, file_offset, length, f"segment {index + 1} data")
            relocations: list[dict[str, int]] = []
            if flags & self.SEGMENT_RELOCATIONS:
                if sector == 0:
                    raise NEFormatError(f"segment {index + 1} has relocations but no file data")
                reloc_base = file_offset + length
                count = _u16(self.data, reloc_base, f"segment {index + 1} relocation count")
                if count > 0x4000:
                    raise NEFormatError(f"implausible relocation count in segment {index + 1}")
                _slice(self.data, reloc_base + 2, count * 8, f"segment {index + 1} relocations")
                for rindex in range(count):
                    q = reloc_base + 2 + rindex * 8
                    source_type = self.data[q]
                    source_address_type = source_type & 0x7F
                    source_offset = _u16(self.data, q + 2, "relocation source offset")
                    source_width = self.RELOCATION_WIDTHS.get(source_address_type, 1)
                    if source_offset + source_width > length:
                        raise NEFormatError(
                            f"relocation source in segment {index + 1} exceeds its {length}-byte segment"
                        )
                    target_flags = self.data[q + 1]
                    if target_flags & self.RELOCATION_ADDITIVE:
                        chain_sites = [source_offset]
                    else:
                        chain_sites = []
                        chain_offset = source_offset
                        seen_chain_offsets: set[int] = set()
                        while True:
                            if chain_offset in seen_chain_offsets:
                                raise NEFormatError(
                                    f"cyclic relocation chain in segment {index + 1} at 0x{chain_offset:04X}"
                                )
                            if chain_offset + 2 > length:
                                raise NEFormatError(
                                    f"relocation chain in segment {index + 1} exceeds its {length}-byte segment"
                                )
                            if chain_offset + source_width > length:
                                raise NEFormatError(
                                    f"relocation source span in segment {index + 1} exceeds its {length}-byte segment"
                                )
                            seen_chain_offsets.add(chain_offset)
                            chain_sites.append(chain_offset)
                            next_offset = _u16(segment_data, chain_offset, "relocation-chain link")
                            if next_offset == 0xFFFF:
                                break
                            if next_offset >= length:
                                raise NEFormatError(
                                    f"relocation chain in segment {index + 1} points outside the segment "
                                    f"at 0x{next_offset:04X}"
                                )
                            chain_offset = next_offset
                    relocations.append(
                        {
                            "source_type": source_type,
                            "target_flags": target_flags,
                            "source_offset": source_offset,
                            "target1": _u16(self.data, q + 4, "relocation target1"),
                            "target2": _u16(self.data, q + 6, "relocation target2"),
                            "source_width": source_width,
                            "source_type_known": source_address_type in self.RELOCATION_WIDTHS,
                            "chain_sites": tuple(chain_sites),
                        }
                    )
            result.append(
                Segment(index + 1, file_offset, length, flags, minimum, segment_data, tuple(relocations))
            )
        return tuple(result)

    def _read_import_name_table(self) -> tuple[dict[int, str], dict[str, int]]:
        if self.module_count == 0:
            return {}, {}
        if self.module_table_offset < self.HEADER_SIZE:
            raise NEFormatError("NE module-reference table overlaps the NE header")
        module_end = self.module_table_offset + self.module_count * 2
        if self.import_table_offset < module_end:
            raise NEFormatError("NE import-name table overlaps the module-reference table")
        if self.import_table_offset < self.HEADER_SIZE:
            raise NEFormatError("NE import-name table overlaps the NE header")
        start = self._relative(self.import_table_offset, 1, "NE import-name table")
        # Import-name offsets are 16-bit offsets relative to this table. Keep
        # the read within both the file and that addressable range; real NE
        # files may place this string pool across other table offsets.
        limit = min(len(self.data), start + 0x10000)
        if limit <= start:
            raise NEFormatError("empty or invalid NE import-name table bounds")
        names: dict[int, str] = {}
        offsets: dict[str, int] = {}
        pos = start
        # The table is a sequence of length-prefixed names terminated by a zero byte.
        # Offset zero is reserved by the NE format; module/function name offsets
        # therefore normally point to strings beginning at relative offset one.
        if self.data[pos] == 0:
            pos += 1
        while pos < limit:
            length = self.data[pos]
            if length == 0:
                return names, offsets
            end = pos + 1 + length
            if end > limit:
                raise NEFormatError(f"truncated import-name string at file offset 0x{pos:X}")
            name = _decode_name(self.data[pos + 1 : end])
            names[pos - start] = name
            offsets[name.upper()] = pos - start
            pos = end
        raise NEFormatError("unterminated NE import-name table")

    def _read_module_refs(self) -> tuple[str, ...]:
        if self.module_count and self.module_table_offset < self.HEADER_SIZE:
            raise NEFormatError("NE module-reference table overlaps the NE header")
        table = self._relative(self.module_table_offset, self.module_count * 2, "NE module-reference table")
        modules: list[str] = []
        for index in range(self.module_count):
            name_offset = _u16(self.data, table + 2 * index, "module-reference name offset")
            if name_offset not in self.import_name_table:
                raise NEFormatError(f"module reference {index + 1} points inside no import-name string")
            modules.append(self.import_name_table[name_offset])
        return tuple(modules)

    def _read_imports(self) -> tuple[Import, ...]:
        imports: list[Import] = []
        for segment in self.segments:
            for relocation in segment.relocations:
                kind = relocation["target_flags"] & 0x03
                if kind not in (1, 2):
                    continue
                module_index = relocation["target1"]
                if module_index < 1 or module_index > len(self.modules):
                    raise NEFormatError(
                        f"import relocation in segment {segment.number} has invalid module index {module_index}"
                    )
                if kind == 1:
                    imports.append(
                        Import(self.modules[module_index - 1], "ordinal", None, relocation["target2"],
                               segment.number, relocation["source_offset"], relocation["source_type"])
                    )
                else:
                    name = self.import_name_table.get(relocation["target2"])
                    if name is None:
                        raise NEFormatError(
                            f"import-by-name relocation points inside no import-name string "
                            f"(offset 0x{relocation['target2']:X})"
                        )
                    imports.append(
                        Import(self.modules[module_index - 1], "name", name, None,
                               segment.number, relocation["source_offset"], relocation["source_type"])
                    )
        return tuple(imports)

    def _read_name_table(self, start: int, limit: int | None, label: str) -> tuple[tuple[str, int], ...]:
        if start == 0:
            if limit not in (None, 0):
                raise NEFormatError(f"{label} table has a length but no file offset")
            return ()
        if limit is None:
            limit = self._next_table_limit(start - self.ne_offset)
        if start < 0 or limit < start or limit > len(self.data):
            raise NEFormatError(f"invalid {label} bounds")
        result: list[tuple[str, int]] = []
        pos = start
        while pos < limit:
            length = self.data[pos]
            if length == 0:
                return tuple(result)
            name, after_name = _read_pascal(self.data, pos, limit, label)
            ordinal = _u16(self.data, after_name, f"{label} ordinal")
            result.append((name, ordinal))
            pos = after_name + 2
        if label == "nonresident names" and self.nonresident_names_length == 0:
            return ()
        raise NEFormatError(f"unterminated {label} table")

    def _read_entry_table(self) -> tuple[tuple[EntryPoint, ...], frozenset[int], bool]:
        if self.entry_table_length == 0:
            return (), frozenset(), True
        if self.entry_table_offset < self.HEADER_SIZE:
            raise NEFormatError("NE entry table overlaps the NE header")
        start = self._relative(self.entry_table_offset, self.entry_table_length, "NE entry table")
        end = start + self.entry_table_length
        entries: list[EntryPoint] = []
        constant_ordinals: set[int] = set()
        ordinal = 1
        pos = start
        while pos < end:
            count = self.data[pos]
            pos += 1
            if count == 0:
                return tuple(entries), frozenset(constant_ordinals), True
            if pos >= end:
                raise NEFormatError("truncated NE entry-table bundle")
            segment_number = self.data[pos]
            pos += 1
            if segment_number == 0:
                # An unused bundle reserves ordinals but contains no entry records.
                ordinal += count
                continue
            if segment_number == 0xFE:
                # Constant bundles contain flags and a WORD value per ordinal.
                if pos + count * 3 > end:
                    raise NEFormatError("truncated constant NE entry-table bundle")
                for _ in range(count):
                    constant_ordinals.add(ordinal)
                    ordinal += 1
                    pos += 3
                continue
            if segment_number == 0xFF:
                # A movable bundle stores flags, a two-byte INT 3Fh marker,
                # an 8-bit segment number, and a 16-bit offset per entry.
                for _ in range(count):
                    if pos + 6 > end:
                        raise NEFormatError("truncated movable NE entry-table record")
                    _flags = self.data[pos]
                    segment = self.data[pos + 3]
                    offset = _u16(self.data, pos + 4, "movable entry-table offset")
                    if segment < 1 or segment > self.segment_count:
                        raise NEFormatError(f"movable entry refers to invalid segment {segment}")
                    entries.append(EntryPoint(ordinal, segment, offset, "movable entry table"))
                    ordinal += 1
                    pos += 6
                continue
            if segment_number > self.segment_count:
                raise NEFormatError(f"entry bundle refers to invalid segment {segment_number}")
            for _ in range(count):
                if pos + 3 > end:
                    raise NEFormatError("truncated fixed NE entry-table record")
                _flags = self.data[pos]
                offset = _u16(self.data, pos + 1, "entry-table offset")
                entries.append(EntryPoint(ordinal, segment_number, offset, "entry table"))
                ordinal += 1
                pos += 3
        return tuple(entries), frozenset(constant_ordinals), False

    def exports(self) -> tuple[dict[str, int], set[int], bool]:
        by_name: dict[str, int] = {}
        ordinals: set[int] = set()
        for name, ordinal in self.resident_exports + self.nonresident_exports:
            if ordinal:
                by_name[name.upper()] = ordinal
                ordinals.add(ordinal)
        for entry in self.entry_points:
            ordinals.add(entry.ordinal)
        ordinals.update(self.constant_entry_ordinals)
        complete = self.entry_table_complete
        return by_name, ordinals, complete

    def internal_relocations(self) -> list[dict[str, Any]]:
        result = []
        for segment in self.segments:
            for fixup in segment.relocations:
                target_kind = fixup["target_flags"] & 0x03
                if target_kind == 0:
                    target_segment = fixup["target1"]
                    result.append({
                        "source_segment": segment.number,
                        "source_offset": f"0x{fixup['source_offset']:04X}",
                        "source_type": fixup["source_type"],
                        "target_segment": target_segment,
                        "target_offset": f"0x{fixup['target2']:04X}",
                        "target_is_code": 1 <= target_segment <= len(self.segments)
                        and not self.segments[target_segment - 1].is_data,
                    })
                elif target_kind == 3:
                    result.append({
                        "source_segment": segment.number,
                        "source_offset": f"0x{fixup['source_offset']:04X}",
                        "source_type": fixup["source_type"],
                        "kind": "OS fixup",
                        "os_target": fixup["target1"],
                        "target2": fixup["target2"],
                    })
        return result

    def code_roots(self) -> tuple[EntryPoint, ...]:
        roots: list[EntryPoint] = []
        if self.initial_cs:
            roots.append(EntryPoint(0, self.initial_cs, self.initial_ip, "initial CS:IP"))
        roots.extend(self.entry_points)
        unique: dict[tuple[int, int], EntryPoint] = {}
        for root in roots:
            unique[(root.segment, root.offset)] = root
        return tuple(unique.values())


def _read_api_directory(path: Path) -> tuple[dict[str, tuple[dict[str, int], set[int], bool]], list[str]]:
    """Read available NE module exports from a local Windows 3.0 directory."""
    modules: dict[str, tuple[dict[str, int], set[int], bool]] = {}
    warnings: list[str] = []
    if not path.is_dir():
        raise AnalyzerError(f"Windows 3.0 API directory does not exist: {path}")
    extensions = {".EXE", ".DLL", ".DRV", ".MOD"}
    for file in sorted(path.rglob("*")):
        if not file.is_file() or file.suffix.upper() not in extensions:
            continue
        try:
            image = NEImage(file.read_bytes(), str(file))
        except (OSError, NEFormatError):
            continue
        key = file.stem.upper()
        export_info = image.exports()
        if key in modules and modules[key] != export_info:
            warnings.append(f"multiple different API reference modules named {key}; imports remain unverified")
            modules.pop(key, None)
            continue
        modules[key] = export_info
    return modules, warnings


_X86_PREFIXES = {0xF0, 0xF2, 0xF3, 0x26, 0x2E, 0x36, 0x3E, 0x64, 0x65, 0x66, 0x67}
_8086_MNEMONICS = {
    "aaa", "aad", "aam", "aas", "adc", "add", "and", "call", "cbw", "clc", "cld", "cli",
    "cmc", "cmp", "cmpsb", "cmpsw", "cwd", "daa", "das", "dec", "div", "lcall", "ljmp",
    "esc", "hlt", "idiv", "imul", "in", "inc", "int", "into", "iret", "ja", "jae", "jb",
    "jbe", "jc", "jcxz", "je", "jg", "jge", "jl", "jle", "jna", "jnae", "jnb", "jnbe",
    "jnc", "jne", "jng", "jnge", "jnl", "jnle", "jno", "jnp", "jns", "jnz", "jo", "jp",
    "jpe", "jpo", "js", "jz", "jmp", "lahf", "lds", "lea", "les", "lock", "lodsb", "lodsw",
    "loop", "loope", "loopne", "loopnz", "loopz", "mov", "movsb", "movsw", "mul", "neg", "nop",
    "not", "or", "out", "pop", "popf", "push", "pushf", "rcl", "rcr", "ret", "retf", "rol",
    "ror", "sahf", "sal", "sar", "sbb", "scasb", "scasw", "shl", "shr", "stc", "std", "sti",
    "stosb", "stosw", "sub", "test", "wait", "xchg", "xlat", "xlatb", "xor",
}
_8087_MNEMONICS = {
    "f2xm1", "fabs", "fadd", "faddp", "fbld", "fbstp", "fchs", "fclex", "fcom", "fcomp",
    "fcompp", "fdecstp", "fdiv", "fdivp", "fdivr", "fdivrp", "ffree", "fiadd", "ficom",
    "ficomp", "fidiv", "fidivr", "fild", "fimul", "fincstp", "finit", "fist", "fistp", "fisub",
    "fisubr", "fld", "fld1", "fldcw", "fldenv", "fldl2e", "fldl2t", "fldlg2", "fldln2", "fldpi",
    "fldz", "fmul", "fmulp", "fnclex", "fninit", "fnop", "fnsave", "fnstcw", "fnstenv", "fnstsw",
    "fpatan", "fprem", "fptan", "frndint", "frstor", "fsave", "fscale", "fsqrt", "fst", "fstcw",
    "fstenv", "fstp", "fstsw", "fsub", "fsubp", "fsubr", "fsubrp", "ftst", "fxam", "fxch", "fyl2x",
    "fyl2xp1",
}


def _cpu_requirement(insn: Any, x86_const: Any) -> tuple[str | None, str | None]:
    """Return (minimum CPU/FPU class, issue kind) for decoded instructions."""
    mnemonic = insn.mnemonic.lower()
    raw = bytes(insn.bytes)
    prefix_bytes: list[int] = []
    for byte in raw:
        if byte not in _X86_PREFIXES:
            opcode = byte
            break
        prefix_bytes.append(byte)
    else:
        opcode = None
    operand_override = 0x66 in prefix_bytes
    if any(byte in (0x64, 0x65) for byte in prefix_bytes):
        return "80386", "FS/GS segment override is newer than 8086/8088"
    if any(byte in (0x66, 0x67) for byte in prefix_bytes):
        return "80386", "operand/address-size override is newer than 8086/8088"
    cpu_186 = {
        "bound", "enter", "leave", "insb", "insw", "outsb", "outsw", "pusha", "pushaw", "popa", "popaw",
    }
    cpu_286 = {
        "arpl", "clts", "lar", "lgdt", "lidt", "lldt", "lmsw", "loadall",
        "ltr", "sgdt", "sidt", "sldt", "smsw", "str", "verr", "verw",
    }
    cpu_386 = {
        "bsf", "bsr", "bt", "btc", "btr", "bts", "cdq", "cwde", "iretd", "insd", "outsd",
        "lfs", "lgs", "movsx", "movzx", "popfd", "pushfd", "shld",
        "shrd", "seta", "setae", "setb", "setbe", "sete", "setg", "setge", "pushad", "popad",
        "setl", "setle", "setne", "setno", "setnp", "setns", "seto", "setp",
        "sets",
    }
    cpu_486 = {"bswap", "cmpxchg", "invd", "invlpg", "wbinvd", "xadd"}
    cpu_pentium = {"cpuid", "rdmsr", "rdtsc", "wrmsr"}
    if mnemonic in _8087_MNEMONICS:
        return "8087", "8087 coprocessor instruction; Windows software emulation needs runtime validation"
    if mnemonic.startswith("f") and mnemonic != "fail":
        return "UNKNOWN", f"unclassified coprocessor instruction family {mnemonic!r}"
    # Capstone 5.0.7 reports 16-bit-mode opcode 98h/99h using their 32-bit
    # mnemonic aliases. On 8086, CBW/CWD are the unprefixed forms; only 66h
    # changes them to CWDE/CDQ (and therefore requires a 386).
    if opcode in {0x98, 0x99} and not operand_override:
        return None, None
    if opcode == 0x0F and len(raw) > len(prefix_bytes) + 1:
        return "80286", "0F escape instruction family is newer than 8086/8088"
    if mnemonic in cpu_186:
        return "80186", "instruction is newer than 8086/8088"
    if mnemonic in cpu_286:
        return "80286", "instruction is newer than 8086/8088"
    if mnemonic in cpu_386 or (mnemonic.startswith("set") and len(mnemonic) > 3):
        return "80386", "instruction is newer than 8086/8088"
    if mnemonic in cpu_486:
        return "80486", "instruction is newer than 8086/8088"
    if mnemonic in cpu_pentium:
        return "Pentium", "instruction is newer than 8086/8088"
    if mnemonic == "int1":
        return "UNKNOWN", "undocumented INT1 opcode family is not classified for 8088"
    if mnemonic == "push" and len(insn.operands) == 1 and insn.operands[0].type == x86_const.X86_OP_IMM:
        return "80186", "immediate PUSH is newer than 8086/8088"
    if mnemonic == "imul" and len(insn.operands) == 3:
        return "80186", "immediate IMUL is newer than 8086/8088"
    if mnemonic in {"rol", "ror", "rcl", "rcr", "shl", "sal", "shr", "sar"} and opcode in {0xC0, 0xC1}:
        return "80186", "immediate-count shift is newer than 8086/8088"
    gpr32 = {"eax", "ebx", "ecx", "edx", "esi", "edi", "esp", "ebp", "eip", "eflags"}
    for operand in getattr(insn, "operands", ()):
        if operand.type == x86_const.X86_OP_REG:
            name = insn.reg_name(operand.reg).lower()
            if name in gpr32 or name in {"fs", "gs"} or name.startswith("cr") or name.startswith("dr"):
                return "80386", f"register {name} is newer than 8086/8088"
    if mnemonic in {"ud2", "sysenter", "sysexit", "syscall", "sysret"}:
        return "80386", "instruction is newer than 8086/8088"
    prefix_parts = mnemonic.split(maxsplit=1)
    if (
        len(prefix_parts) == 2
        and prefix_parts[0] in {"rep", "repe", "repne", "repnz", "repz"}
        and prefix_parts[1] in _8086_MNEMONICS
    ):
        return None, None
    if mnemonic in _8086_MNEMONICS:
        return None, None
    return "UNKNOWN", f"Capstone decoded unclassified instruction family {mnemonic!r}"


def _operation_bytes(insn: Any) -> set[int]:
    """Return raw prefix/opcode/ModRM positions that define the instruction family."""
    raw = bytes(insn.bytes)
    prefix_count = 0
    while prefix_count < len(raw) and raw[prefix_count] in _X86_PREFIXES:
        prefix_count += 1
    if prefix_count >= len(raw):
        return set(range(len(raw)))
    opcode_length = 2 if raw[prefix_count] == 0x0F and prefix_count + 1 < len(raw) else 1
    end = prefix_count + opcode_length
    modrm_offset = getattr(insn, "modrm_offset", 0)
    if modrm_offset:
        end = max(end, modrm_offset + 1)
    return set(range(end))


def _disassemble_reachable(image: NEImage) -> dict[str, Any]:
    try:
        import capstone
        from capstone import x86_const
    except ImportError as exc:
        raise AnalyzerError("Capstone is required; install the pinned host dependency from requirements.txt") from exc

    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    decoder.detail = True
    unsupported: list[dict[str, Any]] = []
    instruction_uncertainties: list[dict[str, Any]] = []
    fixup_uncertainties: list[dict[str, Any]] = []
    import_fixup_instruction_count = 0
    coprocessor: list[dict[str, Any]] = []
    decode_failures: list[dict[str, Any]] = []
    unresolved_edges: list[dict[str, Any]] = []
    decoded: set[tuple[int, int]] = set()
    covered: dict[int, set[int]] = {}
    fixups_by_site: dict[int, dict[int, list[dict[str, Any]]]] = {}
    for segment in image.segments:
        sites: dict[int, list[dict[str, Any]]] = {}
        for relocation in segment.relocations:
            relocation_sites: set[int] = set()
            for site in relocation["chain_sites"]:
                relocation_sites.update(range(site, site + relocation["source_width"]))
            for site in sorted(relocation_sites):
                sites.setdefault(site, []).append(relocation)
        fixups_by_site[segment.number] = sites
    uncertain_instruction_keys: set[tuple[int, int]] = set()
    roots = image.code_roots()
    valid_roots: list[EntryPoint] = []

    for root in roots:
        if root.segment < 1 or root.segment > len(image.segments):
            decode_failures.append({"segment": root.segment, "offset": root.offset, "reason": "invalid code root"})
            continue
        segment = image.segments[root.segment - 1]
        if segment.is_data:
            continue
        if root.offset >= len(segment.data):
            decode_failures.append(
                {"segment": root.segment, "offset": root.offset, "reason": "code root outside initialized bytes"}
            )
            continue
        valid_roots.append(root)
        queue = [root.offset]
        visited_at_root: set[int] = set()
        bytes_seen = covered.setdefault(root.segment, set())
        while queue:
            offset = queue.pop()
            while 0 <= offset < len(segment.data) and offset not in visited_at_root:
                if offset in bytes_seen and (root.segment, offset) not in decoded:
                    decode_failures.append(
                        {"segment": root.segment, "offset": offset, "reason": "overlapping decode paths"}
                    )
                    break
                instruction = next(decoder.disasm(segment.data[offset:], offset, count=1), None)
                if instruction is None or instruction.size <= 0:
                    decode_failures.append(
                        {"segment": root.segment, "offset": offset, "reason": "Capstone could not decode reachable bytes"}
                    )
                    break
                address = offset
                key = (root.segment, address)
                if key in decoded:
                    break
                decoded.add(key)
                visited_at_root.add(address)
                instruction_bytes = set(range(address, address + instruction.size))
                if bytes_seen.intersection(instruction_bytes) - {address}:
                    decode_failures.append(
                        {"segment": root.segment, "offset": address, "reason": "instruction overlaps another decode"}
                    )
                    break
                affecting_sites = sorted(instruction_bytes.intersection(fixups_by_site[root.segment]))
                imported_fixup_sites = [
                    site for site in affecting_sites
                    if all((fixup["target_flags"] & 0x03) in (1, 2)
                           for fixup in fixups_by_site[root.segment][site])
                ]
                unresolved_fixup_sites = [site for site in affecting_sites if site not in imported_fixup_sites]
                if affecting_sites:
                    operation_sites = sorted(
                        address + position
                        for position in _operation_bytes(instruction)
                        if address + position in affecting_sites
                    )
                    if not operation_sites and not unresolved_fixup_sites:
                        import_fixup_instruction_count += 1
                    elif key not in uncertain_instruction_keys:
                        uncertain_instruction_keys.add(key)
                        fixup_uncertainties.append(
                            {
                                "segment": root.segment,
                                "offset": address,
                                "instruction": instruction.mnemonic,
                                "operands": instruction.op_str,
                                "fixup_sites": affecting_sites,
                                "unresolved_fixup_sites": unresolved_fixup_sites,
                                "opcode_or_modrm_sites": operation_sites,
                                "reason": (
                                    "NE relocation changes opcode or ModRM bytes; instruction decode is unreliable"
                                    if operation_sites else
                                    "internal or OS fixup changes an immediate or displacement operand; its value is not final"
                                ),
                            }
                        )
                    if operation_sites:
                        unresolved_edges.append(
                            {
                                "segment": root.segment,
                                "offset": address,
                                "kind": "NE relocation affects opcode or ModRM bytes",
                            }
                        )
                        break
                bytes_seen.update(instruction_bytes)

                cpu, reason = _cpu_requirement(instruction, x86_const)
                if cpu:
                    row = {"segment": root.segment, "offset": address, "mnemonic": instruction.mnemonic,
                           "operands": instruction.op_str, "minimum_cpu": cpu, "reason": reason}
                    if cpu == "8087":
                        coprocessor.append(row)
                    elif cpu == "UNKNOWN":
                        instruction_uncertainties.append(row)
                    else:
                        unsupported.append(row)

                mnemonic = instruction.mnemonic.lower()
                operands = getattr(instruction, "operands", ())
                direct_target = None
                if operands and operands[0].type == x86_const.X86_OP_IMM:
                    direct_target = int(operands[0].imm) & 0xFFFF
                next_offset = address + instruction.size
                control_operand_relocated = bool(affecting_sites)

                if mnemonic in {"ret", "retf", "iret", "iretd", "hlt", "ud2"}:
                    break
                if mnemonic in {"jmp", "ljmp"}:
                    if mnemonic == "jmp" and direct_target is not None:
                        if control_operand_relocated:
                            unresolved_edges.append(
                                {"segment": root.segment, "offset": address,
                                 "kind": "relocated unconditional-branch target"}
                            )
                        else:
                            queue.append(direct_target)
                    elif mnemonic == "jmp":
                        unresolved_edges.append(
                            {"segment": root.segment, "offset": address, "kind": "indirect jump"}
                        )
                    else:
                        unresolved_edges.append(
                            {"segment": root.segment, "offset": address, "kind": "far jump"}
                        )
                    break
                if mnemonic.startswith("j") or mnemonic in {"loop", "loope", "loopne", "loopnz", "loopz"}:
                    if direct_target is not None and not control_operand_relocated:
                        if direct_target < len(segment.data):
                            queue.append(direct_target)
                        else:
                            decode_failures.append(
                                {"segment": root.segment, "offset": address,
                                 "reason": "conditional branch target outside initialized bytes"}
                            )
                    else:
                        unresolved_edges.append(
                            {
                                "segment": root.segment,
                                "offset": address,
                                "kind": (
                                    "relocated conditional-branch target"
                                    if control_operand_relocated else "indirect conditional jump"
                                ),
                            }
                        )
                    offset = next_offset
                    continue
                if mnemonic in {"call", "lcall"}:
                    if mnemonic == "call" and direct_target is not None:
                        if control_operand_relocated:
                            unresolved_edges.append(
                                {
                                    "segment": root.segment,
                                    "offset": address,
                                    "kind": (
                                        "imported API call target"
                                        if imported_fixup_sites and not unresolved_fixup_sites
                                        else "relocated call target"
                                    ),
                                }
                            )
                        else:
                            queue.append(direct_target)
                    else:
                        unresolved_edges.append(
                            {
                                "segment": root.segment,
                                "offset": address,
                                "kind": (
                                    "imported API far call"
                                    if imported_fixup_sites and not unresolved_fixup_sites
                                    else "indirect or far call"
                                ),
                            }
                        )
                if next_offset >= len(segment.data):
                    break
                offset = next_offset

    return {
        "decoder": f"Capstone {capstone.__version__}, x86 16-bit mode",
        "roots": [asdict(root) for root in valid_roots],
        "reachable_instruction_count": len(decoded),
        "code_bytes_reached": sum(len(x) for x in covered.values()),
        "unsupported_instructions": unsupported,
        "instruction_classification_uncertainties": instruction_uncertainties,
        "coprocessor_instructions": coprocessor,
        "relocation_affected_instructions": fixup_uncertainties,
        "import_fixup_instruction_count": import_fixup_instruction_count,
        "decode_failures": decode_failures,
        "unresolved_control_flow": unresolved_edges,
        "entry_table_complete": image.entry_table_complete,
        "reachability_complete": False,
    }


def _api_statuses(image: NEImage, api_dir: Path | None) -> tuple[list[dict[str, Any]], list[str], bool]:
    if api_dir is None:
        return [
            {"module": name, "reference": "not supplied", "status": "UNVERIFIED"}
            for name in sorted(set(image.modules), key=str.upper)
        ], [], False
    api_modules, warnings = _read_api_directory(api_dir)
    statuses: list[dict[str, Any]] = []
    missing: list[str] = []
    all_verified = True
    referenced = {name.upper() for name in image.modules}
    for module in sorted(referenced, key=str.upper):
        ref = api_modules.get(module)
        module_imports = [item for item in image.imports if item.module.upper() == module]
        if ref is None:
            all_verified = False
            statuses.append({"module": module, "reference": "not found in supplied API directory", "status": "UNVERIFIED"})
            continue
        names, ordinals, exports_complete = ref
        statuses.append({"module": module, "reference": "local NE module", "status": "FOUND",
                         "export_name_count": len(names), "entry_ordinal_count": len(ordinals)})
        for item in module_imports:
            row = {
                "module": item.module,
                "import": item.name if item.kind == "name" else f"#{item.ordinal}",
                "kind": item.kind,
                "segment": item.segment,
                "source_offset": f"0x{item.source_offset:04X}",
            }
            if item.kind == "name":
                present = item.name.upper() in names
                row["resolved_names"] = [item.name]
            else:
                present = item.ordinal in ordinals
                row["resolved_names"] = sorted(
                    name for name, exported_ordinal in names.items() if exported_ordinal == item.ordinal
                )
            if present:
                row["status"] = "AVAILABLE_IN_REFERENCE"
            elif exports_complete:
                row["status"] = "MISSING_FROM_WINDOWS_3_0_REFERENCE"
                missing.append(f"{item.module}!{row['import']}")
            else:
                row["status"] = "UNVERIFIED_ORDINAL"
                all_verified = False
            statuses.append(row)
    # If no relocation imports exist, module references alone are still shown.
    return statuses, missing, all_verified


def _runtime_evidence(path: Path | None, data: bytes, source: str) -> tuple[bool, str | None]:
    if path is None:
        return False, None
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return False, f"runtime evidence could not be read: {exc}"
    if len(raw) > 64 * 1024:
        return False, "runtime evidence exceeds the 64 KiB limit"

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate runtime-evidence key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return False, f"runtime evidence is invalid JSON: {exc}"
    if not isinstance(value, dict):
        return False, "runtime evidence must be a JSON object"
    if set(value) != {"schema", "result", "image", "target", "actions"}:
        return False, "runtime evidence does not match the required schema"
    if value.get("schema") != "w31check-runtime-v1":
        return False, "runtime evidence schema version is missing or unsupported"
    if value.get("result") != "PASS":
        return False, "runtime evidence result is not PASS"

    image = value.get("image")
    if not isinstance(image, dict) or set(image) != {"filename", "size_bytes", "sha256"}:
        return False, "runtime evidence lacks an exact image identity"
    expected_image = {
        "filename": Path(source).name,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    if (
        type(image.get("filename")) is not str
        or type(image.get("size_bytes")) is not int
        or type(image.get("sha256")) is not str
        or not re.fullmatch(r"[0-9a-f]{64}", image["sha256"])
        or image != expected_image
    ):
        return False, "runtime evidence image identity does not match the analyzed input"

    target = value.get("target", {})
    actions = value.get("actions", {})
    required_target = {
        "windows": "3.0", "mode": "real", "cpu": "8088", "memory_kb": 640,
        "display": "320x200x16",
    }
    required_actions = {"input": True, "representative_task": True, "redraw": True, "clean_exit": True}
    if not isinstance(target, dict) or set(target) != set(required_target):
        return False, "runtime evidence target is incomplete or has unsupported fields"
    if any(type(target.get(key)) is not type(expected) or target[key] != expected
           for key, expected in required_target.items()):
        return False, "runtime evidence target does not match Windows 3.0 real mode on 8088/640 KB/320x200x16"
    if not isinstance(actions, dict) or set(actions) != set(required_actions):
        return False, "runtime evidence actions are incomplete or have unsupported fields"
    if any(actions.get(key) is not expected for key, expected in required_actions.items()):
        return False, "runtime evidence lacks input, representative-task, redraw, or clean-exit proof"
    return True, None


def analyze_bytes(
    data: bytes,
    source: str = "<memory>",
    api_dir: Path | None = None,
    runtime_evidence: Path | None = None,
) -> dict[str, Any]:
    image = NEImage(data, source)
    disassembly = _disassemble_reachable(image)
    api_statuses, missing_apis, apis_verified = _api_statuses(image, api_dir)
    protected_modules = sorted(
        {
            module for module in image.modules
            if module.upper().endswith((".386", ".VXD"))
            or module.upper() in {"WIN386", "KRNL386", "VMM", "DOSX", "VXD", "WIN32S"}
        },
        key=str.upper,
    )
    dynamic_names = {"GETPROCADDRESS", "LOADLIBRARY", "LOADLIBRARYA", "LOADLIBRARYW"}
    dynamic_import_resolution = any(
        item.name and item.name.upper() in dynamic_names for item in image.imports
    ) or any(
        name.upper() in dynamic_names
        for status in api_statuses if "import" in status
        for name in status.get("resolved_names", [])
    )
    has_win87em = any(module.upper() == "WIN87EM" for module in image.modules)

    static_blockers: list[str] = []
    if image.program_flags & 0x08:
        static_blockers.append("NE module flags mark this image protected-mode-only")
    if image.program_flags & 0x40:
        static_blockers.append("NE program flags declare 80386 instructions")
    elif image.program_flags & 0x20:
        static_blockers.append("NE program flags declare 80286 instructions")
    if image.target_os_id != 2:
        static_blockers.append(f"NE target OS is {image.target_os}, not Windows")
    if protected_modules:
        static_blockers.append("protected-mode dependency module(s): " + ", ".join(protected_modules))
    if disassembly["unsupported_instructions"]:
        first = disassembly["unsupported_instructions"][0]
        static_blockers.append(
            f"reachable {first['minimum_cpu']} instruction at segment {first['segment']}:{first['offset']:04X}"
        )
    if missing_apis:
        static_blockers.append("import(s) missing from supplied Windows 3.0 API reference: " + ", ".join(missing_apis))

    runtime_pass, runtime_error = _runtime_evidence(runtime_evidence, data, source)
    if static_blockers:
        verdict = "BLOCKED"
    elif runtime_pass:
        verdict = "COMPATIBLE"
    elif runtime_evidence is not None:
        verdict = "UNKNOWN"
    elif (
        not apis_verified
        or dynamic_import_resolution
        or disassembly["decode_failures"]
        or disassembly["instruction_classification_uncertainties"]
        or disassembly["relocation_affected_instructions"]
        or not disassembly["roots"]
    ):
        verdict = "UNKNOWN"
    elif disassembly["coprocessor_instructions"] and not has_win87em:
        verdict = "UNKNOWN"
    elif image.windows_version[0] > 3 or (image.windows_version[0] == 3 and image.windows_version[1] > 0):
        verdict = "UNKNOWN"
    else:
        verdict = "CANDIDATE"

    version_flag = f"{image.windows_version[0]}.{image.windows_version[1]}"
    if image.program_flags & 0x40:
        declared_minimum_cpu = "80386"
    elif image.program_flags & 0x20:
        declared_minimum_cpu = "80286"
    elif image.program_flags & 0x10:
        declared_minimum_cpu = "8086/8088"
    else:
        declared_minimum_cpu = "unspecified"
    result = {
        "input": {"path": source, "size_bytes": len(data)},
        "format": "NE",
        "windows_target": {
            "os": image.target_os,
            "os_id": image.target_os_id,
            "expected_windows_version_flag": version_flag,
            "program_flags": f"0x{image.program_flags:02X}",
            "application_flags": f"0x{image.application_flags:02X}",
            "declared_minimum_cpu": declared_minimum_cpu,
            "protected_mode_only": bool(image.program_flags & 0x08),
            "declared_8087_coprocessor": bool(image.program_flags & 0x80),
            "version_flag_is_not_compatibility_proof": True,
        },
        "modules": list(image.modules),
        "imports": [
            {
                "module": item.module,
                "name": item.name,
                "ordinal": item.ordinal,
                "kind": item.kind,
                "segment": item.segment,
                "source_offset": f"0x{item.source_offset:04X}",
                "source_type": item.source_type,
            }
            for item in image.imports
        ],
        "api_reference": {"directory": str(api_dir) if api_dir else None, "items": api_statuses,
                           "missing_3_0_apis": missing_apis, "all_imports_verified": apis_verified},
        "protected_mode_dependencies": protected_modules,
        "internal_dependencies": image.internal_relocations(),
        "dynamic_import_resolution_seen": dynamic_import_resolution,
        "software_87_emulator_module_imported": has_win87em,
        "cpu_analysis": disassembly,
        "static_blockers": static_blockers,
        "runtime_evidence": {"path": str(runtime_evidence) if runtime_evidence else None,
                              "accepted": runtime_pass, "error": runtime_error},
        "verdict": verdict,
        "verdict_notes": {
            "compatible": "requires explicit passing runtime evidence bound to this exact image and target run conditions",
            "candidate": "static checks found no known blocker; indirect control flow and code outside reachable roots remain incomplete",
            "blocked": "a specific static incompatibility was proven",
            "unknown": "static evidence or target API reference is insufficient",
        },
    }
    return result


def analyze_file(path: Path, api_dir: Path | None = None, runtime_evidence: Path | None = None) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise AnalyzerError(f"cannot read {path}: {exc}") from exc
    return analyze_bytes(data, str(path), api_dir, runtime_evidence)


def render_markdown(result: dict[str, Any]) -> str:
    target = result["windows_target"]
    cpu = result["cpu_analysis"]
    lines = [
        f"# W31CHECK report: {Path(result['input']['path']).name}",
        "",
        f"- Verdict: **{result['verdict']}**",
        f"- Input size: {result['input']['size_bytes']} bytes (host-side only)",
        f"- Format / target: {result['format']} / {target['os']}",
        f"- NE expected-Windows-version flag: {target['expected_windows_version_flag']} (not compatibility proof)",
        f"- NE program/application flags: {target['program_flags']} / {target['application_flags']}",
        f"- NE declared minimum CPU: {target['declared_minimum_cpu']}",
        f"- Protected-mode-only flag: {target['protected_mode_only']}",
        f"- Modules: {', '.join(result['modules']) or '(none declared)'}",
        f"- Reachable instructions decoded: {cpu['reachable_instruction_count']}",
        f"- Code-byte reachability: {cpu['code_bytes_reached']} bytes; incomplete by design",
        "",
        "## Referenced modules",
        "",
    ]
    module_rows = [item for item in result["api_reference"]["items"] if "import" not in item]
    import_rows = [item for item in result["api_reference"]["items"] if "import" in item]
    for item in module_rows:
        lines.append(f"- `{item['module']}` module: {item['status']} ({item['reference']})")
    if not module_rows:
        lines.append("- No module references or imports were recorded.")
    status_by_import = {
        (item["module"].upper(), item["import"]): (item["status"], item.get("resolved_names", []))
        for item in import_rows
    }
    lines.extend(["", "## Imports and Windows 3.0 API comparison", ""])
    for item in result["imports"]:
        symbol = item["name"] if item["kind"] == "name" else f"#{item['ordinal']}"
        status, resolved_names = status_by_import.get((item["module"].upper(), symbol), ("UNVERIFIED", []))
        resolved_suffix = (
            f" (export-name mapping: {', '.join(resolved_names)})"
            if item["kind"] == "ordinal" and resolved_names else ""
        )
        lines.append(
            f"- `{item['module']}!{symbol}`: {status} "
            f"(segment {item['segment']}:{item['source_offset']}, relocation type {item['source_type']})"
            f"{resolved_suffix}"
        )
    if not result["imports"]:
        lines.append("- No import relocations were recorded.")
    if result["api_reference"]["missing_3_0_apis"]:
        lines.append("")
        lines.append("Missing from the supplied Windows 3.0 reference: " + ", ".join(
            f"`{item}`" for item in result["api_reference"]["missing_3_0_apis"]
        ))
    lines.extend(["", "## Reachable newer-CPU instructions", ""])
    if cpu["unsupported_instructions"]:
        for item in cpu["unsupported_instructions"]:
            lines.append(
                f"- `{item['segment']}:{item['offset']:04X}` `{item['mnemonic']} {item['operands']}` "
                f"(requires {item['minimum_cpu']}; {item['reason']})"
            )
    else:
        lines.append("- None found in decoded reachable code.")
    lines.extend(["", "## Coprocessor instructions", ""])
    if cpu["coprocessor_instructions"]:
        lines.append(f"- {len(cpu['coprocessor_instructions'])} reachable 8087 instruction(s) found.")
        lines.append(
            f"- WIN87EM module imported: {result['software_87_emulator_module_imported']}; "
            "static analysis does not prove that emulation path works."
        )
    else:
        lines.append("- None found in decoded reachable code.")
    lines.extend(["", "## Internal and protected-mode dependencies", ""])
    lines.append(f"- Internal segment/OS fixups: {len(result['internal_dependencies'])}")
    lines.append(
        f"- Protected-mode dependency modules: {', '.join(result['protected_mode_dependencies']) or '(none found)'}"
    )
    lines.append(f"- Dynamic import lookup APIs imported: {result['dynamic_import_resolution_seen']}")
    lines.extend(["", "## Static reachability limits", ""])
    lines.append(f"- Entry table complete: {cpu['entry_table_complete']}")
    lines.append(f"- Unresolved control-flow edges: {len(cpu['unresolved_control_flow'])}")
    lines.append(f"- Decode failures: {len(cpu['decode_failures'])}")
    lines.append(f"- Relocation-affected instructions: {len(cpu['relocation_affected_instructions'])}")
    lines.append(f"- Instructions with imported-target fixups: {cpu['import_fixup_instruction_count']}")
    lines.append(
        f"- Unclassified instruction families: {len(cpu['instruction_classification_uncertainties'])}"
    )
    lines.append("- Static analysis is not a runtime compatibility result.")
    if result["static_blockers"]:
        lines.extend(["", "## Proven blockers", ""])
        lines.extend(f"- {reason}" for reason in result["static_blockers"])
    return "\r\n".join(lines) + "\r\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a Win16 NE EXE/DLL without executing it")
    parser.add_argument("image", type=Path, help="local NE executable or DLL")
    parser.add_argument("--api-dir", type=Path, help="complete local Windows 3.0 directory for export comparison")
    parser.add_argument("--runtime-evidence", type=Path, help="JSON runtime proof for a COMPATIBLE verdict")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path, help="write report to this host-side path")
    args = parser.parse_args(argv)
    try:
        result = analyze_file(args.image, args.api_dir, args.runtime_evidence)
    except (NEFormatError, AnalyzerError) as exc:
        print(f"W31CHECK: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2) + "\r\n" if args.format == "json" else render_markdown(result)
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\r\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
