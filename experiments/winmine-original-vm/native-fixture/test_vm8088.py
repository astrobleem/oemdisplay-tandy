from __future__ import annotations

import re
import unittest
from pathlib import Path


AX, CX, DX, BP, SP = 0, 1, 2, 5, 4
STACK_WORDS = 8
CODE_SELECTOR = 0x1000
IMPORT_SELECTOR = 0xF001
GETVERSION_OFFSET = 1
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


def run_vm(
    program: bytes,
    *,
    callback_args: tuple[int, int, int] | None = None,
    getversion: int = 0x06160003,
) -> dict[str, object]:
    """Host reference for the C fixture's deliberately small 8088 subset.

    GetVersion is a deterministic test value here. This oracle checks the VM
    bytecode contract only; it does not model the Python Win16Host API bridge.
    """
    registers = [0] * 8
    stack = [0] * STACK_WORDS
    registers[SP] = STACK_WORDS
    if callback_args is not None:
        hwnd, lparam, stop_mode = callback_args
        registers[CX] = stop_mode & 0xFFFF
        for word in (hwnd & 0xFFFF, (lparam >> 16) & 0xFFFF, lparam & 0xFFFF):
            registers[SP] -= 1
            stack[registers[SP]] = word

    ip = 0
    cs = CODE_SELECTOR
    zero = False
    steps = 0
    far_calls = 0
    far_returns = 0
    last_return_cs = 0
    last_return_ip = 0
    last_retf_bytes = 0
    api_calls: list[str] = []

    def fetch8() -> int:
        nonlocal ip
        if cs != CODE_SELECTOR or not 0 <= ip < len(program):
            raise UnsupportedInstruction(f"fetch outside code at {cs:04X}:{ip:04X}")
        value = program[ip]
        ip += 1
        return value

    def fetch16() -> int:
        low = fetch8()
        high = fetch8()
        return (high << 8) | low

    def push(value: int) -> None:
        if registers[SP] <= 0 or registers[SP] > STACK_WORDS:
            raise UnsupportedInstruction("stack overflow")
        registers[SP] -= 1
        stack[registers[SP]] = value & 0xFFFF

    def pop() -> int:
        if registers[SP] >= STACK_WORDS:
            raise UnsupportedInstruction("stack underflow")
        value = stack[registers[SP]]
        registers[SP] += 1
        return value

    def far_return(argument_bytes: int) -> None:
        nonlocal cs, ip, far_returns, last_return_cs, last_return_ip, last_retf_bytes
        if argument_bytes & 1:
            raise UnsupportedInstruction("odd RETF argument size")
        return_ip = pop()
        return_cs = pop()
        if registers[SP] + argument_bytes // 2 > STACK_WORDS:
            raise UnsupportedInstruction("RETF stack adjustment overflow")
        registers[SP] += argument_bytes // 2
        cs, ip = return_cs, return_ip
        far_returns += 1
        last_return_cs, last_return_ip = return_cs, return_ip
        last_retf_bytes = argument_bytes

    for _ in range(64):
        if cs == IMPORT_SELECTOR:
            if ip != GETVERSION_OFFSET:
                raise UnsupportedInstruction(f"unknown far import {cs:04X}:{ip:04X}")
            api_calls.append("GetVersion")
            registers[AX] = getversion & 0xFFFF
            registers[DX] = (getversion >> 16) & 0xFFFF
            far_return(0)
            steps += 1
            continue
        if cs != CODE_SELECTOR:
            raise UnsupportedInstruction(f"unknown selector 0x{cs:04X}")

        opcode = fetch8()
        steps += 1
        if 0x58 <= opcode <= 0x5F:
            reg = opcode - 0x58
            if reg == SP:
                raise UnsupportedInstruction("POP SP is outside subset")
            registers[reg] = pop()
        elif 0xB8 <= opcode <= 0xBF:
            reg = opcode - 0xB8
            if reg == SP:
                raise UnsupportedInstruction("MOV SP immediate is outside subset")
            registers[reg] = fetch16()
        elif opcode == 0x55:
            push(registers[BP])
        elif opcode in (0x89, 0x8B):
            modrm = fetch8()
            if (opcode == 0x89 and modrm != 0xE5) or (opcode == 0x8B and modrm != 0xEC):
                raise UnsupportedInstruction("unsupported MOV ModRM")
            registers[BP] = registers[SP]
        elif opcode in (0x81, 0x83):
            modrm = fetch8()
            mode = modrm >> 6
            if ((modrm >> 3) & 7) != 7:
                raise UnsupportedInstruction("unsupported group-1 operation")
            if mode == 3:
                compared = registers[modrm & 7]
            elif mode == 1 and (modrm & 7) == 6:
                displacement = fetch8()
                if displacement >= 0x80 or displacement & 1:
                    raise UnsupportedInstruction("invalid BP displacement")
                index = registers[BP] + displacement // 2
                if index >= STACK_WORDS:
                    raise UnsupportedInstruction("BP read outside stack")
                compared = stack[index]
            else:
                raise UnsupportedInstruction("unsupported CMP addressing mode")
            if opcode == 0x81:
                immediate = fetch16()
            else:
                value = fetch8()
                immediate = value if value < 0x80 else 0xFF00 | value
            zero = compared == immediate
        elif opcode in (0x74, 0x75):
            displacement = fetch8()
            if displacement & 0x80:
                displacement -= 0x100
            if (zero if opcode == 0x74 else not zero):
                target = ip + displacement
                if not 0 <= target < len(program):
                    raise UnsupportedInstruction("branch outside bytecode")
                ip = target
        elif opcode == 0x9A:
            target_ip = fetch16()
            target_cs = fetch16()
            push(cs)
            push(ip)
            far_calls += 1
            cs, ip = target_cs, target_ip
        elif opcode == 0xCD:
            interrupt = fetch8()
            if interrupt != 0xFF or registers[AX] != GETVERSION_IMPORT:
                raise UnsupportedInstruction("unknown software interrupt/import")
            api_calls.append("GetVersion")
            registers[AX] = getversion & 0xFFFF
            registers[DX] = (getversion >> 16) & 0xFFFF
        elif opcode in (0xCA, 0xCB):
            far_return(fetch16() if opcode == 0xCA else 0)
        elif opcode == 0xF4:
            return {
                "registers": registers,
                "stack": stack,
                "stack_pointer": registers[SP],
                "steps": steps,
                "cs": cs,
                "ip": ip,
                "far_calls": far_calls,
                "far_returns": far_returns,
                "last_return_cs": last_return_cs,
                "last_return_ip": last_return_ip,
                "last_retf_bytes": last_retf_bytes,
                "api_calls": api_calls,
            }
        else:
            raise UnsupportedInstruction(f"opcode 0x{opcode:02X}")
    raise UnsupportedInstruction("instruction limit exceeded")


