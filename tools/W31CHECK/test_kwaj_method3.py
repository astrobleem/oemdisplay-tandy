"""Tests for the bounded, local-only KWAJ method-3 decoder."""

import os
import struct
import unittest
from pathlib import Path

from kwaj_method3 import (
    KWAJError,
    KWAJ_SIGNATURE,
    decompress_method3,
    parse_header,
    validate_mz_ne,
)


class _BitWriter:
    def __init__(self):
        self.bits = []

    def write(self, value, count):
        self.bits.extend((value >> shift) & 1 for shift in range(count - 1, -1, -1))

    def bytes(self):
        bits = self.bits[:]
        while len(bits) % 8:
            bits.append(0)
        result = bytearray()
        for offset in range(0, len(bits), 8):
            value = 0
            for bit in bits[offset : offset + 8]:
                value = (value << 1) | bit
            result.append(value)
        return bytes(result)


def _literal_stream(output):
    writer = _BitWriter()
    # All five symbol tables use the fixed-width encoding (type zero).
    for _ in range(6):
        writer.write(0, 4)
    for offset in range(0, len(output), 32):
        run = output[offset : offset + 32]
        writer.write(0, 4)  # MATCHLEN symbol zero: literal run follows.
        writer.write(len(run) - 1, 5)  # LITLEN stores run_length - 1.
        for value in run:
            writer.write(value, 8)
    return writer.bytes()


def _make_ne():
    image = bytearray(0x42)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 0x40)
    image[0x40:0x42] = b"NE"
    return bytes(image)


def _make_kwaj(output, *, declared_size=None, method=3, payload=None):
    encoded = _literal_stream(output) if payload is None else payload
    body = struct.pack("<I", len(output) if declared_size is None else declared_size) + encoded
    data_offset = 14 + 4
    return KWAJ_SIGNATURE + struct.pack("<HHH", method, data_offset, 0x0001) + body


class KWAJMethod3Tests(unittest.TestCase):
    def test_decodes_synthetic_literal_stream_and_validates_ne(self):
        expected = _make_ne()
        decoded, header = decompress_method3(_make_kwaj(expected))
        self.assertEqual(decoded, expected)
        self.assertEqual((header.method, header.expected_size), (3, len(expected)))
        validate_mz_ne(decoded)

    def test_rejects_bad_signature_and_unsupported_method(self):
        image = bytearray(_make_kwaj(_make_ne()))
        image[0] ^= 1
        with self.assertRaises(KWAJError):
            parse_header(bytes(image))
        with self.assertRaisesRegex(KWAJError, "unsupported KWAJ method"):
            decompress_method3(_make_kwaj(_make_ne(), method=4))

    def test_requires_declared_length_and_enforces_output_bound(self):
        no_length = KWAJ_SIGNATURE + struct.pack("<HHH", 3, 14, 0)
        with self.assertRaisesRegex(KWAJError, "declared output length"):
            parse_header(no_length)
        with self.assertRaisesRegex(KWAJError, "exceeds"):
            parse_header(_make_kwaj(_make_ne()), max_output_size=8)

    def test_rejects_truncated_payload_and_short_output(self):
        encoded = _make_kwaj(_make_ne())
        with self.assertRaises(KWAJError):
            decompress_method3(encoded[:-1])
        with self.assertRaises(KWAJError):
            decompress_method3(_make_kwaj(_make_ne(), declared_size=len(_make_ne()) + 1))

    def test_rejects_output_overrun_and_extra_compressed_bytes(self):
        expected = _make_ne()
        with self.assertRaisesRegex(KWAJError, "exceeds declared output"):
            decompress_method3(_make_kwaj(expected, declared_size=len(expected) - 1))
        with self.assertRaisesRegex(KWAJError, "trailing bytes"):
            decompress_method3(_make_kwaj(expected) + b"\0")

    def test_rejects_oversubscribed_huffman_tree(self):
        writer = _BitWriter()
        writer.write(3, 4)  # Explicit code lengths for MATCHLEN1.
        for _ in range(4):
            writer.write(0, 4)
        for _ in range(16):
            writer.write(1, 4)  # Sixteen one-bit codes oversubscribe this tree.
        for _ in range(5):
            writer.write(0, 4)
        malformed = _make_kwaj(b"X", payload=writer.bytes())
        with self.assertRaisesRegex(KWAJError, "oversubscribed"):
            decompress_method3(malformed)

    def test_rejects_non_ne_output(self):
        with self.assertRaisesRegex(KWAJError, "MZ executable"):
            validate_mz_ne(b"not an executable")
        no_ne = bytearray(0x42)
        no_ne[:2] = b"MZ"
        struct.pack_into("<I", no_ne, 0x3C, 0x40)
        with self.assertRaisesRegex(KWAJError, "no valid NE"):
            validate_mz_ne(bytes(no_ne))


@unittest.skipUnless(os.environ.get("W31CHECK_KWAJ_APPS_DIR"), "set W31CHECK_KWAJ_APPS_DIR to local KWAJ app copies")
class LocalKWAJMediaTests(unittest.TestCase):
    def test_windows_311_calc_and_notepad_decode_to_declared_mz_ne(self):
        root = Path(os.environ["W31CHECK_KWAJ_APPS_DIR"])
        expected = {
            "CALC.EX_": ("CALC", 43072, 27),
            "NOTEPAD.EX_": ("NOTEPAD", 32736, 30),
        }
        for name, (filename, size, data_offset) in expected.items():
            with self.subTest(application=name):
                source = (root / name).read_bytes()
                decoded, header = decompress_method3(source)
                self.assertEqual((header.filename, header.extension), (filename, "EXE"))
                self.assertEqual((header.expected_size, header.data_offset), (size, data_offset))
                self.assertEqual(len(decoded), size)
                validate_mz_ne(decoded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
