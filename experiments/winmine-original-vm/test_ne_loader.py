import unittest
from types import SimpleNamespace

from ne_loader import NELoadError, NELoader


def segment(number, data, relocations=()):
    return SimpleNamespace(number=number, data=data, minimum_allocation=len(data),
                           relocations=tuple(relocations))


def relocation(source_type, target_flags, source_offset, target1, target2,
               *, chain_sites=None, source_type_known=True):
    return {"source_type": source_type, "target_flags": target_flags,
            "source_offset": source_offset, "target1": target1, "target2": target2,
            "source_width": {0: 1, 2: 2, 3: 4, 5: 2}.get(source_type, 1),
            "source_type_known": source_type_known,
            "chain_sites": tuple(chain_sites if chain_sites is not None else (source_offset,))}


def image(code, code_relocations=(), modules=("KERNEL",), import_names=None):
    return SimpleNamespace(
        segment_count=2,
        segments=(segment(1, code, code_relocations), segment(2, b"data")),
        modules=modules,
        import_name_table=import_names or {},
        entry_points=(),
        initial_cs=1,
        initial_ip=0,
        initial_ss=2,
        initial_sp=0,
    )


class NELoaderTests(unittest.TestCase):
    def test_import_far_pointer_and_internal_selector_are_relocated(self):
        code = bytearray(8)
        code[0] = 0x9A
        code[1:5] = b"\0\0\0\0"
        code_relocations = (
            relocation(3, 1, 1, 1, 91),
            relocation(2, 0, 5, 2, 0),
        )
        loaded = NELoader(image(bytes(code), code_relocations)).load()
        self.assertEqual(loaded.segment_selectors, {1: 0x1000, 2: 0x2000})
        entry = loaded.memory[0x10000:0x10008]
        self.assertEqual(entry[1:5], b"\x01\x00\x01\xF0")
        self.assertEqual(int.from_bytes(entry[5:7], "little"), 0x2000)
        self.assertEqual(loaded.resolve_import(0xF001, 1).module, "KERNEL")
        target = loaded.resolve_import(0xF001, 1)
        self.assertEqual((target.kind, target.ordinal), ("ordinal", 91))

    def test_additive_offset_relocation_uses_existing_word_as_addend(self):
        code = bytearray(4)
        code[1:3] = (3).to_bytes(2, "little")
        r = relocation(5, 0x04, 1, 2, 0x34)
        loaded = NELoader(image(bytes(code), (r,))).load()
        self.assertEqual(loaded.memory[0x10001:0x10003], (0x37).to_bytes(2, "little"))

    def test_unknown_source_type_fails_closed(self):
        r = relocation(7, 1, 0, 1, 1, source_type_known=False)
        with self.assertRaisesRegex(NELoadError, "source type"):
            NELoader(image(b"\0\0", (r,))).load()

    def test_os_specific_target_fails_closed(self):
        r = relocation(2, 3, 0, 1, 1)
        with self.assertRaisesRegex(NELoadError, "OS-specific"):
            NELoader(image(b"\0\0", (r,))).load()

    def test_import_name_relocation_resolves_public_parser_name_table(self):
        code = bytearray(4)
        r = relocation(3, 2, 0, 1, 7)
        fake = image(bytes(code), (r,), import_names={7: "GetVersion"})
        loaded = NELoader(fake).load()
        target = loaded.resolve_import(0xF001, 1)
        self.assertEqual((target.module, target.kind, target.name), ("KERNEL", "name", "GetVersion"))

    def test_movable_entry_relocation_resolves_ordinal_to_segment_and_offset(self):
        code = bytearray(8)
        entry = SimpleNamespace(ordinal=1, segment=1, offset=0x0334)
        fake = image(bytes(code), (
            relocation(2, 0, 0, 0xFF, 1),
            relocation(5, 0, 2, 0xFF, 1),
        ))
        fake.entry_points = (entry,)
        loaded = NELoader(fake).load()
        self.assertEqual(int.from_bytes(loaded.memory[0x10000:0x10002], "little"), 0x1000)
        self.assertEqual(int.from_bytes(loaded.memory[0x10002:0x10004], "little"), 0x0334)


if __name__ == "__main__":
    unittest.main()

