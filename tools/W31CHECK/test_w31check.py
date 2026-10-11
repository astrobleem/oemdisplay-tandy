"""Synthetic NE/parser tests plus an opt-in host-side real-media smoke test."""

import json
import hashlib
import os
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from w31check import NEFormatError, NEImage, _cpu_requirement, analyze_bytes


def _pstring(value):
    raw = value.encode("ascii")
    return bytes([len(raw)]) + raw


def runtime_evidence(image, filename="PASS.EXE"):
    return {
        "schema": "w31check-runtime-v1",
        "result": "PASS",
        "image": {
            "filename": filename,
            "size_bytes": len(image),
            "sha256": hashlib.sha256(image).hexdigest(),
        },
        "target": {
            "windows": "3.0", "mode": "real", "cpu": "8088", "memory_kb": 640,
            "display": "320x200x16",
        },
        "actions": {
            "input": True, "representative_task": True, "redraw": True, "clean_exit": True,
        },
    }


def make_ne(
    *,
    code=b"\x90\xCB",
    imports=(),
    internal_fixups=(),
    exports=(),
    flags=0,
    application_flags=0,
    windows_version=0x0300,
    target_os=2,
    include_fixed_entry=True,
):
    """Build a small DOS-wrapped NE with one optional code segment."""
    ne_offset = 0x40
    segment_table_offset = 0x40
    segment_data_offset = 0xA0
    segment_count = 1 if code is not None else 0
    code_data = bytearray(code) if code is not None else None
    modules = []
    for module, _symbol, _kind in imports:
        if module.upper() not in {item.upper() for item in modules}:
            modules.append(module)
    imported_names = []
    for _module, symbol, kind in imports:
        if kind == "name" and symbol not in imported_names:
            imported_names.append(symbol)
    name_table = bytearray(b"\0")  # NE import-name-table offset zero is reserved.
    name_offsets = {}
    for value in modules + imported_names:
        name_offsets[value.upper()] = len(name_table)
        name_table.extend(_pstring(value))
    name_table.append(0)

    relocations = bytearray()
    for _index, (module, symbol, kind) in enumerate(imports):
        target_flags = (1 if kind == "ordinal" else 2) | 0x04
        target2 = int(symbol) if kind == "ordinal" else name_offsets[symbol.upper()]
        source_offset = len(code_data)
        code_data.extend(b"\0\0")
        relocations.extend(
            struct.pack("<BBHHH", 5, target_flags, source_offset, modules.index(module) + 1, target2)
        )
    for source_offset, target_segment, target_offset in internal_fixups:
        relocations.extend(struct.pack("<BBHHH", 5, 0x04, source_offset, target_segment, target_offset))
    relocation_count = len(imports) + len(internal_fixups)
    relocation_data = struct.pack("<H", relocation_count) + relocations if code is not None else b""

    entry_table = bytes([1, 1, 0, 0, 0, 0]) if include_fixed_entry and code is not None else b"\0"
    resident_names = bytearray(_pstring("TESTMOD") + struct.pack("<H", 0))
    for index, export in enumerate(exports, 1):
        ordinal, name = export if isinstance(export, tuple) else (index, export)
        resident_names.extend(_pstring(name) + struct.pack("<H", ordinal))
    resident_names.append(0)

    entry_table_offset = (
        segment_data_offset - ne_offset
        if code_data is None
        else segment_data_offset + len(code_data) + len(relocation_data) - ne_offset
    )
    resident_names_offset = entry_table_offset + len(entry_table)
    module_table_offset = resident_names_offset + len(resident_names)
    import_table_offset = module_table_offset + 2 * len(modules)
    total_size = ne_offset + import_table_offset + len(name_table)
    result = bytearray(total_size)
    result[:2] = b"MZ"
    struct.pack_into("<I", result, 0x3C, ne_offset)
    h = ne_offset
    result[h : h + 2] = b"NE"
    struct.pack_into("<HH", result, h + 4, entry_table_offset, len(entry_table))
    result[h + 0x0C] = flags
    result[h + 0x0D] = application_flags
    if code is not None:
        struct.pack_into("<HH", result, h + 0x14, 0, 1)  # initial IP:CS
    struct.pack_into("<HHHH", result, h + 0x1C, segment_count, len(modules), 0, segment_table_offset)
    struct.pack_into("<HHHH", result, h + 0x24, 0, resident_names_offset,
                     module_table_offset, import_table_offset)
    struct.pack_into("<I", result, h + 0x2C, 0)
    struct.pack_into("<HH", result, h + 0x30, 0, 0)
    result[h + 0x36] = target_os
    struct.pack_into("<H", result, h + 0x3E, windows_version)

    if code_data is not None:
        # One aligned code segment with a relocation table following its bytes.
        stored_length = 0 if len(code_data) == 0x10000 else len(code_data)
        struct.pack_into("<HHHH", result, ne_offset + segment_table_offset,
                         segment_data_offset, stored_length, 0x0100, 0)
        result[segment_data_offset : segment_data_offset + len(code_data)] = code_data
        result[segment_data_offset + len(code_data) : segment_data_offset + len(code_data) + len(relocation_data)] = relocation_data
    result[ne_offset + entry_table_offset : ne_offset + entry_table_offset + len(entry_table)] = entry_table
    result[ne_offset + resident_names_offset : ne_offset + resident_names_offset + len(resident_names)] = resident_names
    for index, module in enumerate(modules):
        struct.pack_into("<H", result, ne_offset + module_table_offset + index * 2, name_offsets[module.upper()])
    result[ne_offset + import_table_offset : ne_offset + import_table_offset + len(name_table)] = name_table
    return bytes(result)


