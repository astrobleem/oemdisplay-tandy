#!/usr/bin/env python3
"""Independent BI_RLE4/BI_RLE8 fixtures and bounded-stream tests.

The tiny BMPs are decoded by Pillow's BMP plugin, independently of the driver
implementation. The expected index rows are hand-authored uncompressed
oracles in top-down display order.
"""
from __future__ import annotations

import io
import struct
import unittest
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("RLETEST requires Pillow for the independent BMP oracle") from exc


RLE8_ROWS_TOP = (
    (12, 12, 12, 12, 12, 12, 12),
    (5, 6, 7, 8, 9, 10, 11),
    (1, 1, 1, 2, 3, 4, 4),
)
RLE8_STREAM = bytes((
    3, 1, 1, 2, 1, 3, 2, 4, 0, 0,
    0, 7, 5, 6, 7, 8, 9, 10, 11, 0, 0, 0,
    7, 12, 0, 0, 0, 1,
))

RLE8_DELTA_ROWS_TOP = (
    (3, 3, 3, 3, 3, 3),
    (0, 0, 0, 0, 2, 2),
    (1, 1, 0, 0, 0, 0),
)
RLE8_DELTA_STREAM = bytes((
    2, 1, 0, 2, 2, 1, 2, 2, 0, 0,
    6, 3, 0, 0, 0, 1,
))

# A one-row delta has rsSkip=0 and nonzero deltaX. In RLESTATE the pending
# vertical-row count is one byte at 27, immediately before deltaX at 28. A
# word read of rsSkip folds deltaX's low byte into the pending-row test.
RLE8_PENDING_DELTA_ROWS_TOP = (
    (0, 0, 0, 0, 7),
    (5, 5, 0, 0, 0),
)
RLE8_PENDING_DELTA_STREAM = bytes((
    2, 5,                    # two pixels on the bottom scan
    0, 2, 2, 1,               # dx=2, dy=1: rsSkip=0, deltaX=2
    1, 7, 0, 0,               # paint x=4 on the target scan, then EOL
    0, 1,                    # EOB
))

RLE4_ROWS_TOP = (
    (6, 7, 8, 9, 10, 0, 0, 0, 0),
    (1, 2, 1, 2, 1, 3, 4, 5, 0),
)
RLE4_STREAM = bytes((
    5, 0x12, 0, 4, 0x34, 0x50, 0, 0,
    0, 5, 0x67, 0x89, 0xA0, 0, 0, 0, 0, 1,
))


def target_app_fixture(bits: int) -> tuple[bytes, tuple[tuple[int, ...], ...]]:
    """Build the exact 37x11 streams and BI_RGB rows used by MODETEST.C."""
    width, height = 37, 11

    def value(x: int, scan: int) -> int:
        if bits == 8 and scan == 1:
            return 0
        if bits == 8 and scan == 0 and x < 2:
            return 0
        if bits == 8 and scan == 0 and x < 6:
            return 1
        if x < 4:
            return ((scan + 1) & 15) if bits == 8 else (2 if x & 1 else 1)
        return (x * 3 + (height - 1 - scan) * 5) & 15

    stream = bytearray()
    bottom = []
    for scan in range(height):
        row = [value(x, scan) for x in range(width)]
        bottom.append(row)
        if bits == 8 and scan == 1:
            stream.extend((0, 2, 0, 1))  # delta-Y leaves this row zero
            continue
        if bits == 8 and scan == 0:
            stream.extend((0, 2, 2, 0, 4, 1, 0, 31))  # delta-X, encoded, absolute
            stream.extend(row[6:])
            stream.extend((0, 0, 0))  # absolute pad, EOL
            continue
        stream.extend((4, ((scan + 1) & 15) if bits == 8 else 0x12, 0, 33))
        if bits == 8:
            stream.extend(row[4:])
            stream.append(0)  # 33-byte absolute payload padding
        else:
            for x in range(4, width, 2):
                low = row[x + 1] if x + 1 < width else 0
                stream.append((row[x] << 4) | low)
            if (33 + 1) // 2 & 1:
                stream.append(0)  # 17-byte packed absolute payload padding
        stream.extend((0, 0))  # EOL
    stream.extend((0, 1))  # EOB
    expected = tuple(tuple(row) for row in reversed(bottom))
    return bytes(stream), expected


