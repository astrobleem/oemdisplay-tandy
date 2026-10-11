"""Synthetic NE/parser tests plus an opt-in host-side real-media smoke test."""

import json
import os
import struct
import tempfile
import unittest
from pathlib import Path

from w31check import NEFormatError, NEImage, analyze_bytes


def _pstring(value):
    raw = value.encode("ascii")
    return bytes([len(raw)]) + raw


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
        target_flags = 1 if kind == "ordinal" else 2
        target2 = int(symbol) if kind == "ordinal" else name_offsets[symbol.upper()]
        relocations.extend(struct.pack("<BBHHH", 0, target_flags, 0, modules.index(module) + 1, target2))
    for source_offset, target_segment, target_offset in internal_fixups:
        relocations.extend(struct.pack("<BBHHH", 0, 0, source_offset, target_segment, target_offset))
    relocation_count = len(imports) + len(internal_fixups)
    relocation_data = struct.pack("<H", relocation_count) + relocations if code is not None else b""

    entry_table = bytes([1, 1, 0, 0, 0, 0]) if include_fixed_entry and code is not None else b"\0"
    resident_names = bytearray(_pstring("TESTMOD") + struct.pack("<H", 0))
    for ordinal, name in enumerate(exports, 1):
        resident_names.extend(_pstring(name) + struct.pack("<H", ordinal))
    resident_names.append(0)

    entry_table_offset = segment_data_offset - ne_offset if code is None else segment_data_offset + len(code) + len(relocation_data) - ne_offset
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

    if code is not None:
        # One aligned code segment with a relocation table following its bytes.
        stored_length = 0 if len(code) == 0x10000 else len(code)
        struct.pack_into("<HHHH", result, ne_offset + segment_table_offset,
                         segment_data_offset, stored_length, 0x0100, 0)
        result[segment_data_offset : segment_data_offset + len(code)] = code
        result[segment_data_offset + len(code) : segment_data_offset + len(code) + len(relocation_data)] = relocation_data
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
        relocation_record = 0xA0 + 2 + 2
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
            evidence.write_text(json.dumps({
                "result": "PASS",
                "target": {"windows": "3.0", "mode": "real", "cpu": "8088", "memory_kb": 640,
                           "display": "320x200x16"},
                "actions": {"input": True, "representative_task": True, "redraw": True, "clean_exit": True},
            }), encoding="utf-8")
            report = analyze_bytes(app, "PASS.EXE", root, evidence)
        self.assertEqual(report["verdict"], "COMPATIBLE")


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
