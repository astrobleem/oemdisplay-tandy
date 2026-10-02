#!/usr/bin/env python3
"""Check emitted instruction opcodes in MASM listings; data templates need separate review."""
from pathlib import Path
import json, re, sys
MNEMONICS = set("aaa aad aam aas adc add and call cbw clc cld cli cmc cmp cmps cmpsb cmpsw cwd daa das dec div hlt idiv imul in inc int into iret ja jae jb jbe jc jcxz je jg jge jl jle jmp jna jnae jnb jnbe jnc jne jng jnge jnl jnle jno jnp jns jnz jo jp jpe jpo js jz lahf lds lea les lods lodsb lodsw loop loope loopne loopnz loopz mov movs movsb movsw mul neg nop not or out pop popf push pushf rcl rcr ret retn retf rol ror sahf sal sar sbb scas scasb scasw shl shr stc std sti stos stosb stosw sub test wait xchg xlat xlatb xor rep repe repne repnz repz lock enter leave pusha popa bound ins insb insw outs outsb outsw".split())
BANNED = set(range(0x60,0x70)) | {0x0f,0xc0,0xc1,0xc8,0xc9,0xf1}
PREFIXES = {0x26,0x2e,0x36,0x3e,0xf0,0xf2,0xf3}

def audit(paths):
    bad, count, per_file = [], 0, {}
    for path in paths:
        local = 0
        for lineno, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
            line = raw.expandtabs(8)
            if not re.match(r"^ [0-9A-F]{4}  [0-9A-F]{2}", line):
                continue
            source = line[32:].strip().split(";",1)[0].strip()
            words = source.split()
            if words and words[0].endswith(":"):
                words = words[1:]
            if not words:
                continue
            mnemonic = words[0].lower()
            # MASM data/structure declarations may display values resembling
            # opcodes. Do not decode data as instructions.
            data_words = {"db", "dw", "dd", "dq", "dt", "bitmap", "bitmapinfoheader", "rgbquad", "rgbtriple", "bitmapcoreheader"}
            if mnemonic in data_words or (len(words)>1 and words[1].lower() in data_words):
                continue
            if mnemonic == "even":
                continue
            if mnemonic not in MNEMONICS and mnemonic != "out16":
                raise AssertionError("Unclassified emitted listing row: " + line)
            field = line[7:28]
            tokens = re.findall(r"[0-9A-F]{2,8}", field)
            if not tokens:
                raise AssertionError("No machine bytes: " + line)
            # Prefixes are individually printed. First opcode is the leading byte.
            index = 0
            while index < len(tokens) and len(tokens[index]) == 2 and int(tokens[index],16) in PREFIXES:
                index += 1
            if index == len(tokens):
                continue  # REP on a separate source line; following instruction is checked.
            opcode = int(tokens[index][:2],16)
            count += 1
            local += 1
            if opcode in BANNED:
                bad.append({"file":path.name,"line":lineno,"opcode":hex(opcode),"source":source})
        per_file[path.name] = local
    if not count:
        raise AssertionError("No emitted instructions found")
    report = {"emitted_instruction_rows_checked":count,"listing_counts":per_file,"unsupported":bad,
              "scope":"Emitted instruction rows, including macro expansions (some macro header rows repeat bytes). Numeric runtime-code templates are audited separately by PORT8086."}
    if bad:
        raise AssertionError(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    print(json.dumps(audit([Path(p) for p in sys.argv[1:]]), indent=2))