def make_bmp(width: int, height: int, bits: int, compression: int,
             stream: bytes, *, image_size: int | None = None) -> bytes:
    """Wrap a compact RLE byte stream in a Windows 3.x BMP header."""
    if bits not in (4, 8):
        raise ValueError("fixtures only cover indexed RLE4/RLE8")
    if (compression, bits) not in ((1, 8), (2, 4)):
        raise ValueError("BI_RLE8 requires 8bpp and BI_RLE4 requires 4bpp")
    colors = 1 << bits
    palette = b"".join(bytes((i, i, i, 0)) for i in range(colors))
    size_image = len(stream) if image_size is None else image_size
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, bits,
                       compression, size_image, 0, 0, colors, 0)
    pixel_offset = 14 + len(info) + len(palette)
    total = pixel_offset + len(stream)
    file_header = b"BM" + struct.pack("<IHHI", total, 0, 0, pixel_offset)
    return file_header + info + palette + stream


def make_uncompressed_bmp(rows_top: tuple[tuple[int, ...], ...],
                          bits: int) -> bytes:
    """Pack an independent BI_RGB BMP oracle for indexed pixel rows."""
    height = len(rows_top)
    width = len(rows_top[0])
    if bits not in (4, 8) or any(len(row) != width for row in rows_top):
        raise ValueError("invalid indexed oracle rows")
    packed_rows = []
    for row in reversed(rows_top):
        if bits == 8:
            payload = bytes(row)
        else:
            payload = bytes((row[i] << 4) | (row[i + 1] if i + 1 < width else 0)
                            for i in range(0, width, 2))
        stride = (width * bits + 31) // 32 * 4
        packed_rows.append(payload + bytes(stride - len(payload)))
    pixels = b"".join(packed_rows)
    colors = 1 << bits
    palette = b"".join(bytes((i, i, i, 0)) for i in range(colors))
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, bits,
                       0, len(pixels), 0, 0, colors, 0)
    pixel_offset = 14 + len(info) + len(palette)
    total = pixel_offset + len(pixels)
    file_header = b"BM" + struct.pack("<IHHI", total, 0, 0, pixel_offset)
    return file_header + info + palette + pixels


def pillow_indices(bmp: bytes) -> tuple[tuple[int, ...], ...]:
    with Image.open(io.BytesIO(bmp)) as image:
        image.load()
        return tuple(tuple(int(image.getpixel((x, y))) for x in range(image.width))
                     for y in range(image.height))


