import json
from pathlib import Path
import tempfile
import unittest

from cpu_subset import CPU, UnsupportedOpcode
from dos_context import (
    DosContextError,
    SyntheticDosLaunchContext,
    build_dos_environment_block,
    validate_dos_environment_block,
)
from ne_loader import LoadedNE
from win16_host import InitTaskRegisters


def context(**changes):
    values = {
        "psp_segment": 0x3000,
        "environment_segment": 0x3100,
        "environment_entries": (),
        "program_path": r"C:\FIXTURE\WINMINE.EXE",
        "command_tail": "",
        "interrupt_vectors": ((0, 0xF000, 0x0040),),
    }
    values.update(changes)
    return SyntheticDosLaunchContext(**values)


class SyntheticDosContextTests(unittest.TestCase):
    def make_loaded(self, memory=None):
        return LoadedNE(
            memory=memory if memory is not None else bytearray(1 << 20),
            image=object(),
            segment_selectors={1: 0x1000, 2: 0x2000},
            import_targets={},
            initial_cs=0x1000,
            initial_ip=0x0100,
            initial_ss=0x2000,
            initial_sp=0xFFFE,
            loaded_bytes=0,
        )

    def test_empty_environment_has_double_nul_and_explicit_path_trailer(self):
        block = build_dos_environment_block((), r"C:\FIXTURE\WINMINE.EXE")
        self.assertEqual(block, b"\0\0\x01\0C:\\FIXTURE\\WINMINE.EXE\0")
        self.assertEqual(
            validate_dos_environment_block(block),
            ((), r"C:\FIXTURE\WINMINE.EXE"),
        )

    def test_environment_entries_are_name_value_ascii_without_controls(self):
        block = build_dos_environment_block(("A=1", "PATH=C:\\FIXTURE"), "C:\\FIXTURE\\APP.EXE")
        self.assertEqual(
            validate_dos_environment_block(block),
            (("A=1", "PATH=C:\\FIXTURE"), "C:\\FIXTURE\\APP.EXE"),
        )
        for entry in ("NO_EQUALS", "=VALUE", "A=B\0", "CAFÉ=1", "A=bad\nvalue"):
            with self.subTest(entry=entry):
                with self.assertRaises(DosContextError):
                    build_dos_environment_block((entry,), "C:\\APP.EXE")

    def test_environment_parser_rejects_unterminated_or_malformed_blocks(self):
        for block in (
            b"A=B\0",
            b"A=B\0\0",
            b"A=B\0\0\x02\0PATH\0",
            b"A=B\0\0\x01\0PATH",
            b"A=B\0\0\x01\0PATH\0extra\0",
        ):
            with self.subTest(block=block):
                with self.assertRaises(DosContextError):
                    validate_dos_environment_block(block)

    def test_explicit_json_fixture_installs_psp_environment_and_guest_ivt(self):
        path = Path(__file__).with_name("fixtures") / "winmine-synthetic-dos-context.json"
        launch = SyntheticDosLaunchContext.from_json_file(path)
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        cpu = CPU(memory=memory)
        launch.install(cpu, loaded, InitTaskRegisters())

        self.assertEqual(cpu.read16(0x3000, 0x2C), 0x3100)
        self.assertEqual(cpu.read8(0x3000, 0x80), 0)
        self.assertEqual(cpu.read8(0x3000, 0x81), 0x0D)
        self.assertEqual(cpu.read8(0x3100, 0), 0)
        self.assertEqual((cpu.read16(0, 0), cpu.read16(0, 2)), (0x0040, 0xF000))
        self.assertEqual(launch.report()["synthetic"], True)

        with self.assertRaisesRegex(UnsupportedOpcode, "uninitialized synthetic PSP"):
            cpu.read8(0x3000, 0x03)
        with self.assertRaisesRegex(UnsupportedOpcode, "uninitialized synthetic IVT"):
            cpu.read8(0, 0x04)
        with self.assertRaisesRegex(UnsupportedOpcode, "uninitialized synthetic low DOS memory"):
            cpu.read8(0, 0x0500)
        with self.assertRaisesRegex(UnsupportedOpcode, "unterminated or out-of-range synthetic environment"):
            cpu.read8(0x3100, len(launch.environment_block))

    def test_json_loader_rejects_missing_or_unknown_context_fields(self):
        path = Path(__file__).with_name("fixtures") / "winmine-synthetic-dos-context.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        for changed in (
            {key: field for key, field in value.items() if key != "notice"},
            dict(value, ignored="not allowed"),
            dict(value, notice="Ordinary launch data only."),
        ):
            with tempfile.TemporaryDirectory() as directory:
                temp_path = Path(directory) / "context.json"
                temp_path.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(changed=changed):
                    with self.assertRaises(DosContextError):
                        SyntheticDosLaunchContext.from_json_file(temp_path)

    def test_launch_context_checks_segments_overlap_and_scan_bounds(self):
        loaded = self.make_loaded()
        cpu = CPU(memory=loaded.memory)
        with self.assertRaisesRegex(DosContextError, "share the same guest memory"):
            context().validate_for(CPU(), loaded, InitTaskRegisters())
        with self.assertRaisesRegex(DosContextError, "disagrees"):
            context(psp_segment=0x3001).validate_for(cpu, loaded, InitTaskRegisters())
        with self.assertRaisesRegex(DosContextError, "overlaps loaded selector"):
            context(environment_segment=0x2000).validate_for(cpu, loaded, InitTaskRegisters())
        with self.assertRaisesRegex(DosContextError, "overlaps loaded selector"):
            context(psp_segment=0x2000).validate_for(
                cpu, loaded, InitTaskRegisters(psp_segment=0x2000)
            )
        with self.assertRaisesRegex(DosContextError, "overlaps the IVT"):
            context(psp_segment=0x0030).validate_for(
                cpu, loaded, InitTaskRegisters(psp_segment=0x0030)
            )
        with self.assertRaisesRegex(DosContextError, "low DOS memory"):
            context(psp_segment=0x0800).validate_for(
                cpu, loaded, InitTaskRegisters(psp_segment=0x0800)
            )
        with self.assertRaisesRegex(DosContextError, "overlaps low DOS memory"):
            context(environment_segment=0x0800).validate_for(cpu, loaded, InitTaskRegisters())
        with self.assertRaisesRegex(DosContextError, "outside guest memory"):
            context(environment_segment=0xFF00).validate_for(cpu, loaded, InitTaskRegisters())
        with self.assertRaisesRegex(DosContextError, "command-tail offset"):
            context().validate_for(cpu, loaded, InitTaskRegisters(command_tail_offset=0x90))

    def test_command_tail_limit_and_required_int00_context(self):
        with self.assertRaisesRegex(DosContextError, "126-byte"):
            context(command_tail="x" * 127)
        with self.assertRaisesRegex(DosContextError, "explicit INT 00h"):
            context(interrupt_vectors=((1, 0xF000, 0x0100),))


if __name__ == "__main__":
    unittest.main()
