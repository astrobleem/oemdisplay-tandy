"""Small, strict host-side 8086/80186 interpreter subset for synthetic probes.

This is not a general x86 emulator. Unsupported instruction bytes raise
UnsupportedOpcode before any CPU state is changed by that instruction.
"""

from dataclasses import dataclass, field

MASK16 = 0xFFFF
REGS = ("AX", "CX", "DX", "BX", "SP", "BP", "SI", "DI")
SEGS = ("ES", "CS", "SS", "DS")
FLAG_BITS = {"CF": 0, "PF": 2, "AF": 4, "ZF": 6, "SF": 7,
             "TF": 8, "IF": 9, "DF": 10, "OF": 11}


class UnsupportedOpcode(RuntimeError):
    """Raised when this deliberately narrow interpreter sees unknown code."""


@dataclass
class CPU:
    memory: bytearray = field(default_factory=lambda: bytearray(1 << 20))
    AX: int = 0; BX: int = 0; CX: int = 0; DX: int = 0
    SP: int = 0; BP: int = 0; SI: int = 0; DI: int = 0
    CS: int = 0; DS: int = 0; ES: int = 0; SS: int = 0
    IP: int = 0
    flags: int = 0x0002

    def __post_init__(self):
        if len(self.memory) < 0x10000:
            raise ValueError("flat memory must be at least 64 KiB")

    def reg(self, n): return getattr(self, REGS[n])
    def set_reg(self, n, value): setattr(self, REGS[n], value & MASK16)
    def flag(self, name): return bool(self.flags & (1 << FLAG_BITS[name]))
    def set_flag(self, name, value):
        bit = 1 << FLAG_BITS[name]
        self.flags = (self.flags | bit) if value else (self.flags & ~bit)
        self.flags |= 2

    def linear(self, seg, off): return ((seg << 4) + (off & MASK16)) % len(self.memory)
    def read8(self, seg, off): return self.memory[self.linear(seg, off)]
    def read16(self, seg, off):
        return self.read8(seg, off) | (self.read8(seg, off + 1) << 8)
    def write8(self, seg, off, value): self.memory[self.linear(seg, off)] = value & 0xFF
    def write16(self, seg, off, value):
        self.write8(seg, off, value); self.write8(seg, off + 1, value >> 8)

    def fetch8(self):
        b = self.read8(self.CS, self.IP); self.IP = (self.IP + 1) & MASK16; return b
    def fetch16(self):
        lo = self.fetch8(); return lo | (self.fetch8() << 8)
    def push(self, value):
        self.SP = (self.SP - 2) & MASK16; self.write16(self.SS, self.SP, value)
    def pop(self):
        v = self.read16(self.SS, self.SP); self.SP = (self.SP + 2) & MASK16; return v
    def call_far(self, target_cs, target_ip):
        return_cs, return_ip = self.CS, self.IP
        self.push(return_cs); self.push(return_ip)
        self.CS, self.IP = target_cs & MASK16, target_ip & MASK16
    def far_return(self, argument_bytes=0):
        self.IP = self.pop(); self.CS = self.pop()
        self.SP = (self.SP + argument_bytes) & MASK16

    def _parity(self, value): return (value & 0xFF).bit_count() % 2 == 0
    def _logic_flags(self, result):
        r = result & MASK16
        self.set_flag("CF", False); self.set_flag("OF", False); self.set_flag("AF", False)
        self.set_flag("ZF", r == 0); self.set_flag("SF", bool(r & 0x8000)); self.set_flag("PF", self._parity(r))
    def _add(self, a, b):
        full = a + b; r = full & MASK16
        self.set_flag("CF", full > MASK16); self.set_flag("AF", ((a ^ b ^ r) & 0x10) != 0)
        self.set_flag("OF", ((~(a ^ b) & (a ^ r)) & 0x8000) != 0)
        self.set_flag("ZF", r == 0); self.set_flag("SF", bool(r & 0x8000)); self.set_flag("PF", self._parity(r))
        return r
    def _sub(self, a, b):
        r = (a - b) & MASK16
        self.set_flag("CF", a < b); self.set_flag("AF", ((a ^ b ^ r) & 0x10) != 0)
        self.set_flag("OF", (((a ^ b) & (a ^ r)) & 0x8000) != 0)
        self.set_flag("ZF", r == 0); self.set_flag("SF", bool(r & 0x8000)); self.set_flag("PF", self._parity(r))
        return r

    def _modrm(self):
        m = self.fetch8(); mod, reg, rm = m >> 6, (m >> 3) & 7, m & 7
        if mod == 3: return reg, ("r", rm)
        bases = ((self.BX + self.SI), (self.BX + self.DI), (self.BP + self.SI),
                 (self.BP + self.DI), self.SI, self.DI, self.BP, self.BX)
        uses_bp = rm in (2, 3, 6) and not (mod == 0 and rm == 6)
        if mod == 0 and rm == 6: off = self.fetch16()
        elif mod == 1:
            d = self.fetch8(); off = bases[rm] + (d - 256 if d & 0x80 else d)
        elif mod == 2:
            d = self.fetch16(); off = bases[rm] + (d - 65536 if d & 0x8000 else d)
        else: off = bases[rm]
        return reg, ("m", (self.SS if uses_bp else self.DS), off & MASK16)
    def _getop(self, op):
        return self.reg(op[1]) if op[0] == "r" else self.read16(op[1], op[2])
    def _setop(self, op, value):
        if op[0] == "r": self.set_reg(op[1], value)
        else: self.write16(op[1], op[2], value)

    def step(self):
        start = self.IP
        op = self.fetch8()
        if 0xB8 <= op <= 0xBF: self.set_reg(op - 0xB8, self.fetch16())                         # MOV r16,imm16
        elif 0x50 <= op <= 0x57: self.push(self.reg(op - 0x50))                              # PUSH r16
        elif 0x58 <= op <= 0x5F: self.set_reg(op - 0x58, self.pop())                         # POP r16
        elif op == 0x68: self.push(self.fetch16())                                           # 80186 PUSH imm16
        elif op == 0x6A:                                                                     # 80186 PUSH sign-extended imm8
            v = self.fetch8(); self.push(v - 256 if v & 0x80 else v)
        elif op == 0x6B:                                                                     # 80186 IMUL r16,r/m16,sign-extended imm8
            reg, src = self._modrm()
            imm = self.fetch8(); imm = imm - 256 if imm & 0x80 else imm
            a = self._getop(src); product = ((a if a < 0x8000 else a - 0x10000) * imm)
            self.set_reg(reg, product); overflow = not (-32768 <= product <= 32767)
            self.set_flag("CF", overflow); self.set_flag("OF", overflow)
        elif op in (0x89, 0x8B):                                                             # MOV r/m16,r16; MOV r16,r/m16
            reg, dst = self._modrm()
            if op == 0x89: self._setop(dst, self.reg(reg))
            else: self.set_reg(reg, self._getop(dst))
        elif op in (0x01, 0x03, 0x29, 0x2B, 0x31, 0x33, 0x39, 0x3B):                       # ADD/SUB/XOR/CMP
            reg, rm = self._modrm(); direction = op in (0x03, 0x2B, 0x33, 0x3B)
            dst, src = (self.reg(reg), self._getop(rm)) if direction else (self._getop(rm), self.reg(reg))
            base = op & 0xFC
            if base == 0x00: result = self._add(dst, src)
            elif base == 0x28: result = self._sub(dst, src)
            elif base == 0x30: result = dst ^ src; self._logic_flags(result)
            else: self._sub(dst, src); result = dst
            if base != 0x38:
                if direction: self.set_reg(reg, result)
                else: self._setop(rm, result)
        elif op in (0x09, 0x0B):                                                            # OR r/m16,r16; OR r16,r/m16
            reg, rm = self._modrm()
            if op == 0x09:
                result = self._getop(rm) | self.reg(reg)
                self._setop(rm, result)
            else:
                result = self.reg(reg) | self._getop(rm)
                self.set_reg(reg, result)
            self._logic_flags(result)
        elif op in (0x05, 0x2D, 0x3D):                                                       # ADD/SUB/CMP AX,imm16
            imm = self.fetch16()
            if op == 0x05: self.AX = self._add(self.AX, imm)
            else:
                r = self._sub(self.AX, imm)
                if op == 0x2D: self.AX = r
        elif op == 0x81:                                                                    # supported group-1 word immediate: /0,/5,/7
            subop, dst = self._modrm(); imm = self.fetch16(); value = self._getop(dst)
            if subop == 0: self._setop(dst, self._add(value, imm))
            elif subop in (5, 7):
                result = self._sub(value, imm)
                if subop == 5: self._setop(dst, result)
            else:
                self.IP = start
                raise UnsupportedOpcode(f"opcode 81 /{subop} at {start:04X}")
        elif op in (0x40, 0x48):                                                           # INC/DEC r16, preserve CF
            n = op & 7; cf = self.flag("CF")
            value = self._add(self.reg(n), 1) if op < 0x48 else self._sub(self.reg(n), 1)
            self.set_reg(n, value); self.set_flag("CF", cf)
        elif op == 0x90: pass                                                               # NOP
        elif op == 0xEB:                                                                    # JMP short
            d = self.fetch8(); self.IP = (self.IP + (d - 256 if d & 0x80 else d)) & MASK16
        elif op == 0x74:                                                                    # JE/JZ short
            d = self.fetch8()
            if self.flag("ZF"):
                self.IP = (self.IP + (d - 256 if d & 0x80 else d)) & MASK16
        elif op == 0xE9:
            d = self.fetch16(); self.IP = (self.IP + (d - 65536 if d & 0x8000 else d)) & MASK16
        elif op == 0xE8:
            d = self.fetch16(); self.push(self.IP); self.IP = (self.IP + (d - 65536 if d & 0x8000 else d)) & MASK16
        elif op == 0x9A:                                                                    # CALL FAR ptr16:16
            target_ip = self.fetch16(); target_cs = self.fetch16()
            self.call_far(target_cs, target_ip)
            return ("far_call", target_cs, target_ip)
        elif op == 0xC3: self.IP = self.pop()
        elif op == 0xCB:                                                                    # RETF
            self.far_return()
            return ("far_return", self.CS, self.IP)
        elif op == 0xCA:                                                                    # RETF imm16
            argument_bytes = self.fetch16()
            self.far_return(argument_bytes)
            return ("far_return", self.CS, self.IP)
        elif op == 0xCD:                                                                    # intercepted host interrupt
            vector = self.fetch8()
            if vector != 0xFF: raise UnsupportedOpcode(f"INT {vector:02X} at {start:04X}")
            return ("host_interrupt", vector)
        else:
            self.IP = start
            raise UnsupportedOpcode(f"opcode {op:02X} at {start:04X}")
        return ("instruction", op)

    def run(self, count, interrupt_handler=None, import_handler=None):
        for _ in range(count):
            event = self.step()
            if event[0] == "host_interrupt":
                if interrupt_handler is None: raise UnsupportedOpcode("host interrupt has no handler")
                interrupt_handler(self, event[1])
            elif event[0] == "far_call":
                if import_handler is None: raise UnsupportedOpcode("far call has no import handler")
                _, target_cs, target_ip = event
                import_handler(self, target_cs, target_ip)
                # The intercepted imported routine returns with RETF: pop IP,
                # then CS, leaving the caller's stack exactly as before CALL.
                self.far_return()


