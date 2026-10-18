import unittest

from cpu_subset import CPU
from ne_loader import ImportTarget, LoadedNE
from win16_host import (
    CallbackError,
    GuestCallbackDispatcher,
    SyntheticDosVersion,
    UnsupportedImport,
    Win16Host,
)


class Win16HostTests(unittest.TestCase):
    def make_loaded(self, memory=None):
        return LoadedNE(
            memory=memory if memory is not None else bytearray(1 << 20),
            image=object(),
            segment_selectors={1: 0x1000},
            import_targets={(0xF001, 1): ImportTarget("GDI", "ordinal", None, 1)},
            initial_cs=0x1000,
            initial_ip=0x0100,
            initial_ss=0x2000,
            initial_sp=0x0100,
            loaded_bytes=0,
        )

    def test_unbound_gdi_import_fails_closed(self):
        loaded = self.make_loaded()
        host = Win16Host(loaded)
        with self.assertRaisesRegex(UnsupportedImport, "GDI ordinal 1"):
            host.dispatch_import(CPU(memory=loaded.memory), 0xF001, 1)
        self.assertEqual(host.calls, [])

    def test_dos3call_get_interrupt_zero_returns_documented_es_bx_and_far_returns(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        target = ImportTarget("KERNEL", "ordinal", None, 102)
        loaded.import_targets[(0xF001, 0x0102)] = target
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0x1000, 0x0123
        cpu.SS, cpu.SP = 0x2000, 0x0100
        cpu.AX, cpu.BX, cpu.CX, cpu.DX = 0x3500, 0x2222, 0x3333, 0x4444
        cpu.SI, cpu.DI, cpu.DS, cpu.ES = 0x5555, 0x6666, 0x7777, 0x8888
        cpu.write16(cpu.SS, cpu.SP, 0xA55A)  # Caller-owned stack sentinel.
        cpu.call_far(0xF001, 0x0102)
        handler_sp = cpu.SP

        host = Win16Host(loaded, dos_interrupt_vectors={0: (0x4321, 0x8765)})
        self.assertIs(host.dispatch_import(cpu, 0xF001, 0x0102), True)

        self.assertEqual((cpu.CS, cpu.IP, cpu.SS, cpu.SP), (0x1000, 0x0123, 0x2000, 0x0100))
        self.assertEqual((cpu.ES, cpu.BX), (0x4321, 0x8765))
        self.assertEqual((cpu.AX, cpu.CX, cpu.DX, cpu.SI, cpu.DI, cpu.DS),
                         (0x3500, 0x3333, 0x4444, 0x5555, 0x6666, 0x7777))
        self.assertEqual(cpu.read16(cpu.SS, 0x0100), 0xA55A)
        self.assertEqual(host.calls, [target])
        self.assertEqual(host.dos3call_records[0].request_ax, 0x3500)
        self.assertEqual(host.dos3call_records[0].interrupt_number, 0)
        self.assertEqual(host.dos3call_records[0].handler_sp, handler_sp)
        self.assertEqual(host.dos3call_records[0].returned_sp, 0x0100)

    def test_dos3call_rejects_other_dos_functions_without_mutating_cpu_or_stack(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        target = ImportTarget("KERNEL", "ordinal", None, 102)
        loaded.import_targets[(0xF001, 0x0102)] = target
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0x1000, 0x0123
        cpu.SS, cpu.SP = 0x2000, 0x0100
        cpu.AX, cpu.BX, cpu.ES = 0x3100, 0x2222, 0x8888
        cpu.write16(cpu.SS, cpu.SP, 0xA55A)
        cpu.call_far(0xF001, 0x0102)
        before = (cpu.CS, cpu.IP, cpu.SS, cpu.SP, cpu.AX, cpu.BX, cpu.ES,
                  cpu.read16(cpu.SS, cpu.SP), cpu.read16(cpu.SS, cpu.SP + 2))

        host = Win16Host(loaded, dos_interrupt_vectors={0: (0x4321, 0x8765)})
        with self.assertRaisesRegex(
            UnsupportedImport, "supports AX=3000h, 3500h, or 2500h"
        ):
            host.dispatch_import(cpu, 0xF001, 0x0102)

        after = (cpu.CS, cpu.IP, cpu.SS, cpu.SP, cpu.AX, cpu.BX, cpu.ES,
                 cpu.read16(cpu.SS, cpu.SP), cpu.read16(cpu.SS, cpu.SP + 2))
        self.assertEqual(after, before)
        self.assertEqual(host.calls, [])
        self.assertEqual(host.dos3call_records, [])

    def test_dos3call_get_dos_version_returns_documented_ax_bx_cx_registers(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        target = ImportTarget("KERNEL", "ordinal", None, 102)
        loaded.import_targets[(0xF001, 0x0102)] = target
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0x1000, 0x0123
        cpu.SS, cpu.SP = 0x2000, 0x0100
        cpu.AX, cpu.BX, cpu.CX, cpu.DX = 0x3000, 0x1111, 0x2222, 0x3333
        cpu.DS, cpu.ES = 0x4444, 0x5555
        cpu.call_far(0xF001, 0x0102)
        handler_sp = cpu.SP

        host = Win16Host(
            loaded,
            dos_version=SyntheticDosVersion(major=3, minor=30, oem_id=0x0C,
                                            serial24=0xABCDEF),
        )
        self.assertIs(host.dispatch_import(cpu, 0xF001, 0x0102), True)

        self.assertEqual((cpu.CS, cpu.IP, cpu.SS, cpu.SP), (0x1000, 0x0123, 0x2000, 0x0100))
        self.assertEqual((cpu.AX, cpu.BX, cpu.CX), (0x1E03, 0x0CAB, 0xCDEF))
        self.assertEqual((cpu.DX, cpu.DS, cpu.ES), (0x3333, 0x4444, 0x5555))
        self.assertEqual(host.calls, [target])
        self.assertEqual(host.dos_version_call_records[0].request_ax, 0x3000)
        self.assertEqual(host.dos_version_call_records[0].serial24, 0xABCDEF)
        self.assertEqual(host.dos_version_call_records[0].handler_sp, handler_sp)
        self.assertEqual(host.dos_version_call_records[0].returned_sp, 0x0100)

    def test_dos3call_get_version_requires_explicit_synthetic_dos_context(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        loaded.import_targets[(0xF001, 0x0102)] = ImportTarget(
            "KERNEL", "ordinal", None, 102
        )
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0x1000, 0x0123
        cpu.SS, cpu.SP = 0x2000, 0x0100
        cpu.AX = 0x3000
        cpu.call_far(0xF001, 0x0102)
        before = (cpu.CS, cpu.IP, cpu.SP, cpu.AX, cpu.BX, cpu.CX)

        host = Win16Host(loaded)
        with self.assertRaisesRegex(UnsupportedImport, "no explicit synthetic DOS version"):
            host.dispatch_import(cpu, 0xF001, 0x0102)

        self.assertEqual((cpu.CS, cpu.IP, cpu.SP, cpu.AX, cpu.BX, cpu.CX), before)
        self.assertEqual(host.calls, [])
        self.assertEqual(host.dos_version_call_records, [])

    def test_dos3call_set_interrupt_zero_uses_ds_dx_and_has_no_return_registers(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        target = ImportTarget("KERNEL", "ordinal", None, 102)
        loaded.import_targets[(0xF001, 0x0102)] = target
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0x1000, 0x0123
        cpu.SS, cpu.SP = 0x2000, 0x0100
        cpu.AX, cpu.BX, cpu.CX = 0x2500, 0x2222, 0x3333
        cpu.DX, cpu.DS, cpu.ES = 0x2A18, 0x1000, 0x8888
        cpu.write16(cpu.SS, cpu.SP, 0xA55A)
        cpu.call_far(0xF001, 0x0102)
        handler_sp = cpu.SP

        host = Win16Host(loaded, dos_interrupt_vectors={0: (0xF000, 0x0040)})
        self.assertIs(host.dispatch_import(cpu, 0xF001, 0x0102), True)

        self.assertEqual((cpu.CS, cpu.IP, cpu.SS, cpu.SP), (0x1000, 0x0123, 0x2000, 0x0100))
        self.assertEqual((cpu.AX, cpu.BX, cpu.CX, cpu.DX, cpu.DS, cpu.ES),
                         (0x2500, 0x2222, 0x3333, 0x2A18, 0x1000, 0x8888))
        self.assertEqual(host.dos_interrupt_vectors[0], (0x1000, 0x2A18))
        self.assertEqual(host.calls, [target])
        record = host.dos3call_records[0]
        self.assertEqual(record.action, "set")
        self.assertEqual(record.vector_before, (0xF000, 0x0040))
        self.assertEqual(record.vector_after, (0x1000, 0x2A18))
        self.assertEqual(record.handler_sp, handler_sp)
        self.assertEqual(record.returned_sp, 0x0100)
        self.assertEqual(cpu.read16(cpu.SS, 0x0100), 0xA55A)

    def test_dos3call_missing_synthetic_vector_fails_before_returning(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        loaded.import_targets[(0xF001, 0x0102)] = ImportTarget(
            "KERNEL", "ordinal", None, 102
        )
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0x1000, 0x0123
        cpu.SS, cpu.SP = 0x2000, 0x0100
        cpu.AX = 0x3500
        cpu.call_far(0xF001, 0x0102)
        before = (cpu.CS, cpu.IP, cpu.SP, cpu.AX, cpu.BX, cpu.ES)

        host = Win16Host(loaded)
        with self.assertRaisesRegex(UnsupportedImport, "no synthetic vector"):
            host.dispatch_import(cpu, 0xF001, 0x0102)

        self.assertEqual((cpu.CS, cpu.IP, cpu.SP, cpu.AX, cpu.BX, cpu.ES), before)
        self.assertEqual(host.calls, [])
        self.assertEqual(host.dos3call_records, [])

    def test_synthetic_dos_vector_context_requires_valid_16_bit_pairs(self):
        loaded = self.make_loaded()
        for vectors in (
            {-1: (0x1234, 0x5678)},
            {0: (0x10000, 0x0000)},
            {0: (0x1234, 0x5678, 0x9ABC)},
            {0: [0x1234, 0x5678]},
        ):
            with self.subTest(vectors=vectors):
                with self.assertRaises(ValueError):
                    Win16Host(loaded, dos_interrupt_vectors=vectors)

    def test_first_party_far_callback_returns_to_host_frame(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0xF000, 0x0123  # The current import-service continuation.
        cpu.SS, cpu.SP = 0x2000, 0x0100
        callback_selector, callback_offset = 0x1000, 0x0200
        callback_start = cpu.linear(callback_selector, callback_offset)
        memory[callback_start:callback_start + 4] = bytes.fromhex("B8 EF BE CB")

        host = Win16Host(loaded)
        steps = host.call_guest_callback(cpu, callback_selector, callback_offset)

        self.assertEqual(steps, 2)
        self.assertEqual((cpu.AX, cpu.CS, cpu.IP, cpu.SP),
                         (0xBEEF, 0xF000, 0x0123, 0x0100))

    def test_callback_that_does_not_return_fails_closed(self):
        cpu = CPU(); cpu.CS, cpu.IP = 0xF000, 0x0100
        cpu.SS, cpu.SP = 0x2000, 0x0100
        selector, offset = 0x1000, 0x0200
        start = cpu.linear(selector, offset)
        cpu.memory[start:start + 1] = b"\x90"  # NOP forever through adjacent zero bytes.
        with self.assertRaisesRegex(CallbackError, "unsupported callback instruction"):
            GuestCallbackDispatcher(instruction_limit=2).invoke(cpu, selector, offset)

    def test_pascal_callback_must_clean_its_stack_arguments(self):
        memory = bytearray(1 << 20)
        loaded = self.make_loaded(memory)
        cpu = CPU(memory=memory)
        cpu.CS, cpu.IP = 0xF000, 0x0123
        cpu.SS, cpu.SP = 0x2000, 0x0100
        selector, offset = 0x1000, 0x0200
        start = cpu.linear(selector, offset)
        memory[start:start + 4] = bytes.fromhex("B8 EF BE CB")  # RETF, no RETF n.

        with self.assertRaisesRegex(CallbackError, "expected 0100"):
            GuestCallbackDispatcher().invoke(
                cpu, selector, offset, argument_words_push_order=(0x1234,)
            )


if __name__ == "__main__":
    unittest.main()