class NEParserTests(unittest.TestCase):
    def test_rejects_malformed_or_truncated_inputs(self):
        with self.assertRaises(NEFormatError):
            NEImage(b"not an executable")
        truncated = bytearray(b"MZ" + bytes(62))
        struct.pack_into("<I", truncated, 0x3C, 0x40)
        with self.assertRaises(NEFormatError):
            NEImage(bytes(truncated))
        bad_table = bytearray(make_ne())
        # Segment data is declared at 0xA0; remove bytes so a real segment read is truncated.
        with self.assertRaises(NEFormatError):
            NEImage(bad_table[:0xA1])

        bad_segment_table = bytearray(make_ne())
        struct.pack_into("<H", bad_segment_table, 0x40 + 0x22, 0xFFFF)
        with self.assertRaises(NEFormatError):
            NEImage(bytes(bad_segment_table))

        unterminated_imports = make_ne(imports=[("KERNEL", "GetVersion", "name")])[:-1]
        with self.assertRaises(NEFormatError):
            NEImage(unterminated_imports)

        bad_relocation = bytearray(make_ne(imports=[("KERNEL", "GetVersion", "name")]))
        relocation_record = 0xA0 + 2 + 2 + 2
        struct.pack_into("<H", bad_relocation, relocation_record + 2, 0xFFFF)
        with self.assertRaises(NEFormatError):
            NEImage(bytes(bad_relocation))

        bad_import_target = bytearray(make_ne(imports=[("KERNEL", "GetVersion", "name")]))
        struct.pack_into("<H", bad_import_target, relocation_record + 6, 0xFFFF)
        with self.assertRaises(NEFormatError):
            NEImage(bytes(bad_import_target))

        bad_module_name = bytearray(make_ne(imports=[("KERNEL", "GetVersion", "name")]))
        module_table_offset = struct.unpack_from("<H", bad_module_name, 0x40 + 0x28)[0]
        struct.pack_into("<H", bad_module_name, 0x40 + module_table_offset, 0xFFFF)
        with self.assertRaises(NEFormatError):
            NEImage(bytes(bad_module_name))

    def test_parses_module_refs_import_name_and_actual_fixup(self):
        data = make_ne(imports=[("KERNEL", "GetVersion", "name")])
        image = NEImage(data)
        self.assertEqual(image.modules, ("KERNEL",))
        self.assertEqual(len(image.imports), 1)
        item = image.imports[0]
        self.assertEqual((item.module, item.name, item.kind), ("KERNEL", "GetVersion", "name"))
        self.assertEqual(item.segment, 1)

    def test_parses_import_by_ordinal_and_checks_reference_ordinal(self):
        app = make_ne(imports=[("KERNEL", 1, "ordinal")])
        kernel = make_ne(code=None, exports=["GetVersion"])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "KERNEL.EXE").write_bytes(kernel)
            report = analyze_bytes(app, "ORDINAL.EXE", api_dir)
        self.assertEqual(report["imports"][0]["kind"], "ordinal")
        self.assertEqual(report["imports"][0]["ordinal"], 1)
        status = next(item for item in report["api_reference"]["items"] if item.get("import") == "#1")
        self.assertEqual(status["status"], "AVAILABLE_IN_REFERENCE")

    def test_imported_far_call_fixup_does_not_create_a_false_unknown_path(self):
        code = bytes.fromhex("9a 00 00 00 00 cb")
        app = bytearray(make_ne(code=code, imports=[("KERNEL", "GetVersion", "name")]))
        relocation_record = 0xA0 + len(code) + 2 + 2
        app[relocation_record] = 3  # POINTER32 fixup over the far-call operand.
        struct.pack_into("<H", app, relocation_record + 2, 1)
        kernel = make_ne(code=None, exports=["GetVersion"])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "KERNEL.EXE").write_bytes(kernel)
            report = analyze_bytes(bytes(app), "IMPORTED-CALL.EXE", api_dir)
        self.assertEqual(report["verdict"], "CANDIDATE")
        self.assertEqual(report["cpu_analysis"]["relocation_affected_instructions"], [])
        self.assertEqual(report["cpu_analysis"]["import_fixup_instruction_count"], 1)
        self.assertIn("imported API far call", [edge["kind"] for edge in report["cpu_analysis"]["unresolved_control_flow"]])

    def test_missing_import_ordinal_is_proven_against_complete_reference(self):
        app = make_ne(imports=[("KERNEL", 7, "ordinal")])
        kernel = make_ne(code=None, exports=["GetVersion"])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "KERNEL.EXE").write_bytes(kernel)
            report = analyze_bytes(app, "MISSINGORDINAL.EXE", api_dir)
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["api_reference"]["missing_3_0_apis"], ["KERNEL!#7"])

    def test_reports_internal_segment_relocations(self):
        image = NEImage(make_ne(code=b"\x00\x00\x00\x00", internal_fixups=[(0, 1, 2)]))
        fixups = image.internal_relocations()
        self.assertEqual(len(fixups), 1)
        self.assertEqual(fixups[0]["target_segment"], 1)
        self.assertTrue(fixups[0]["target_is_code"])

    def test_unused_and_constant_entry_bundles_preserve_ordinals(self):
        for bundle, constant_ordinals, expected_entry_ordinal in (
            (bytes([1, 0, 1, 1, 0, 0, 0, 0]), frozenset(), 2),
            (bytes([1, 0xFE, 0, 0x34, 0x12, 1, 1, 0, 0, 0, 0]), frozenset({1}), 2),
        ):
            with self.subTest(bundle=bundle):
                data = bytearray(make_ne(code=b"\x90\xCB"))
                table_offset = len(data) - 0x40
                data.extend(bundle)
                struct.pack_into("<HH", data, 0x40 + 4, table_offset, len(bundle))
                image = NEImage(bytes(data))
                self.assertTrue(image.entry_table_complete)
                self.assertEqual(image.constant_entry_ordinals, constant_ordinals)
                self.assertEqual([entry.ordinal for entry in image.entry_points], [expected_entry_ordinal])
                self.assertIn(expected_entry_ordinal, image.exports()[1])
                self.assertTrue(constant_ordinals.issubset(image.exports()[1]))

    def test_nonadditive_relocation_chain_is_followed_and_bounded(self):
        code = bytes.fromhex("e9 08 00 68 00 00 cb 90 ff ff cb")
        data = bytearray(make_ne(code=code, internal_fixups=[(1, 1, 5)]))
        relocation_record = 0xA0 + len(code) + 2
        data[relocation_record + 1] = 0
        image = NEImage(bytes(data))
        self.assertEqual(image.segments[0].relocations[0]["chain_sites"], (1, 8))

    def test_rejects_cyclic_nonadditive_relocation_chain(self):
        code = bytes.fromhex("e9 01 00 cb")
        data = bytearray(make_ne(code=code, internal_fixups=[(1, 1, 5)]))
        relocation_record = 0xA0 + len(code) + 2
        data[relocation_record + 1] = 0
        with self.assertRaisesRegex(NEFormatError, "cyclic relocation chain"):
            NEImage(bytes(data))

    def test_rejects_relocation_chain_site_whose_source_span_crosses_segment_end(self):
        code = bytes.fromhex("e9 05 00 90 90 ff ff")
        data = bytearray(make_ne(code=code, internal_fixups=[(1, 1, 5)]))
        relocation_record = 0xA0 + len(code) + 2
        data[relocation_record] = 3  # POINTER32 source width.
        data[relocation_record + 1] = 0  # Non-additive chain visits offset 5.
        with self.assertRaisesRegex(NEFormatError, "relocation source span"):
            NEImage(bytes(data))

    def test_chained_pointer_fixup_expands_each_overlapping_source_span(self):
        code = bytearray(b"\x90" * 0x1004)
        code[:9] = bytes.fromhex("b8 02 00 10 90 cb 90 90 cb")
        code[0x1000:0x1002] = b"\xff\xff"
        data = bytearray(make_ne(code=bytes(code), internal_fixups=[(1, 1, 0)]))
        relocation_record = 0xA0 + len(code) + 2
        data[relocation_record] = 3  # POINTER32 source width, linked by 16-bit sites.
        data[relocation_record + 1] = 0  # Non-additive chain: 1 -> 2 -> 0x1000.

        image = NEImage(bytes(data))
        relocation = image.segments[0].relocations[0]
        self.assertEqual(relocation["source_width"], 4)
        self.assertEqual(relocation["chain_sites"], (1, 2, 0x1000))

        report = analyze_bytes(bytes(data), "CHAINED-POINTER-SPANS.EXE")
        affected = {
            item["offset"]: item["fixup_sites"]
            for item in report["cpu_analysis"]["relocation_affected_instructions"]
        }
        self.assertEqual(affected[0], [1, 2])
        self.assertEqual(affected[3], [3, 4, 5])

    def test_zero_segment_file_length_means_64k(self):
        empty_segment = bytearray(make_ne(code=None))
        struct.pack_into("<H", empty_segment, 0x40 + 0x1C, 1)
        struct.pack_into("<HHHH", empty_segment, 0x40 + 0x40, 0, 0, 0, 0)
        image = NEImage(bytes(empty_segment))
        self.assertEqual(image.segments[0].file_length, 0x10000)
        self.assertEqual(len(image.segments[0].data), 0)

    def test_zero_resident_name_offset_means_no_resident_table(self):
        app = bytearray(make_ne(code=None))
        struct.pack_into("<H", app, 0x40 + 0x26, 0)
        image = NEImage(bytes(app))
        self.assertEqual(image.resident_exports, ())

    def test_reports_8086_supported_static_pass_as_candidate_only(self):
        app = make_ne(code=b"\xB8\x00\x00\xCD\x21\xCB", imports=[("KERNEL", "GetVersion", "name")])
        kernel = make_ne(code=None, exports=["GetVersion"])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "KERNEL.EXE").write_bytes(kernel)
            report = analyze_bytes(app, "APP.EXE", api_dir)
        self.assertEqual(report["verdict"], "CANDIDATE")
        self.assertEqual(report["api_reference"]["missing_3_0_apis"], [])
        self.assertGreater(report["cpu_analysis"]["reachable_instruction_count"], 0)
        self.assertNotEqual(report["verdict"], "COMPATIBLE")

    def test_detects_80186_immediate_push_with_disassembler(self):
        app = make_ne(code=b"\x68\x34\x12\xCB")
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "PUSHIMM.EXE", Path(temp))
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"][0]["minimum_cpu"], "80186")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"][0]["mnemonic"], "push")

    def test_detects_leave_as_80186(self):
        report = analyze_bytes(make_ne(code=bytes.fromhex("c9 cb")), "LEAVE.EXE")
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"][0]["minimum_cpu"], "80186")

    def test_detects_fs_segment_override_as_386(self):
        report = analyze_bytes(make_ne(code=bytes.fromhex("64 8b 07 cb")), "FS386.EXE")
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"][0]["minimum_cpu"], "80386")

    def test_instruction_prefixes_are_classified_before_mnemonic_early_returns(self):
        prefix_sequences = (
            b"\x64", b"\x65", b"\x66", b"\x67",
            b"\x64\x66", b"\x66\x64", b"\x65\x67", b"\x67\x65",
            b"\x64\x66\x67", b"\x67\x66\x64", b"\x65\x66\x67", b"\x66\x67\x65",
        )
        bodies = (bytes.fromhex("d9 07 c3"), b"\x98\xC3", b"\x99\xC3")
        for prefix in prefix_sequences:
            for body in bodies:
                with self.subTest(prefix=prefix.hex(), body=body.hex()):
                    report = analyze_bytes(make_ne(code=prefix + body), "PREFIXED.EXE")
                    self.assertEqual(report["verdict"], "BLOCKED")
                    self.assertEqual(
                        report["cpu_analysis"]["unsupported_instructions"][0]["minimum_cpu"],
                        "80386",
                    )

    def test_unclassified_instruction_family_is_not_assumed_8086(self):
        fake = SimpleNamespace(mnemonic="futureop", bytes=b"\x90", operands=(), prefix=())
        cpu, reason = _cpu_requirement(fake, SimpleNamespace(X86_OP_IMM=1, X86_OP_REG=2))
        self.assertEqual(cpu, "UNKNOWN")
        self.assertIn("unclassified", reason)

    def test_additive_offset16_fixup_makes_branch_path_unknown(self):
        code = bytes.fromhex("e9 00 00 68 00 00 cb 90 cb")
        app = make_ne(code=code, internal_fixups=[(1, 1, 5)])
        report = analyze_bytes(app, "RELOCATED-JUMP.EXE")
        cpu = report["cpu_analysis"]
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(cpu["unsupported_instructions"], [])
        self.assertEqual(cpu["relocation_affected_instructions"][0]["fixup_sites"], [1, 2])
        self.assertEqual(cpu["relocation_affected_instructions"][0]["offset"], 0)

    def test_word_fixup_span_makes_the_following_opcode_uncertain(self):
        code = bytes.fromhex("b8 00 00 68 00 00 cb")
        report = analyze_bytes(make_ne(code=code, internal_fixups=[(2, 1, 0)]), "FIXUP-SPAN.EXE")
        cpu = report["cpu_analysis"]
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(cpu["unsupported_instructions"], [])
        following_opcode = next(item for item in cpu["relocation_affected_instructions"] if item["offset"] == 3)
        self.assertEqual(following_opcode["fixup_sites"], [3])
        self.assertEqual(following_opcode["opcode_or_modrm_sites"], [3])

    def test_overlapping_word_fixup_spans_mark_each_affected_byte(self):
        code = bytes.fromhex("b8 00 00 68 00 00 cb")
        fixups = [(1, 1, 0), (2, 1, 0)]
        report = analyze_bytes(make_ne(code=code, internal_fixups=fixups), "OVERLAPPING-FIXUPS.EXE")
        cpu = report["cpu_analysis"]
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(cpu["unsupported_instructions"], [])
        self.assertEqual(
            next(item for item in cpu["relocation_affected_instructions"] if item["offset"] == 0)["fixup_sites"],
            [1, 2],
        )
        next_opcode = next(item for item in cpu["relocation_affected_instructions"] if item["offset"] == 3)
        self.assertEqual(next_opcode["opcode_or_modrm_sites"], [3])

    def test_chained_fixup_path_is_marked_uncertain_before_decoding_raw_target(self):
        code = bytes.fromhex("e9 08 00 68 00 00 cb 90 ff ff cb")
        data = bytearray(make_ne(code=code, internal_fixups=[(1, 1, 5)]))
        relocation_record = 0xA0 + len(code) + 2
        data[relocation_record + 1] = 0
        report = analyze_bytes(bytes(data), "CHAINED-JUMP.EXE")
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"], [])
        self.assertEqual(report["cpu_analysis"]["relocation_affected_instructions"][0]["fixup_sites"], [1, 2])

    def test_detects_286_arpl_at_reachable_entry(self):
        app = make_ne(code=b"\x63\x00\xCB")
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "ARPL.EXE", Path(temp))
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"][0]["minimum_cpu"], "80286")

    def test_does_not_treat_8086_cbw_cwd_or_unreachable_bytes_as_incompatibility(self):
        app = make_ne(code=b"\x98\x99\xC3\x68\x34\x12\xCB")
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "8086.EXE", Path(temp))
        self.assertEqual(report["verdict"], "CANDIDATE")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"], [])

    def test_detects_386_operand_override_from_decoded_instruction(self):
        app = make_ne(code=b"\x66\x98\xC3")
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "CWDE.EXE", Path(temp))
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["cpu_analysis"]["unsupported_instructions"][0]["minimum_cpu"], "80386")

    def test_x87_code_needs_explicit_software_emulator_dependency(self):
        app = make_ne(code=b"\xD8\xC0\xC3")
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "FPU.EXE", Path(temp))
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(len(report["cpu_analysis"]["coprocessor_instructions"]), 1)

    def test_x87_code_with_win87em_reference_remains_only_a_candidate(self):
        app = make_ne(code=b"\xD8\xC0\xC3", imports=[("WIN87EM", "FPMATH", "name")])
        win87em = make_ne(code=None, exports=["FPMATH"])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "WIN87EM.EXE").write_bytes(win87em)
            report = analyze_bytes(app, "FPU.EXE", api_dir)
        self.assertEqual(report["verdict"], "CANDIDATE")
        self.assertEqual(len(report["cpu_analysis"]["coprocessor_instructions"]), 1)

    def test_dynamic_api_resolution_keeps_verdict_unknown(self):
        app = make_ne(imports=[("KERNEL", "GetProcAddress", "name")])
        kernel = make_ne(code=None, exports=["GetProcAddress"])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "KERNEL.EXE").write_bytes(kernel)
            report = analyze_bytes(app, "DYNAMIC.EXE", api_dir)
        self.assertTrue(report["dynamic_import_resolution_seen"])
        self.assertEqual(report["verdict"], "UNKNOWN")

    def test_ordinal_getprocaddress_export_triggers_dynamic_lookup_uncertainty(self):
        app = make_ne(imports=[("KERNEL", 207, "ordinal")])
        kernel = make_ne(code=None, exports=[(207, "GetProcAddress")])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "KERNEL.EXE").write_bytes(kernel)
            report = analyze_bytes(app, "DYNAMIC-ORDINAL.EXE", api_dir)
        self.assertTrue(report["api_reference"]["all_imports_verified"])
        self.assertTrue(report["dynamic_import_resolution_seen"])
        row = next(item for item in report["api_reference"]["items"] if item.get("import") == "#207")
        self.assertEqual(row["resolved_names"], ["GETPROCADDRESS"])
        self.assertEqual(report["verdict"], "UNKNOWN")

    def test_missing_windows_3_0_api_is_proven_from_export_table(self):
        app = make_ne(imports=[("USER", "GetOpenFileName", "name")])
        user = make_ne(code=None, exports=["MessageBox"])
        with tempfile.TemporaryDirectory() as temp:
            api_dir = Path(temp)
            (api_dir / "USER.EXE").write_bytes(user)
            report = analyze_bytes(app, "USESNEWAPI.EXE", api_dir)
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["api_reference"]["missing_3_0_apis"], ["USER!GetOpenFileName"])

    def test_unknown_if_target_module_is_not_in_supplied_reference(self):
        app = make_ne(imports=[("VENDOR", "VendorCall", "name")])
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "THIRDPARTY.EXE", Path(temp))
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(report["api_reference"]["items"][0]["status"], "UNVERIFIED")

    def test_protected_mode_flag_is_not_treated_as_real_mode_candidate(self):
        app = make_ne(flags=0x08)
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "PROT.EXE", Path(temp))
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertTrue(report["windows_target"]["protected_mode_only"])

    def test_windows_386_ne_target_is_not_treated_as_windows_3_real_mode(self):
        app = make_ne(target_os=4)
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "WIN386.EXE", Path(temp))
        self.assertEqual(report["windows_target"]["os"], "Windows 386")
        self.assertEqual(report["verdict"], "BLOCKED")

    def test_vxd_import_is_reported_as_protected_mode_dependency(self):
        app = make_ne(imports=[("VMM.VXD", "InitVxD", "name")])
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "USES_VXD.EXE", Path(temp))
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["protected_mode_dependencies"], ["VMM.VXD"])

    def test_dll_application_flag_is_not_misread_as_protected_mode(self):
        app = make_ne(application_flags=0x80)
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "LIBRARY.DLL", Path(temp))
        self.assertFalse(report["windows_target"]["protected_mode_only"])
        self.assertEqual(report["windows_target"]["application_flags"], "0x80")

    def test_declared_286_cpu_requirement_is_reported_as_a_blocker(self):
        app = make_ne(flags=0x20)
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "NEEDS286.EXE", Path(temp))
        self.assertEqual(report["windows_target"]["declared_minimum_cpu"], "80286")
        self.assertEqual(report["verdict"], "BLOCKED")

    def test_expected_windows_31_flag_alone_is_unknown_not_compatible(self):
        app = make_ne(windows_version=0x030A)
        with tempfile.TemporaryDirectory() as temp:
            report = analyze_bytes(app, "VERSIONFLAG.EXE", Path(temp))
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertTrue(report["windows_target"]["version_flag_is_not_compatibility_proof"])

    def test_compatible_requires_all_runtime_actions_and_exact_target(self):
        app = make_ne(code=b"\x90\xCB")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = root / "runtime.json"
            evidence.write_text(json.dumps(runtime_evidence(app)), encoding="utf-8")
            report = analyze_bytes(app, "PASS.EXE", root, evidence)
        self.assertEqual(report["verdict"], "COMPATIBLE")

    def test_runtime_evidence_cannot_be_reused_for_a_different_image(self):
        evidence_image = make_ne(code=b"\x90\xCB")
        analyzed_image = make_ne(code=b"\x90\xC3")
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "runtime.json"
            evidence.write_text(json.dumps(runtime_evidence(evidence_image)), encoding="utf-8")
            report = analyze_bytes(analyzed_image, "PASS.EXE", Path(temp), evidence)
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertFalse(report["runtime_evidence"]["accepted"])
        self.assertIn("identity", report["runtime_evidence"]["error"])

    def test_runtime_evidence_rejects_malformed_or_incomplete_records(self):
        app = make_ne(code=b"\x90\xCB")
        good = runtime_evidence(app)
        malformed_records = [
            [],
            {key: value for key, value in good.items() if key != "image"},
            {**good, "image": {**good["image"], "filename": "OTHER.EXE"}},
            {**good, "actions": {"input": True, "representative_task": "true", "redraw": True, "clean_exit": True}},
            {**good, "unexpected": "extra"},
        ]
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "runtime.json"
            for index, value in enumerate(malformed_records):
                with self.subTest(index=index):
                    evidence.write_text(json.dumps(value), encoding="utf-8")
                    report = analyze_bytes(app, "PASS.EXE", Path(temp), evidence)
                    self.assertEqual(report["verdict"], "UNKNOWN")
                    self.assertFalse(report["runtime_evidence"]["accepted"])
            evidence.write_text('{"schema":"w31check-runtime-v1","schema":"w31check-runtime-v1"}', encoding="utf-8")
            report = analyze_bytes(app, "PASS.EXE", Path(temp), evidence)
            self.assertEqual(report["verdict"], "UNKNOWN")
            self.assertIn("duplicate", report["runtime_evidence"]["error"])


