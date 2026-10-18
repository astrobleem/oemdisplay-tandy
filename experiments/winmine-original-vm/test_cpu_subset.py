import unittest

from cpu_subset import CPU, UnsupportedOpcode


def load(cpu, code, offset=0x100):
    cpu.CS = 0x1000
    cpu.IP = offset
    start = cpu.linear(cpu.CS, offset)
    cpu.memory[start:start + len(code)] = code


class CpuSubsetTests(unittest.TestCase):
    def test_synthetic_8086_block_expected_register_stack_and_flags(self):
        c = CPU(); c.SS = 0x2000; c.SP = 0x0100
        # MOV AX,7; MOV BX,5; ADD AX,BX; PUSH AX; XOR AX,AX;
        # POP CX; CMP CX,12
        load(c, bytes.fromhex("B8 07 00 BB 05 00 03 C3 50 31 C0 59 81 F9 0C 00"))
        c.run(7)
        self.assertEqual((c.AX, c.BX, c.CX, c.SP), (0, 5, 12, 0x0100))
        self.assertEqual(c.read16(c.SS, 0x00FE), 12)
        self.assertTrue(c.flag("ZF")); self.assertFalse(c.flag("CF"))
        self.assertFalse(c.flag("SF")); self.assertFalse(c.flag("OF"))
        self.assertEqual(c.IP, 0x110)

    def test_80186_push_immediate_forms_sign_extend_and_preserve_flags(self):
        c = CPU(); c.SS = 0x2000; c.SP = 0x0100; c.flags = 0x0ED7
        load(c, bytes.fromhex("6A 80 68 34 12"))
        c.run(2)
        self.assertEqual(c.SP, 0x00FC)
        self.assertEqual(c.read16(c.SS, 0x00FE), 0xFF80)
        self.assertEqual(c.read16(c.SS, 0x00FC), 0x1234)
        self.assertEqual(c.flags, 0x0ED7)

    def test_80186_imul_signed_immediate_flags_and_destination(self):
        c = CPU(); c.AX = 0xFFFF; c.flags = 0x0002
        load(c, bytes.fromhex("6B C8 FE"))  # IMUL CX,AX,-2 => +2
        c.step()
        self.assertEqual(c.CX, 2)
        self.assertFalse(c.flag("CF")); self.assertFalse(c.flag("OF"))
        c.AX = 0x4000; c.IP = 0x100
        c.step()  # 16384 * -2 = -32768, still representable
        self.assertEqual(c.CX, 0x8000)
        self.assertFalse(c.flag("CF")); self.assertFalse(c.flag("OF"))
        # 16384 * +2 overflows signed 16-bit.
        load(c, bytes.fromhex("6B C8 02")); c.step()
        self.assertEqual(c.CX, 0x8000)
        self.assertTrue(c.flag("CF")); self.assertTrue(c.flag("OF"))

    def test_host_import_intercept_and_callback(self):
        c = CPU(); load(c, bytes.fromhex("B8 01 00 CD FF"))
        seen = []
        def import_handler(cpu, vector):
            seen.append((vector, cpu.AX))
            cpu.AX = 0xBEEF
        c.run(2, import_handler)
        self.assertEqual(seen, [(0xFF, 1)])
        self.assertEqual(c.AX, 0xBEEF)

    def test_far_import_call_relocated_target_and_retf_return(self):
        c = CPU(); c.SS = 0x2000; c.SP = 0x0100
        c.CS = 0x1000
        # Entry sequence: XOR BP,BP; PUSH BP; CALL FAR relocated target.
        # The loader has resolved the call operand to 1234:5678.
        load(c, bytes.fromhex("31 ED 55 9A 34 12 78 56"))
        observed = []
        def imported(cpu, target_cs, target_ip):
            observed.append((target_cs, target_ip, cpu.CS, cpu.IP, cpu.SP,
                            cpu.read16(cpu.SS, cpu.SP), cpu.read16(cpu.SS, cpu.SP + 2)))
            cpu.AX = 0xCAFE
        c.run(3, import_handler=imported)
        self.assertEqual(observed, [(0x5678, 0x1234, 0x5678, 0x1234,
                                     0x00FA, 0x0108, 0x1000)])
        self.assertEqual((c.BP, c.AX, c.SP, c.CS, c.IP),
                         (0, 0xCAFE, 0x00FE, 0x1000, 0x0108))
        self.assertEqual(c.read16(c.SS, c.SP), 0)

    def test_unknown_opcode_fails_closed_without_advancing_ip(self):
        c = CPU(); load(c, b"\x0f")
        before = (c.AX, c.BX, c.flags, c.SP)
        with self.assertRaisesRegex(UnsupportedOpcode, "0F"):
            c.step()
        self.assertEqual(c.IP, 0x100)
        self.assertEqual((c.AX, c.BX, c.flags, c.SP), before)


if __name__ == "__main__":
    unittest.main()

