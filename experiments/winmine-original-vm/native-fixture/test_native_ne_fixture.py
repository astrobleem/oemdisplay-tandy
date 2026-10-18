from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT))

from build_ne_fixture import CALLBACK_CODE, ENTRY_CODE, build_fixture, validate_fixture
from ne_loader import NELoadError, NELoader
from tools.W31CHECK.w31check import NEFormatError
from test_vm8088 import bytecode_array


class NativeNEFixtureTests(unittest.TestCase):
    def test_generated_ne_resolves_both_named_imports_and_callback_segment(self) -> None:
        data = build_fixture()
        validate_fixture(data)
        loaded = NELoader.from_bytes(data, "fixture.ne").load()

        self.assertEqual(loaded.image.modules, ("KERNEL", "USER"))
        self.assertEqual(len(loaded.image.segments), 2)
        self.assertEqual([segment.minimum_allocation for segment in loaded.image.segments],
                         [0x0100, 0x0100])
        self.assertEqual(loaded.initial_cs, 0x1000)
        self.assertEqual(loaded.initial_ss, 0x2000)
        self.assertEqual(loaded.resolve_import(0xF001, 1).name, "GetVersion")
        self.assertEqual(loaded.resolve_import(0xF002, 1).name, "EnumWindows")

        entry_base = loaded.segment_selectors[1] << 4
        callback_base = loaded.segment_selectors[2] << 4
        entry = bytearray(ENTRY_CODE)
        entry[1:5] = bytes((1, 0, 1, 0xF0))
        entry[22:26] = bytes((1, 0, 2, 0xF0))
        self.assertEqual(loaded.memory[entry_base : entry_base + len(ENTRY_CODE)],
                         bytes(entry))
        self.assertEqual(loaded.memory[callback_base : callback_base + 6],
                         bytes((0x9A, 6, 0, 0, 0x20, 0xF4)))
        self.assertEqual(len(CALLBACK_CODE), 48)
        assembled_source = bytearray(bytecode_array("g_far_callback_bytecode"))
        assembled_source[1:5] = b"\0\0\0\0"
        self.assertEqual(CALLBACK_CODE, bytes(assembled_source))

    def test_bad_dos_or_ne_signature_fails_closed(self) -> None:
        original = build_fixture()
        for offset, value in ((0, ord("X")), (0x40, ord("X"))):
            with self.subTest(offset=offset):
                malformed = bytearray(original)
                malformed[offset] = value
                with self.assertRaises((NEFormatError, NELoadError)):
                    NELoader.from_bytes(bytes(malformed)).load()

    def test_bad_import_module_reference_fails_closed(self) -> None:
        malformed = bytearray(build_fixture())
        # Segment 1 starts at 0x100; its two relocation records follow its data.
        malformed[0x121:0x123] = (3).to_bytes(2, "little")
        with self.assertRaises((NEFormatError, NELoadError)):
            NELoader.from_bytes(bytes(malformed)).load()

    def test_unsupported_ne_source_type_fails_closed(self) -> None:
        malformed = bytearray(build_fixture())
        malformed[0x11D] = 7
        with self.assertRaisesRegex(NELoadError, "source type"):
            NELoader.from_bytes(bytes(malformed)).load()


if __name__ == "__main__":
    unittest.main()