@unittest.skipUnless(
    os.environ.get("W31CHECK_REAL_APPS_DIR") and os.environ.get("W31CHECK_WINDOWS_30_API_DIR"),
    "set W31CHECK_REAL_APPS_DIR and W31CHECK_WINDOWS_30_API_DIR to private Windows 3.0 copies",
)
class LocalMediaSmokeTests(unittest.TestCase):
    def test_known_windows_30_calc_and_notepad_parse_as_windows_ne(self):
        root = Path(os.environ["W31CHECK_REAL_APPS_DIR"])
        api_dir = Path(os.environ["W31CHECK_WINDOWS_30_API_DIR"])
        for name in ("CALC.EXE", "NOTEPAD.EXE"):
            with self.subTest(application=name):
                report = analyze_bytes((root / name).read_bytes(), name, api_dir)
                self.assertEqual(report["format"], "NE")
                self.assertEqual(report["windows_target"]["os"], "Windows")
                self.assertEqual(report["windows_target"]["expected_windows_version_flag"], "3.0")
                self.assertTrue(report["api_reference"]["all_imports_verified"])
                self.assertEqual(report["api_reference"]["missing_3_0_apis"], [])
                self.assertEqual(report["static_blockers"], [])


@unittest.skipUnless(
    os.environ.get("W31CHECK_WINDOWS_30_API_DIR"),
    "set W31CHECK_WINDOWS_30_API_DIR to the private Windows 3.0 API reference",
)
class LocalOrdinalResolutionTests(unittest.TestCase):
    def test_windows_30_kernel_ordinal_207_is_verified_from_entry_table(self):
        app = make_ne(imports=[("KERNEL", 207, "ordinal")])
        report = analyze_bytes(app, "DYNAMIC-ORDINAL.EXE", Path(os.environ["W31CHECK_WINDOWS_30_API_DIR"]))
        row = next(item for item in report["api_reference"]["items"] if item.get("import") == "#207")
        self.assertEqual(row["status"], "AVAILABLE_IN_REFERENCE")
        self.assertEqual(row["resolved_names"], [])
        self.assertFalse(report["dynamic_import_resolution_seen"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