class VM8088FarCallTests(unittest.TestCase):
    def test_far_getversion_import_returns_dx_ax_and_retf_to_caller(self) -> None:
        state = run_vm(bytecode_array("g_farcall_version_bytecode"))
        registers = state["registers"]
        self.assertEqual((registers[DX] << 16) | registers[AX], 0x06160003)
        self.assertEqual(state["api_calls"], ["GetVersion"])
        self.assertEqual(state["far_calls"], 1)
        self.assertEqual(state["far_returns"], 1)
        self.assertEqual(state["last_return_cs"], CODE_SELECTOR)
        self.assertEqual(state["last_return_ip"], 5)
        self.assertEqual(state["last_retf_bytes"], 0)
        self.assertEqual(state["stack_pointer"], STACK_WORDS)
        self.assertEqual((state["cs"], state["ip"]), (CODE_SELECTOR, 6))

    def test_callback_returns_retf6_and_restores_far_frame_and_bp(self) -> None:
        state = run_vm(
            bytecode_array("g_far_callback_bytecode"),
            callback_args=(0x1090, 0x13579BDF, 0),
        )
        registers = state["registers"]
        self.assertEqual(registers[AX], 1)
        self.assertEqual(registers[BP], 0)
        self.assertEqual(state["stack_pointer"], STACK_WORDS)
        self.assertEqual(state["far_calls"], 1)
        self.assertEqual(state["far_returns"], 1)
        self.assertEqual(state["last_retf_bytes"], 6)
        self.assertEqual(state["last_return_cs"], CODE_SELECTOR)
        self.assertEqual(state["last_return_ip"], 5)
        self.assertEqual((state["cs"], state["ip"]), (CODE_SELECTOR, 6))

    def test_callback_bad_cookie_null_window_and_stop_mode_return_false(self) -> None:
        program = bytecode_array("g_far_callback_bytecode")
        cases = (
            (0x1090, 0x13579BDE, 0),
            (0, 0x13579BDF, 0),
            (0x1090, 0x13579BDF, 1),
        )
        for args in cases:
            with self.subTest(args=args):
                state = run_vm(program, callback_args=args)
                self.assertEqual(state["registers"][AX], 0)
                self.assertEqual(state["stack_pointer"], STACK_WORDS)
                self.assertEqual(state["far_returns"], 1)
                self.assertEqual(state["last_retf_bytes"], 6)

    def test_unknown_far_selector_and_offset_fail_closed(self) -> None:
        unknown_selector = bytes((0x9A, 1, 0, 2, 0xF0, 0xF4))
        unknown_offset = bytes((0x9A, 2, 0, 1, 0xF0, 0xF4))
        for program in (unknown_selector, unknown_offset):
            with self.subTest(program=program):
                with self.assertRaisesRegex(UnsupportedInstruction, "far import|selector"):
                    run_vm(program)

    def test_legacy_smoke_bytecode_remains_available(self) -> None:
        state = run_vm(bytecode_array("g_version_bytecode"))
        self.assertEqual(state["api_calls"], ["GetVersion"])
        self.assertEqual(state["stack_pointer"], STACK_WORDS)

    def test_unsupported_instruction_still_fails_closed(self) -> None:
        with self.assertRaisesRegex(UnsupportedInstruction, "0x90"):
            run_vm(bytecode_array("g_unsupported_bytecode"))


if __name__ == "__main__":
    unittest.main()