def reference_decode(width: int, height: int, bits: int, compression: int,
                    source: bytes | bytearray, *, size_image: int | None = None,
                    palette_colors: int | None = None
                    ) -> tuple[tuple[int, ...], ...]:
    """Spec-driven oracle that bounds every read by the declared stream size."""
    if width <= 0 or height <= 0 or width > 32767 or height > 32767:
        raise ValueError("invalid dimensions")
    if (compression, bits) not in ((1, 8), (2, 4)):
        raise ValueError("invalid RLE compression/depth pair")
    maximum_colors = 1 << bits
    if palette_colors is None:
        palette_colors = maximum_colors
    if not 0 < palette_colors <= maximum_colors:
        raise ValueError("invalid palette size")
    limit = len(source) if size_image is None else size_image
    if limit <= 0 or limit > len(source):
        raise ValueError("invalid biSizeImage")
    pos = x = y = 0
    bottom_up = [[0] * width for _ in range(height)]
    ended = False

    def take(count: int) -> bytes:
        nonlocal pos
        if count < 0 or pos > limit or count > limit - pos:
            raise ValueError("truncated RLE stream")
        result = bytes(source[pos:pos + count])
        pos += count
        return result

    def emit(values: tuple[int, ...]) -> None:
        nonlocal x
        if y >= height or x + len(values) > width:
            raise ValueError("RLE run outside bitmap")
        for value in values:
            if value >= palette_colors:
                raise ValueError("RLE palette index out of range")
            bottom_up[y][x] = value
            x += 1

    while not ended:
        count, value = take(2)
        if count:
            if bits == 8:
                emit((value,) * count)
            else:
                pair = (value >> 4, value & 15)
                emit(tuple(pair[i & 1] for i in range(count)))
        elif value == 0:  # end of line
            if y >= height:
                raise ValueError("end of line past bitmap")
            x = 0
            y += 1
        elif value == 1:  # end of bitmap
            ended = True
        elif value == 2:  # delta
            dx, dy = take(2)
            if x + dx > width or y + dy >= height:
                raise ValueError("delta outside bitmap")
            x += dx
            y += dy
        else:  # absolute mode
            n = value
            nbytes = n if bits == 8 else (n + 1) // 2
            packed = take(nbytes)
            if nbytes & 1:
                take(1)  # align the run to a 16-bit word boundary
            if bits == 8:
                emit(tuple(packed))
            else:
                emit(tuple((packed[i // 2] >> (4 if i % 2 == 0 else 0)) & 15
                           for i in range(n)))
    return tuple(tuple(row) for row in reversed(bottom_up))


def read_bounded(memory: bytes | bytearray, base: int, size: int,
                 position: int, count: int) -> bytes:
    """Model a huge-pointer byte read while honoring biSizeImage exactly."""
    if position < 0 or count < 0 or position > size or count > size - position:
        raise ValueError("RLE input exceeds biSizeImage")
    start = base + position
    end = start + count
    if end > len(memory):
        raise ValueError("RLE input exceeds supplied buffer")
    return bytes(memory[start:end])


class IndependentOracleTests(unittest.TestCase):
    def test_rle8_mixed_encoded_absolute_and_word_padding(self) -> None:
        bmp = make_bmp(7, 3, 8, 1, RLE8_STREAM)
        self.assertEqual(pillow_indices(bmp), RLE8_ROWS_TOP)
        self.assertEqual(reference_decode(7, 3, 8, 1, RLE8_STREAM),
                         RLE8_ROWS_TOP)

    def test_rle8_delta_and_partial_rows(self) -> None:
        self.assertEqual(reference_decode(6, 3, 8, 1, RLE8_DELTA_STREAM),
                         RLE8_DELTA_ROWS_TOP)

    def test_rle8_pending_delta_does_not_read_delta_x_as_skip_count(self) -> None:
        decoded = reference_decode(5, 2, 8, 1, RLE8_PENDING_DELTA_STREAM)
        self.assertEqual(decoded, RLE8_PENDING_DELTA_ROWS_TOP)
        # Use Pillow's independent uncompressed BMP path as the pixel oracle.
        self.assertEqual(pillow_indices(make_uncompressed_bmp(
            RLE8_PENDING_DELTA_ROWS_TOP, 8)), RLE8_PENDING_DELTA_ROWS_TOP)
        source = Path(__file__).with_name("RLE88.ASM").read_text()
        self.assertIn("cmp byte ptr es:[di+rsSkip],0", source)
        self.assertNotIn("mov ax,es:[di+rsSkip]", source)

    def test_rle4_alternating_nibbles_and_odd_absolute_padding(self) -> None:
        decoded = reference_decode(9, 2, 4, 2, RLE4_STREAM)
        self.assertEqual(decoded, RLE4_ROWS_TOP)
        # Pillow's 4bpp BI_RGB path is broken too, so store the same index
        # values in an independent 8bpp BI_RGB oracle for its BMP decoder.
        self.assertEqual(pillow_indices(make_uncompressed_bmp(RLE4_ROWS_TOP, 8)),
                         decoded)

    def test_target_app_rle4_rle8_fixtures_match_independent_oracle(self) -> None:
        for bits, compression, size in ((8, 1, 408), (4, 2, 266)):
            with self.subTest(bits=bits):
                stream, expected = target_app_fixture(bits)
                self.assertEqual(len(stream), size)
                decoded = reference_decode(37, 11, bits, compression, stream)
                self.assertEqual(decoded, expected)
                self.assertEqual(pillow_indices(make_uncompressed_bmp(expected, 8)),
                                 expected)

    def test_rle8_early_eob_leaves_remaining_pixels_zero(self) -> None:
        stream = bytes((2, 9, 0, 1))
        expected = ((0, 0, 0, 0), (9, 9, 0, 0))
        self.assertEqual(reference_decode(4, 2, 8, 1, stream), expected)
        self.assertEqual(pillow_indices(make_uncompressed_bmp(expected, 8)),
                         expected)

    def test_scan_band_and_clipping_oracle(self) -> None:
        rows = pillow_indices(make_bmp(7, 3, 8, 1, RLE8_STREAM))
        # Windows scan numbers count from the bottom of an RLE DIB.
        start, count = 1, 1
        band = tuple(rows[len(rows) - 1 - (start + k)] for k in range(count))
        self.assertEqual(band, ((5, 6, 7, 8, 9, 10, 11),))
        # Pixel clipping must preserve the decoded source columns.
        self.assertEqual(tuple(band[0][2:6]), (7, 8, 9, 10))

    def test_size_image_bounds_reads_across_64k_segment_boundary(self) -> None:
        base = 0xFFFE
        memory = bytearray(base + len(RLE8_STREAM) + 4)
        memory[base:base + len(RLE8_STREAM)] = RLE8_STREAM
        self.assertEqual(read_bounded(memory, base, len(RLE8_STREAM), 0,
                                      len(RLE8_STREAM)), RLE8_STREAM)
        with self.assertRaises(ValueError):
            read_bounded(memory, base, len(RLE8_STREAM) - 1, 0,
                         len(RLE8_STREAM))
        with self.assertRaises(ValueError):
            read_bounded(memory, base, len(RLE8_STREAM), len(RLE8_STREAM), 1)

    def test_source_buffer_is_immutable(self) -> None:
        stream = bytearray(RLE4_STREAM)
        before = bytes(stream)
        self.assertEqual(reference_decode(9, 2, 4, 2, stream),
                         RLE4_ROWS_TOP)
        self.assertEqual(bytes(stream), before)

    def test_truncated_payload_is_rejected_at_declared_size(self) -> None:
        # Keep the full source bytes present after the declared bound: the
        # decoder must not treat those sentinel bytes as compressed payload.
        with self.assertRaises(ValueError):
            reference_decode(7, 3, 8, 1, RLE8_STREAM,
                             size_image=len(RLE8_STREAM) - 1)

    def test_malformed_runs_and_coordinates_are_rejected(self) -> None:
        malformed = (
            (4, 1, 8, 1, bytes((5, 1, 0, 1))),
            (4, 1, 8, 1, bytes((0, 3, 1, 2))),
            (4, 1, 8, 1, bytes((1, 1, 0, 2, 1, 0))),
            (4, 1, 8, 1, bytes((1, 1, 0, 2, 4, 0, 0, 1))),
            (4, 1, 8, 1, bytes((1, 1, 0, 0))),
            (4, 1, 4, 2, bytes((0, 5, 0x12, 0x34, 0x50))),
            (4, 1, 4, 2, bytes((0, 5, 0x12, 0x34, 0x50, 0))),
            (4, 1, 8, 1, bytes((0, 2, 0))),
            (4, 1, 8, 1, bytes((0, 0, 0, 0, 0, 1))),
        )
        for width, height, bits, compression, stream in malformed:
            with self.subTest(stream=stream), self.assertRaises(ValueError):
                reference_decode(width, height, bits, compression, stream)

    def test_bad_compression_depth_pair_is_not_a_valid_fixture(self) -> None:
        # BI_RLE8 is defined for 8bpp and BI_RLE4 for 4bpp only.
        with self.assertRaises(ValueError):
            make_bmp(4, 1, 4, 1, bytes((4, 1, 0, 1)))

    def test_short_palette_and_bad_palette_sizes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            reference_decode(1, 1, 8, 1, bytes((1, 2, 0, 1)), palette_colors=2)
        with self.assertRaises(ValueError):
            reference_decode(1, 1, 4, 2, bytes((1, 0xF0, 0, 1)), palette_colors=15)
        for palette_colors in (0, 17):
            with self.subTest(palette_colors=palette_colors), self.assertRaises(ValueError):
                reference_decode(1, 1, 4, 2, bytes((1, 0x10, 0, 1)),
                                 palette_colors=palette_colors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
