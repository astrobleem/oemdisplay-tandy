#!/usr/bin/env python3
"""Bounded KWAJ method-3 decoder for local Windows NE evidence.

This decoder accepts only KWAJ method 3 with a declared output length and
returns only a size-checked MZ/NE executable. It never executes input files.
The bitstream implementation follows the published KWAJ format description;
it does not embed or copy libmspack code.
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


KWAJ_SIGNATURE = bytes.fromhex("4B 57 41 4A 88 F0 27 D1")
KWAJ_HEADER_SIZE = 14
WINDOW_SIZE = 4096
WINDOW_MASK = WINDOW_SIZE - 1
MAX_INPUT_SIZE = 8 * 1024 * 1024
MAX_OUTPUT_SIZE = 16 * 1024 * 1024


class KWAJError(ValueError):
    """The KWAJ file is malformed, unsupported, or exceeds a safety bound."""


@dataclass(frozen=True)
class KWAJHeader:
    method: int
    data_offset: int
    flags: int
    expected_size: int
    filename: str | None
    extension: str | None


def _u16(data: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise KWAJError(f"truncated {label}")
    return struct.unpack_from("<H", data, offset)[0]


def _read_cstring(data: bytes, offset: int, limit: int, max_chars: int, label: str) -> tuple[str, int]:
    end = min(limit, offset + max_chars + 1)
    nul = data.find(b"\0", offset, end)
    if nul < 0:
        raise KWAJError(f"missing or overlong {label} extension")
    return data[offset:nul].decode("cp437", errors="replace"), nul + 1


def parse_header(data: bytes, *, max_output_size: int = MAX_OUTPUT_SIZE) -> KWAJHeader:
    if len(data) > MAX_INPUT_SIZE:
        raise KWAJError(f"input exceeds {MAX_INPUT_SIZE} byte limit")
    if len(data) < KWAJ_HEADER_SIZE:
        raise KWAJError("truncated KWAJ fixed header")
    if data[:8] != KWAJ_SIGNATURE:
        raise KWAJError("invalid KWAJ signature")

    method = _u16(data, 8, "compression method")
    data_offset = _u16(data, 10, "compressed-data offset")
    flags = _u16(data, 12, "header flags")
    if method != 3:
        raise KWAJError(f"unsupported KWAJ method {method}; only method 3 is implemented")
    if flags & ~0x003F:
        raise KWAJError(f"unknown KWAJ header flag bits 0x{flags & ~0x003F:04X}")
    if data_offset < KWAJ_HEADER_SIZE or data_offset > len(data):
        raise KWAJError("compressed-data offset is outside the input")

    cursor = KWAJ_HEADER_SIZE
    expected_size: int | None = None
    filename: str | None = None
    extension: str | None = None

    if flags & 0x0001:
        if cursor + 4 > data_offset:
            raise KWAJError("truncated declared output length")
        expected_size = struct.unpack_from("<I", data, cursor)[0]
        cursor += 4
    if flags & 0x0002:
        if cursor + 2 > data_offset:
            raise KWAJError("truncated KWAJ unknown header field")
        cursor += 2
    if flags & 0x0004:
        size = _u16(data, cursor, "KWAJ unknown-field size")
        cursor += 2
        if cursor + size > data_offset:
            raise KWAJError("truncated KWAJ unknown field")
        cursor += size
    if flags & 0x0008:
        filename, cursor = _read_cstring(data, cursor, data_offset, 8, "filename")
    if flags & 0x0010:
        extension, cursor = _read_cstring(data, cursor, data_offset, 3, "extension")
    if flags & 0x0020:
        size = _u16(data, cursor, "KWAJ text-field size")
        cursor += 2
        if cursor + size > data_offset:
            raise KWAJError("truncated KWAJ text field")
        cursor += size
    if cursor > data_offset:
        raise KWAJError("KWAJ header extensions overlap compressed data")
    if expected_size is None:
        raise KWAJError("method 3 requires a declared output length for bounded decoding")
    if expected_size <= 0:
        raise KWAJError("declared output length must be positive")
    if expected_size > max_output_size:
        raise KWAJError(f"declared output exceeds {max_output_size} byte limit")

    return KWAJHeader(method, data_offset, flags, expected_size, filename, extension)


class _BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.bitpos = 0

    @property
    def remaining_bits(self) -> int:
        return len(self.data) * 8 - self.bitpos

    def read(self, count: int) -> int:
        if count < 0 or self.bitpos + count > len(self.data) * 8:
            raise KWAJError("truncated KWAJ bitstream")
        value = 0
        for _ in range(count):
            byte = self.data[self.bitpos >> 3]
            value = (value << 1) | ((byte >> (7 - (self.bitpos & 7))) & 1)
            self.bitpos += 1
        return value


def _read_code_lengths(reader: _BitReader, encoding: int, symbol_count: int) -> list[int]:
    if encoding == 0:
        length = {16: 4, 32: 5, 64: 6, 256: 8}.get(symbol_count)
        if length is None:
            raise KWAJError("invalid fixed Huffman alphabet size")
        return [length] * symbol_count

    lengths = [reader.read(4)]
    for _ in range(1, symbol_count):
        previous = lengths[-1]
        if encoding == 1:
            first = reader.read(1)
            if first == 0:
                current = previous
            elif reader.read(1) == 0:
                current = previous + 1
            else:
                current = reader.read(4)
        elif encoding == 2:
            selector = reader.read(2)
            current = reader.read(4) if selector == 3 else previous + selector - 1
        elif encoding == 3:
            current = reader.read(4)
        else:
            raise KWAJError(f"invalid Huffman length encoding {encoding}")
        if not 0 <= current <= 15:
            raise KWAJError("Huffman code length is outside 0..15")
        lengths.append(current)
    return lengths


class _Huffman:
    def __init__(self, lengths: list[int]):
        if not lengths or any(length < 0 or length > 15 for length in lengths):
            raise KWAJError("invalid Huffman lengths")
        self.counts = [0] * 16
        for length in lengths:
            if length:
                self.counts[length] += 1
        self.max_length = max((i for i, count in enumerate(self.counts) if count), default=0)
        if self.max_length == 0:
            raise KWAJError("empty Huffman tree")

        free_codes = 1
        for length in range(1, 16):
            free_codes = (free_codes << 1) - self.counts[length]
            if free_codes < 0:
                raise KWAJError("oversubscribed Huffman tree")

        next_code = [0] * 16
        code = 0
        for length in range(1, 16):
            code = (code + self.counts[length - 1]) << 1
            next_code[length] = code
        self.codes: dict[tuple[int, int], int] = {}
        for symbol, length in enumerate(lengths):
            if length:
                symbol_code = next_code[length]
                next_code[length] += 1
                self.codes[(length, symbol_code)] = symbol

    def read_symbol(self, reader: _BitReader) -> int:
        code = 0
        for length in range(1, self.max_length + 1):
            code = (code << 1) | reader.read(1)
            symbol = self.codes.get((length, code))
            if symbol is not None:
                return symbol
        raise KWAJError("bitstream has no matching Huffman code")


def _read_trees(reader: _BitReader) -> tuple[_Huffman, _Huffman, _Huffman, _Huffman, _Huffman]:
    encodings = [reader.read(4) for _ in range(6)]
    if any(kind > 3 for kind in encodings[:5]):
        raise KWAJError("invalid KWAJ Huffman table encoding")
    # The sixth nibble is padding according to the KWAJ method-3 format.
    sizes = (16, 16, 32, 64, 256)
    trees = []
    for encoding, count in zip(encodings, sizes):
        trees.append(_Huffman(_read_code_lengths(reader, encoding, count)))
    return tuple(trees)  # type: ignore[return-value]


def decompress_method3(data: bytes, *, max_output_size: int = MAX_OUTPUT_SIZE) -> tuple[bytes, KWAJHeader]:
    """Decode one method-3 KWAJ file under strict input/output bounds."""
    header = parse_header(data, max_output_size=max_output_size)
    reader = _BitReader(data[header.data_offset :])
    matchlen1, matchlen2, litlen, offset_tree, literals = _read_trees(reader)
    ring = bytearray(b" " * WINDOW_SIZE)
    ring_pos = 0
    output = bytearray()
    after_short_literal_run = False

    while len(output) < header.expected_size:
        matchlen_tree = matchlen2 if after_short_literal_run else matchlen1
        code = matchlen_tree.read_symbol(reader)
        if code:
            run_length = code + 2
            if len(output) + run_length > header.expected_size:
                raise KWAJError("match exceeds declared output length")
            distance = (offset_tree.read_symbol(reader) << 6) | reader.read(6)
            for _ in range(run_length):
                value = ring[(ring_pos - distance) & WINDOW_MASK]
                ring[ring_pos] = value
                ring_pos = (ring_pos + 1) & WINDOW_MASK
                output.append(value)
            after_short_literal_run = False
        else:
            run_length = litlen.read_symbol(reader) + 1
            if len(output) + run_length > header.expected_size:
                raise KWAJError("literal run exceeds declared output length")
            after_short_literal_run = run_length != 32
            for _ in range(run_length):
                value = literals.read_symbol(reader)
                ring[ring_pos] = value
                ring_pos = (ring_pos + 1) & WINDOW_MASK
                output.append(value)

    used_bytes = (reader.bitpos + 7) // 8
    if used_bytes != len(reader.data):
        raise KWAJError("compressed stream has trailing bytes after the declared output")
    # Method 3 has no explicit EOF code. The header's declared size is the
    # output boundary; any unused bits in its final byte are padding.
    if len(output) != header.expected_size:
        raise KWAJError("decoded size does not match the KWAJ header")
    return bytes(output), header


def validate_mz_ne(data: bytes) -> None:
    if len(data) < 0x42 or data[:2] != b"MZ":
        raise KWAJError("decoded output is not a complete MZ executable")
    ne_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if ne_offset < 0x40 or ne_offset + 2 > len(data) or data[ne_offset : ne_offset + 2] != b"NE":
        raise KWAJError("decoded MZ output has no valid NE header")


def decode_file(source: Path, destination: Path) -> KWAJHeader:
    if source.stat().st_size > MAX_INPUT_SIZE:
        raise KWAJError(f"input exceeds {MAX_INPUT_SIZE} byte limit")
    data = source.read_bytes()
    if len(data) > MAX_INPUT_SIZE:
        raise KWAJError(f"input exceeds {MAX_INPUT_SIZE} byte limit")
    output, header = decompress_method3(data)
    validate_mz_ne(output)
    if not destination.parent.is_dir():
        raise KWAJError("output directory must already exist")
    try:
        with destination.open("xb") as stream:
            stream.write(output)
    except FileExistsError as exc:
        raise KWAJError(f"refusing to overwrite existing output: {destination}") from exc
    return header


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Decode bounded KWAJ method-3 Windows NE evidence")
    parser.add_argument("input", type=Path, help="local KWAJ method-3 input")
    parser.add_argument("output", type=Path, help="new output path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        header = decode_file(args.input, args.output)
    except (OSError, KWAJError) as exc:
        print(f"kwaj_method3: {exc}", file=sys.stderr)
        return 1
    print(f"decoded {header.filename or ''}{'.' + header.extension if header.extension else ''}")
    print(f"method={header.method} expected_bytes={header.expected_size} data_offset={header.data_offset}")
    print(f"validated=MZ+NE output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
