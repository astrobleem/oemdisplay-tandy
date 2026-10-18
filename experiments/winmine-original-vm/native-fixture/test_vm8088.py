from __future__ import annotations

import re
import unittest
from pathlib import Path


AX, CX, DX, BX, SP = 0, 1, 2, 3, 4
VM_STACK_WORDS = 8
GETVERSION_IMPORT = 1
SOURCE = Path(__file__).with_name("W16APIN.C")


class UnsupportedInstruction(RuntimeError):
    pass


def bytecode_array(name: str) -> bytes:
    source = SOURCE.read_text(encoding="ascii")
    match = re.search(
        rf"static const BYTE {re.escape(name)}\[\]\s*=\s*\{{(.*?)\}};",
        source,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing C bytecode array {name}")
    body = re.sub(r"/\*.*?\*/|//[^\r\n]*", "", match.group(1), flags=re.DOTALL)
    values = re.findall(r"0x([0-9A-Fa-f]{2})\b", body)
    if not values:
        raise AssertionError(f"empty C bytecode array {name}")
    return bytes(int(value, 16) for value in values)


def run_reference(
    program: bytes,
    *,
    callback_args: tuple[int, int, int] | None = None,
    getversion: int = 0x06160003,
) -> dict[str, object]:
    """Host oracle for the exact C bytecode arrays and the C decoder subset."""
    registers = [0] * 8
    stack = [0] * VM_STACK_WORDS
    registers[SP] = VM_STACK_WORDS
    if callback_args is not None:
        hwnd, lparam, stop_mode = callback_args
        for word in (
            stop_mode,
            (lparam >> 16) & 0xFFFF,
            lparam & 0xFFFF,
            hwnd & 0xFFFF,
        ):
            registers[SP] -= 1
            stack[registers[SP]] = word & 0xFFFF

    ip = 0
    zero = False
    steps = 0
    api_calls: list[str] = []

    def fetch8() -> int:
        nonlocal ip
        if ip >= len(program):
            raise UnsupportedInstruction("fetch beyond bytecode")
        value = program[ip]
        ip += 1
        return value

    def fetch16() -> int:
        low = fetch8()
        high = fetch8()
        return (high << 8) | low

    for _ in range(64):
        opcode = fetch8()
        steps += 1
        if 0x58 <= opcode <= 0x5F:
            reg = opcode - 0x58
            if reg == SP or registers[SP] >= VM_STACK_WORDS:
                raise UnsupportedInstruction("invalid POP stack/register")
            registers[reg] = stack[registers[SP]]
            registers[SP] += 1
        elif 0xB8 <= opcode <= 0xBF:
            reg = opcode - 0xB8
            if reg == SP:
                raise UnsupportedInstruction("MOV SP immediate is outside subset")
            registers[reg] = fetch16()
        elif opcode == 0x81:
            modrm = fetch8()
            if (modrm & 0xC0) != 0xC0 or ((modrm >> 3) & 7) != 7:
                raise UnsupportedInstruction("only register CMP /7 is supported")
            reg = modrm & 7
            zero = registers[reg] == fetch16()
        elif opcode in (0x74, 0x75):
            displacement = fetch8()
            if displacement & 0x80:
                displacement -= 0x100
            take = zero if opcode == 0x74 else not zero
            if take:
                target = ip + displacement
                if not 0 <= target < len(program):
                    raise UnsupportedInstruction("branch outside bytecode")
                ip = target
        elif opcode == 0xCD:
            interrupt = fetch8()
            if interrupt != 0xFF or registers[AX] != GETVERSION_IMPORT:
                raise UnsupportedInstruction("unknown software interrupt/import")
            api_calls.append("GetVersion")
            registers[AX] = getversion & 0xFFFF
            registers[DX] = (getversion >> 16) & 0xFFFF
        elif opcode == 0xF4:
            return {
                "registers": registers,
                "stack_pointer": registers[SP],
                "steps": steps,
                "api_calls": api_calls,
            }
        else:
            raise UnsupportedInstruction(f"opcode 0x{opcode:02X}")
    raise UnsupportedInstruction("instruction limit exceeded")


class VM8088DifferentialTests(unittest.TestCase):
    def test_version_bytecode_uses_getversion_import_bridge(self) -> None:
        state = run_reference(bytecode_array("g_version_bytecode"))
        regs = state["registers"]
        version = (regs[DX] << 16) | regs[AX]
        self.assertEqual(version, 0x06160003)
        self.assertEqual(state["api_calls"], ["GetVersion"])
        self.assertEqual(state["stack_pointer"], VM_STACK_WORDS)

    def test_callback_bytecode_reads_stack_arguments_and_cookie(self) -> None:
        state = run_reference(
            bytecode_array("g_callback_bytecode"),
            callback_args=(0x1090, 0x13579BDF, 0),
        )
        self.assertEqual(state["registers"][AX], 1)
        self.assertEqual(state["stack_pointer"], VM_STACK_WORDS)

    def test_wrong_cookie_and_stop_mode_return_false(self) -> None:
        program = bytecode_array("g_callback_bytecode")
        bad_cookie = run_reference(program, callback_args=(0x1090, 0x13579BDE, 0))
        stop_first = run_reference(program, callback_args=(0x1090, 0x13579BDF, 1))
        self.assertEqual(bad_cookie["registers"][AX], 0)
        self.assertEqual(stop_first["registers"][AX], 0)
        self.assertEqual(bad_cookie["stack_pointer"], VM_STACK_WORDS)
        self.assertEqual(stop_first["stack_pointer"], VM_STACK_WORDS)

    def test_null_window_returns_false(self) -> None:
        state = run_reference(
            bytecode_array("g_callback_bytecode"),
            callback_args=(0, 0x13579BDF, 0),
        )
        self.assertEqual(state["registers"][AX], 0)

    def test_unknown_opcode_fails_closed(self) -> None:
        with self.assertRaisesRegex(UnsupportedInstruction, "0x90"):
            run_reference(bytecode_array("g_unsupported_bytecode"))

    def test_unknown_import_fails_closed(self) -> None:
        with self.assertRaisesRegex(UnsupportedInstruction, "unknown software interrupt"):
            run_reference(bytes((0xB8, 0x02, 0x00, 0xCD, 0xFF, 0xF4)))


if __name__ == "__main__":
    unittest.main()
