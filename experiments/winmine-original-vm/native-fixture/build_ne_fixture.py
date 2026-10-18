"""Build a tiny first-party NE image for the native Win16 loader fixture.

The emitted image contains only 8088 fixture bytecode. It is a test input,
not an executable distribution or a Windows application.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ne_loader import NELoader


ENTRY_CODE = bytes((
    0x9A, 0, 0, 0, 0,       # CALL FAR KERNEL!GetVersion (NE relocation)
    0xB8, 0x57, 0x13, 0x50, # MOV AX,LPARAM high; PUSH AX
    0xB8, 0xDF, 0x9B, 0x50, # MOV AX,LPARAM low; PUSH AX
    0xB8, 0x00, 0x20, 0x50, # MOV AX,callback selector; PUSH AX
    0xB8, 0x00, 0x00, 0x50, # MOV AX,callback offset; PUSH AX
    0x9A, 0, 0, 0, 0,       # CALL FAR USER!EnumWindows (NE relocation)
    0xF4,                   # HLT
))

# MASM 5.10 bytes from W16CALL.ASM, with its internal CALL FAR selector
# supplied by an NE internal-segment relocation at byte 3.
CALLBACK_CODE = bytes((
    0x9A, 0x00, 0x00, 0x00, 0x00, 0xF4,
    0x55, 0x8B, 0xEC, 0x83, 0x7E, 0x0A, 0x00, 0x74, 0x1A,
    0x81, 0x7E, 0x06, 0xDF, 0x9B, 0x75, 0x13,
    0x81, 0x7E, 0x08, 0x57, 0x13, 0x75, 0x0C,
    0x83, 0xF9, 0x00, 0x75, 0x07,
    0xB8, 0x01, 0x00, 0x5D, 0xCA, 0x06, 0x00,
    0xB8, 0x00, 0x00, 0x5D, 0xCA, 0x06, 0x00,
))


def _u16(data: bytearray, offset: int, value: int) -> None:
    data[offset : offset + 2] = value.to_bytes(2, "little")


def _u32(data: bytearray, offset: int, value: int) -> None:
    data[offset : offset + 4] = value.to_bytes(4, "little")


def build_fixture() -> bytes:
    names = bytearray(b"\0")
    name_offsets: dict[str, int] = {}
    for name in ("KERNEL", "USER", "GetVersion", "EnumWindows"):
        encoded = name.encode("ascii")
        name_offsets[name] = len(names)
        names.append(len(encoded))
        names.extend(encoded)
    names.append(0)

    ne_offset = 0x40
    segment_table = 0x40
    module_table = segment_table + 16
    import_table = module_table + 4
    entry_offset = 0
    names_file_offset = ne_offset + import_table
    names_end = names_file_offset + len(names)
    entry_file_offset = 0x100
    callback_file_offset = 0x140
    alignment_shift = 4

    image = bytearray(callback_file_offset + len(CALLBACK_CODE))
    image[:2] = b"MZ"
    _u32(image, 0x3C, ne_offset)
    image[ne_offset : ne_offset + 2] = b"NE"
    image[ne_offset + 2 : ne_offset + 4] = bytes((5, 10))
    _u16(image, ne_offset + 4, entry_offset)
    _u16(image, ne_offset + 6, 0)
    _u16(image, ne_offset + 0x14, 0)
    _u16(image, ne_offset + 0x16, 1)
    _u16(image, ne_offset + 0x18, 0x0100)
    _u16(image, ne_offset + 0x1A, 2)
    _u16(image, ne_offset + 0x1C, 2)
    _u16(image, ne_offset + 0x1E, 2)
    _u16(image, ne_offset + 0x22, segment_table)
    _u16(image, ne_offset + 0x28, module_table)
    _u16(image, ne_offset + 0x2A, import_table)
    _u16(image, ne_offset + 0x32, alignment_shift)
    image[ne_offset + 0x36] = 2  # Windows target
    _u16(image, ne_offset + 0x3E, 0x0300)

    table = ne_offset + segment_table
    for index, (file_offset, data, flags) in enumerate((
        (entry_file_offset, ENTRY_CODE, 0x0100),
        (callback_file_offset, CALLBACK_CODE, 0x0100),
    )):
        row = table + index * 8
        _u16(image, row, file_offset >> alignment_shift)
        _u16(image, row + 2, len(data))
        _u16(image, row + 4, flags)
        _u16(image, row + 6, 0x0100)

    refs = ne_offset + module_table
    _u16(image, refs, name_offsets["KERNEL"])
    _u16(image, refs + 2, name_offsets["USER"])
    image[names_file_offset:names_end] = names

    image[entry_file_offset : entry_file_offset + len(ENTRY_CODE)] = ENTRY_CODE
    reloc = entry_file_offset + len(ENTRY_CODE)
    _u16(image, reloc, 2)
    # source=far pointer, target=import-by-name plus additive, site=CALL operand
    image[reloc + 2 : reloc + 10] = bytes((3, 6)) + (1).to_bytes(2, "little") + (1).to_bytes(2, "little") + name_offsets["GetVersion"].to_bytes(2, "little")
    image[reloc + 10 : reloc + 18] = bytes((3, 6)) + (22).to_bytes(2, "little") + (2).to_bytes(2, "little") + name_offsets["EnumWindows"].to_bytes(2, "little")

    image[callback_file_offset : callback_file_offset + len(CALLBACK_CODE)] = CALLBACK_CODE
    reloc = callback_file_offset + len(CALLBACK_CODE)
    _u16(image, reloc, 1)
    # source=far pointer, target=internal segment 2, offset 6, additive
    image[reloc + 2 : reloc + 10] = bytes((3, 4)) + (1).to_bytes(2, "little") + (2).to_bytes(2, "little") + (6).to_bytes(2, "little")
    return bytes(image)


def validate_fixture(image: bytes) -> None:
    loaded = NELoader.from_bytes(image, "<first-party fixture>").load()
    if len(loaded.image.segments) != 2 or loaded.image.modules != ("KERNEL", "USER"):
        raise ValueError("unexpected first-party NE fixture tables")
    entry = loaded.memory[loaded.segment_selectors[1] << 4 : (loaded.segment_selectors[1] << 4) + len(ENTRY_CODE)]
    callback = loaded.memory[loaded.segment_selectors[2] << 4 : (loaded.segment_selectors[2] << 4) + len(CALLBACK_CODE)]
    if entry[:5] != bytes((0x9A, 1, 0, 1, 0xF0)):
        raise ValueError("KERNEL!GetVersion import relocation did not resolve")
    if entry[21:26] != bytes((0x9A, 1, 0, 2, 0xF0)):
        raise ValueError("USER!EnumWindows import relocation did not resolve")
    if callback[1:5] != bytes((6, 0, 0, 0x20)):
        raise ValueError("callback internal far-call relocation did not resolve")
    if len(loaded.import_targets) != 2:
        raise ValueError("unexpected NE import resolution table")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    image = build_fixture()
    validate_fixture(image)
    args.output.write_bytes(image)
    import hashlib

    print(f"NE_FIXTURE_BYTES={len(image)}")
    print(f"NE_FIXTURE_SHA256={hashlib.sha256(image).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
