import unittest

from cpu_subset import CPU
from ne_loader import ImportTarget, LoadedNE
from win16_host import CallbackError, GuestCallbackDispatcher, UnsupportedImport, Win16Host


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
