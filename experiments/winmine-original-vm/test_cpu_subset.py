import unittest
from itertools import product

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

    def test_mov_ah_immediate_preserves_al_and_flags(self):
        c = CPU(); c.AX = 0x12EF; c.flags = 0x0ED7
        load(c, bytes.fromhex("B4 30"))
        c.step()
        self.assertEqual((c.AX, c.IP, c.flags), (0x30EF, 0x0102, 0x0ED7))

    def test_cwd_sign_extends_ax_into_dx_without_changing_flags(self):
        for ax, expected_dx in ((0x0000, 0x0000), (0x7FFF, 0x0000), (0x8000, 0xFFFF),
                                (0xFFFF, 0xFFFF)):
            with self.subTest(ax=ax):
                c = CPU(); c.AX = ax; c.DX = 0x1234; c.flags = 0x0ED7
                load(c, bytes.fromhex("99"))
                c.step()
                self.assertEqual((c.AX, c.DX, c.flags), (ax, expected_dx, 0x0ED7))

    def test_cmp_al_immediate_sets_8_bit_subtract_flags_without_changing_ax(self):
        for ax, immediate, expected_flags in (
            (0x1203, 0x02, {"CF": 0, "AF": 0, "OF": 0, "ZF": 0, "SF": 0, "PF": 0}),
            (0x1200, 0x01, {"CF": 1, "AF": 1, "OF": 0, "ZF": 0, "SF": 1, "PF": 1}),
            (0x1280, 0x01, {"CF": 0, "AF": 1, "OF": 1, "ZF": 0, "SF": 0, "PF": 0}),
        ):
            with self.subTest(ax=ax, immediate=immediate):
                c = CPU(); c.AX = ax; c.flags = 0x0ED7
                load(c, bytes((0x3C, immediate)))
                c.step()
                self.assertEqual(c.AX, ax)
                self.assertEqual({name: int(c.flag(name)) for name in expected_flags}, expected_flags)

    def test_mov_moffs_ax_writes_ds_and_preserves_flags(self):
        c = CPU(); c.AX = 0xABCD; c.DS = 0x2000; c.flags = 0x0ED7
        load(c, bytes.fromhex("A3 22 01"))
        c.step()
        self.assertEqual(c.read16(c.DS, 0x0122), 0xABCD)
        self.assertEqual((c.AX, c.IP, c.flags), (0xABCD, 0x0103, 0x0ED7))

    def test_push_cs_pop_ds_preserve_flags_and_restore_stack(self):
        c = CPU(); c.CS = 0x1234; c.DS = 0xAAAA; c.SS = 0x2000; c.SP = 0x0100
        c.flags = 0x0ED7
        code = bytes.fromhex("0E 1F")
        load(c, code)
        c.CS = 0x1234
        start = c.linear(c.CS, 0x0100)
        c.memory[start:start + len(code)] = code
        c.run(2)
        self.assertEqual((c.CS, c.DS, c.SP), (0x1234, 0x1234, 0x0100))
        self.assertEqual(c.read16(c.SS, 0x00FE), 0x1234)
        self.assertEqual(c.flags, 0x0ED7)

    def test_push_ss_pop_ds_preserve_flags_and_restore_stack(self):
        c = CPU(); c.DS = 0xAAAA; c.SS = 0x2000; c.SP = 0x0100; c.flags = 0x0ED7
        load(c, bytes.fromhex("16 1F"))
        c.run(2)
        self.assertEqual((c.DS, c.SP), (0x2000, 0x0100))
        self.assertEqual(c.read16(c.SS, 0x00FE), 0x2000)
        self.assertEqual(c.flags, 0x0ED7)

    def test_jcxz_short_taken_and_not_taken_preserves_flags(self):
        for count, expected_ax, expected_ip in ((0, 0x2222, 0x0108), (1, 0x1111, 0x0105)):
            with self.subTest(cx=count):
                c = CPU(); c.CX = count; c.flags = 0x0ED7
                load(c, bytes.fromhex("E3 03 B8 11 11 B8 22 22"))
                c.run(2 if count == 0 else 2)
                self.assertEqual((c.AX, c.IP), (expected_ax, expected_ip))
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

    def test_mov_segment_register_to_direct_memory_is_little_endian_and_preserves_flags(self):
        c = CPU(); c.ES = 0xBEEF; c.DS = 0x1234; c.flags = 0x0ED7
        load(c, bytes.fromhex("8C 06 22 01"))  # MOV WORD PTR [0122h], ES
        before_registers = (c.AX, c.BX, c.CX, c.DX, c.SI, c.DI, c.BP, c.SP,
                            c.CS, c.DS, c.ES, c.SS)
        c.step()
        address = (0x1234 << 4) + 0x0122
        self.assertEqual(bytes(c.memory[address:address + 2]), bytes.fromhex("EF BE"))
        self.assertEqual(c.IP, 0x104)
        self.assertEqual((c.AX, c.BX, c.CX, c.DX, c.SI, c.DI, c.BP, c.SP,
                          c.CS, c.DS, c.ES, c.SS), before_registers)
        self.assertEqual(c.flags, 0x0ED7)

    def test_mov_segment_register_to_general_register_preserves_flags(self):
        c = CPU(); c.AX = 0x1234; c.ES = 0xCAFE; c.flags = 0x0ED7
        load(c, bytes.fromhex("8C C0"))  # MOV AX, ES
        c.step()
        self.assertEqual(c.AX, 0xCAFE)
        self.assertEqual(c.ES, 0xCAFE)
        self.assertEqual(c.IP, 0x102)
        self.assertEqual(c.flags, 0x0ED7)

    def test_mov_es_from_memory_is_bounded_and_preserves_flags(self):
        c = CPU(); c.DS = 0x2000; c.ES = 0xAAAA; c.flags = 0x0ED7
        c.write16(c.DS, 0x0122, 0x3000)
        load(c, bytes.fromhex("8E 06 22 01"))
        c.step()
        self.assertEqual((c.ES, c.IP), (0x3000, 0x0104))
        self.assertEqual(c.flags, 0x0ED7)

    def test_mov_segment_from_rm_rejects_non_es_selector_without_mutation(self):
        c = CPU(); c.DS = 0x2000; c.ES = 0xAAAA; c.flags = 0x0ED7
        c.write16(c.DS, 0x0122, 0x3000)
        load(c, bytes.fromhex("8E 1E 22 01"))  # MOV DS,[0122h], outside this probe slice.
        before = (c.IP, c.DS, c.ES, c.flags)
        with self.assertRaisesRegex(UnsupportedOpcode, "opcode 8E /3 at 0100"):
            c.step()
        self.assertEqual((c.IP, c.DS, c.ES, c.flags), before)

    def test_pop_word_to_direct_memory_uses_stack_and_preserves_flags(self):
        c = CPU(); c.SS = 0x2000; c.DS = 0x3000; c.SP = 0x0100; c.flags = 0x0ED7
        c.write16(c.SS, c.SP, 0xBEEF)
        load(c, bytes.fromhex("8F 06 00 02"))
        c.step()
        self.assertEqual((c.SP, c.read16(c.DS, 0x0200), c.IP), (0x0102, 0xBEEF, 0x0104))
        self.assertEqual(c.flags, 0x0ED7)

    def test_pop_rm_rejects_nonzero_extension_before_changing_stack(self):
        c = CPU(); c.SS = 0x2000; c.DS = 0x3000; c.SP = 0x0100
        c.write16(c.SS, c.SP, 0xBEEF)
        load(c, bytes.fromhex("8F 0E 00 02"))  # POP /1 is undefined.
        before = (c.IP, c.SP, c.read16(c.SS, c.SP), c.read16(c.DS, 0x0200))
        with self.assertRaisesRegex(UnsupportedOpcode, "opcode 8F /1 at 0100"):
            c.step()
        self.assertEqual((c.IP, c.SP, c.read16(c.SS, c.SP), c.read16(c.DS, 0x0200)), before)

    def test_mov_segment_register_uses_ss_for_bp_based_word_destination(self):
        c = CPU(); c.DS = 0xAAAA; c.SS = 0x2000; c.BP = 3; c.SI = 4
        load(c, bytes.fromhex("8C 5A 02"))  # MOV [BP+SI+2], DS
        c.step()
        address = (0x2000 << 4) + 9
        self.assertEqual(bytes(c.memory[address:address + 2]), bytes.fromhex("AA AA"))
        self.assertEqual(c.DS, 0xAAAA)
        self.assertEqual(c.IP, 0x103)

    def test_mov_segment_register_word_store_wraps_at_20_bit_bus_boundary(self):
        c = CPU(); c.DS = 0xFFFF; c.ES = 0x1234
        load(c, bytes.fromhex("8C 06 0F 00"))
        c.step()
        self.assertEqual(c.memory[0xFFFFF], 0x34)
        self.assertEqual(c.memory[0], 0x12)

    def test_segment_override_prefix_selects_cs_for_memory_source(self):
        c = CPU(); c.DS = 0x2000; c.CS = 0x1000; c.IP = 0x0100
        c.memory[c.linear(c.CS, c.IP):c.linear(c.CS, c.IP) + 5] = bytes.fromhex(
            "2E 8B 06 20 01"
        )
        c.write16(c.CS, 0x0120, 0xCAFE)
        c.write16(c.DS, 0x0120, 0xBEEF)
        c.step()
        self.assertEqual(c.AX, 0xCAFE)
        self.assertEqual(c.IP, 0x0105)

    def test_segment_override_prefix_is_restored_on_unsupported_opcode(self):
        c = CPU(); c.CS = 0x1000; c.IP = 0x0100
        c.memory[c.linear(c.CS, c.IP):c.linear(c.CS, c.IP) + 2] = bytes.fromhex("2E 0F")
        with self.assertRaisesRegex(UnsupportedOpcode, "opcode 0F at 0100"):
            c.step()
        self.assertEqual(c.IP, 0x0100)

    def test_f7_test_immediate_updates_logic_flags_without_writing_operand(self):
        c = CPU(); c.DS = 0x1234; c.flags = 0x0ED7
        c.write16(c.DS, 0x0200, 0x0101)
        load(c, bytes.fromhex("F7 06 00 02 01 00"))  # TEST WORD PTR [0200h], 0001h
        c.step()
        self.assertEqual(c.read16(c.DS, 0x0200), 0x0101)
        self.assertEqual(c.IP, 0x106)
        self.assertFalse(c.flag("CF")); self.assertFalse(c.flag("OF"))
        self.assertFalse(c.flag("ZF")); self.assertFalse(c.flag("SF"))
        self.assertFalse(c.flag("PF"))

    def test_f7_test_zero_result_sets_zero_and_parity_flags(self):
        c = CPU(); c.AX = 0x0100
        load(c, bytes.fromhex("F7 C0 01 00"))  # TEST AX, 0001h
        c.step()
        self.assertTrue(c.flag("ZF")); self.assertTrue(c.flag("PF"))
        self.assertFalse(c.flag("CF")); self.assertFalse(c.flag("OF"))
        self.assertEqual(c.AX, 0x0100)

    def test_f7_rejects_unimplemented_group_extension_without_state_change(self):
        c = CPU(); c.AX = 0x1234; c.flags = 0x0ED7
        load(c, bytes.fromhex("F7 D0"))  # /2 is outside the supported TEST subset.
        before = (c.AX, c.flags)
        with self.assertRaisesRegex(UnsupportedOpcode, "F7 /2 at 0100"):
            c.step()
        self.assertEqual(c.IP, 0x100)
        self.assertEqual((c.AX, c.flags), before)

    def test_mov_segment_register_rejects_reserved_segment_selector_before_mutation(self):
        c = CPU(); c.AX = 0x1234; c.flags = 0x0ED7
        load(c, bytes.fromhex("8C E0"))  # Reserved ModRM segment field /4.
        before = (c.AX, c.BX, c.CX, c.DX, c.flags, bytes(c.memory[0x10000:0x10002]))
        with self.assertRaisesRegex(UnsupportedOpcode, "8C /4 at 0100"):
            c.step()
        self.assertEqual(c.IP, 0x100)
        self.assertEqual((c.AX, c.BX, c.CX, c.DX, c.flags,
                          bytes(c.memory[0x10000:0x10002])), before)

    def test_mov_segment_register_rejects_out_of_bounds_word_destination(self):
        c = CPU(memory=bytearray(0x10000)); c.CS = 0x0100; c.IP = 0x0100; c.DS = 0x1000
        c.memory[0x1100:0x1104] = bytes.fromhex("8C 06 00 00")
        c.ES = 0xBEEF; c.flags = 0x0ED7
        before = (c.AX, c.BX, c.CX, c.DX, c.ES, c.DS, c.SS, c.flags,
                  bytes(c.memory[0x1100:0x1104]))
        with self.assertRaisesRegex(UnsupportedOpcode, "out of bounds at 1000:0000"):
            c.step()
        self.assertEqual(c.IP, 0x0100)
        self.assertEqual((c.AX, c.BX, c.CX, c.DX, c.ES, c.DS, c.SS, c.flags,
                          bytes(c.memory[0x1100:0x1104])), before)

    def test_or_ax_and_je_cover_entry_success_continuation(self):
        c = CPU(); c.AX = 1
        load(c, bytes.fromhex("09 C0 74 02 B8 34 12"))
        c.run(2)
        self.assertFalse(c.flag("ZF"))
        self.assertEqual(c.IP, 0x104)  # JE not taken; execution falls through to MOV.

    def test_all_short_conditional_branches_match_flag_truth_tables(self):
        def expected(opcode, cf, pf, zf, sf, of):
            return (
                of, not of, cf, not cf, zf, not zf, cf or zf, not cf and not zf,
                sf, not sf, pf, not pf, sf != of, sf == of, zf or sf != of,
                not zf and sf == of,
            )[opcode - 0x70]

        flag_positions = {"CF": 0, "PF": 2, "ZF": 6, "SF": 7, "OF": 11}
        for opcode in range(0x70, 0x80):
            for values in product((False, True), repeat=5):
                flags = 0x0002
                selected = dict(zip(("CF", "PF", "ZF", "SF", "OF"), values))
                for name, value in selected.items():
                    if value:
                        flags |= 1 << flag_positions[name]
                c = CPU(); c.flags = flags
                load(c, bytes((opcode, 0xFE)))
                c.step()
                self.assertEqual(c.IP, 0x100 if expected(opcode, *values) else 0x102)
                self.assertEqual(c.flags, flags)

    def test_inc_dec_all_register_encodings_and_preserve_carry(self):
        c = CPU(); c.BX = 0xFFFF; c.SI = 0; c.set_flag("CF", True)
        load(c, bytes.fromhex("43 4E"))  # INC BX; DEC SI
        c.run(2)
        self.assertEqual((c.BX, c.SI), (0, 0xFFFF))
        self.assertTrue(c.flag("CF"))
        self.assertTrue(c.flag("SF"))
        self.assertFalse(c.flag("ZF"))

    def test_retf_pops_far_frame_and_retf_immediate_discards_arguments(self):
        c = CPU(); c.SS = 0x2000; c.SP = 0x0100
        c.CS = 0x3000; c.IP = 0x0200
        c.push(0x0200)  # Callback's single Pascal argument.
        c.call_far(0x1000, 0x0400)
        start = c.linear(c.CS, c.IP)
        c.memory[start:start + 3] = bytes.fromhex("CA 02 00")
        c.step()
        self.assertEqual((c.CS, c.IP, c.SP), (0x3000, 0x0200, 0x0100))

    def test_unknown_opcode_fails_closed_without_advancing_ip(self):
        c = CPU(); load(c, b"\x0f")
        before = (c.AX, c.BX, c.flags, c.SP)
        with self.assertRaisesRegex(UnsupportedOpcode, "0F"):
            c.step()
        self.assertEqual(c.IP, 0x100)
        self.assertEqual((c.AX, c.BX, c.flags, c.SP), before)

    def test_unsupported_interrupt_vector_restores_instruction_state(self):
        c = CPU(); c.AX = 0x1234; c.flags = 0x0ED7; c.SP = 0x0100
        load(c, bytes.fromhex("CD 10"))
        before = (c.AX, c.BX, c.flags, c.SP)
        with self.assertRaisesRegex(UnsupportedOpcode, "INT 10"):
            c.step()
        self.assertEqual(c.IP, 0x100)
        self.assertEqual((c.AX, c.BX, c.flags, c.SP), before)


if __name__ == "__main__":
    unittest.main()

