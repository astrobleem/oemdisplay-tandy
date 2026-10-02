#!/usr/bin/env python3
r"""Deterministic 8086 port of the frozen V1 staged DDK renderer.

Call port(renderer, repo) immediately after build.prepare(). This never changes
tracked DDK files. Add R:\INC BEFORE the original DDK paths in SET INCLUDE.

The complete transitive linked DDK inputs are pinned, not just edited files:
assembler CPU selection cannot detect instructions emitted by a code generator.
In particular, CBLT used C0 /0,/1 rotate-immediate encodings, and SPECIAL relied
on the exact PUSHA frame and POPA preserving flags. All modifications here are
reviewed substitutions; unknown source revisions fail before any file is edited.
"""
from pathlib import Path
import hashlib
import re

# SHA-256 of latin-1 source after CRLF/EOF-marker normalization. These are the
# prepared V1 sources; three .286 directives and the published V1 repairs have
# already been applied by build.prepare(). TSOFT/TCURSOR are owned by the port.
EXPECTED = {
    'DDK/286/INC/WINDEFS.INC': 'ecd4e252ef72ce86bfa3559978abedf17159bce4a4bc2a20fb20547b60e5a63c',
    'BITBLT.ASM': '022198936174bb9876024f6cfd0482e055c05f5a40350104339f5d28057ee8a9',
    'CBLT.ASM': '6f610b400220521739c9366fe10c2d6e8353d80ad6240649a868e9602bb3fee5',
    'CHARWDTH.ASM': 'c90f9df1486a3971765b2455f3f18a08fa51412ad0388c1fffac21c451b62c47',
    'CHKSTK.ASM': 'df14a69cf7962b7ae91b2a0169553c5b6c172f7a405260bdc99c4aa7a82338b6',
    'CLIP.INC': '36d3fea586d2ea3178d4f12f9ecdb4e8619dadccdda9eb4ccef14aa1541359fe',
    'CLRCONST.INC': '89be6f9d7a6fd197c2ec8a499ff2a8de8024f0a859c967e58d7cdf6525e8110e',
    'CLRDATA.INC': '8019ef5bbf44e5f80b7260123ebbcb6a025622f355aa9e210d95e9d14b26d081',
    'CLRLOCAL.INC': 'ea638e526a898d9a869772058347f8db9ff7d68175c21357ca2706878bcdddb3',
    'COLORINF.ASM': '356e5b35921b6740d95eeb0a33694516490a9b59efe7c47a832371f6816a832b',
    'COLORS.ASM': 'c351302b2c5ce2b09a4c9e26df3d35edfee23d75f1a1e1567c65d04b58a8082b',
    'COMPUTEY.INC': 'ad8645b717da4e7c10c694f1bb2471d7770fadd855f0390d997a255190f54331',
    'COPYDEV.INC': 'b657ec8b263ad155bf184cfdbba4d27b560199bb9e88c5ab703d5e1be0749b50',
    'CURSOR.INC': '7468c11ab88bfbf4d1390acbf99b5062ba196f50ffb54a2c3ad7bd2213b322d1',
    'DDK/286/INC/CMACROS.INC': 'e94a181f3b6663c6ca2a633dde5f82d4eeb07f702ce8bc665222a95c93d5cf0e',
    'DDK/286/INC/GDIDEFS.INC': 'b77b7526aa77a7cf1d3dc3fc36ed8ec93012225b7e7d2244a51db42f5ea1f5d5',
    'DEBUG.INC': '1e6547e997f0536dc06a03f3f31a3b54e08d9e0b7c5bc7bccb12fd68d46501d3',
    'DEVCONST.INC': 'd3157dffbef0bd0e4a1c481507756a6f35f75d9e3e271e2d6c80246292077711',
    'DEVDATA.INC': '657197b584e52b142388711f797a065c0916a016483b38cb4307eba4142ed299',
    'DEVLOCAL.INC': 'f47aa7c68dda794e333ad80d922362e4272ba6a8f4317f415c9668f95098d1e3',
    'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a',
    'DITHER.ASM': '5aaa67fc03cce208a2b4ed1085dc93008586f781007d4d429d10b79c2e791d92',
    'DITHERS.ASM': '1a4400f0145d02a0ada9c783f1a8936bc8c60d9675f8fa969317c4fd2dd0c379',
    'DRAWMOD2.INC': 'b662c3ec11a13664e9ecbab8d00246e78f193431a3141f550fc107a6c5ffe751',
    'EGA.INC': '65eeea9b048d9087ea1e5a7eb07c16d7c43d10dd277269530d52650cbedf1be5',
    'EGAMEM.INC': '7576169eec54d3d5a3e580d984b3575f0af9074685a9ba737e21c0c7d19bb6b7',
    'ENUM.ASM': 'b875948da157f1ed4f50707c64d1038635dea7b6df0e363383e7972391896c44',
    'EXIT.INC': 'bb4c25f8d790ad7e3caa2f65fcac512849b0ac4cf28bf06df40361ef96d9b648',
    'FB.ASM': 'c6565d1e683dd1256acd670ef648dd534cc7b6c40499a3ab67e395aaf0d0602a',
    'FONTSEG.INC': '8f456a7d5d4a5227b009735b22ca2cd89d643d62ad5478f9dd7f1e44a51b65a9',
    'GENCONST.INC': 'cb6299bf0b59cf20a43fe33435da414b45e760d3bf5b2e5fed47133b29f1188b',
    'GENDATA.INC': '066dfb96d322c00f13e188de4435018bac332bb719ec61c738a277a30ab403e5',
    'GENLOCAL.INC': '1e431ef5d51c56917cfa5015ae168191e63c553f2a22400c6689bb6cc58f3f9f',
    'LINES.INC': '9fcfd68bffb0c34c9f54601ded798da6923a3c6ac3f4df7421c00df2e8a0018d',
    'MACROS.INC': '3dfd46e3c210f529b96626f43ef0f7489bf6482192851b3da22c297c4540b629',
    'MACROS.MAC': '3dfd46e3c210f529b96626f43ef0f7489bf6482192851b3da22c297c4540b629',
    'MFLAGS.INC': '4b052ddc2d394daf575b8b2950c1f8ed6be2e546fb9066b82746a9d1863b1825',
    'NJMP.INC': '210f4a4022ea705eb595c266f52563f062045ef9cd3f6343e647dd122ec72974',
    'OUTPUT.ASM': '936d80af4d305bb16b11c0203a15b4608375c4bf978f6a21077b82d70b7bd456',
    'PATTERN.INC': 'be8ef8f9016881b9efc70db9d378a0747d193ba592c6abdd1de58bd13496d1d9',
    'PDEVICE.INC': '1bdbb09b210445b8db18bf1316353813a3590d3d27d2bb4153440f3817f46c79',
    'PIXEL.ASM': 'f73cf8b9c368de5cb45c26533b22104ab5232c9f438ff292610fb2006d5d4ae3',
    'PLYSOLID.INC': '155b52efabff31575baa0473bcf8f52884cbea973b1f7def145c5a76f87559e0',
    'POLYBITM.INC': '24310589f5be7ca98c5b3756255f49b42129821f3be7908e1c337c70e59573df',
    'POLYLINE.ASM': '9d92a41aaddf8131c14049c178ecf3835eaf7d2b546ab04ea3c1f349fac841bc',
    'POLYLINE.INC': '20c102845353101ff643b4e2e9c7432ad9d2b0f40155feeb2f36bd4196a401b4',
    'POLYSTYL.INC': 'b5f43b951677291c8020deeb1f5dbf186afa6d143326a0e73e208f825406d11c',
    'REALFIX.ASM': '1e3147c562b7030d6604e91bac8ace22f930042eda55550ad5886f212a704eaa',
    'REALPRO.ASM': 'dd37d57d044d5deeecf39546a272dc0c68dcb1c6a0f634568423c24afaa63377',
    'RLBLDSTR.ASM': '08c4b7801813c4d3295eec2b568fcb14de3e4fed5c7977328551c17d1512dd95',
    'RLBLDSTR.PUB': '57eb95a88dd13f9c8ab4fabdd7730c7026cdcf8d44353963bc47f850ab6f1aaa',
    'RLFNTSEG.INC': 'fa96a66f89f307fa675674e4a422dacd19751ae7cb07c711c1cdd34dd904a73d',
    'RLSTRBLT.ASM': 'fefe2d4f4df13b138d9c15ab52aff6bb9e543a26d4c4f99ba962a735738c2f2a',
    'RLSTRBLT.INC': '22f742fc5e7acd5fdb208776217d86cb7ef50f7275a6139cf6c64217fa1f3252',
    'RLSTRBLT.PUB': 'c7adcb4e31798c8d16a289255348ef16eb26ddab7dfda3ee6d635fea97ebf6a0',
    'ROBJECT.ASM': '482f446663655827b4f66ccdd4c00da8c40e565bb645e0e110e51bdeebe7663e',
    'ROPDEFS.INC': 'd1f9186e23d71c87eaa24e395b14c31639031b7445c0d89083f0861e7adab4ed',
    'ROPTABLE.INC': 'a77c680ba180eb55f8815ae066762344f1cb803ca972fd376f409fccc82f5593',
    'SCANLINE.ASM': 'f1ba086a7ac163e353ac3523dd41bebc9ea380078af787c566f8cfd3470c0d30',
    'SCANLR.ASM': '6dbc1d6d2af95f4796cb164ccdfc3795a6254ebd9721a8f881bd56739a2113da',
    'SETMODE.ASM': 'bae325fd0fac848d14817b4d37ad1191f183541f13f77f139faf974372c2be5f',
    'SPECIAL.INC': 'b1a21333277072d0718970acf5d3146d2c792f61af88978b55d83fac71cbe811',
}


def normalized(path):
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\x1a", b"").decode("latin1")


def write_dos(path, value):
    path.write_bytes(value.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1"))


def replace(text, old, new, count=1):
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"Port patch mismatch: {old!r}: {actual}, expected {count}")
    return text.replace(old, new)


# PUSH SP differs between an 8086 and later CPUs. Do not use it. LEA and MOV
# recover original SP without modifying flags or the original BX register.
# Final offsets: DI 0, SI 2, BP 4, original SP 6, BX 8, DX 10, CX 12, AX 14.
PUSHA86 = """push ax
    push cx
    push dx
    push bx
    mov bx,sp
    lea bx,[bx+8]
    push bx
    mov bx,sp
    mov bx,ss:[bx+2]
    push bp
    push si
    push di"""
# POPA ignores the original SP word. A dummy POP rather than ADD SP preserves
# flags, required by the JZ immediately following an original POPA in SPECIAL.
POPA86 = """pop di
    pop si
    pop bp
    pop bx
    pop bx
    pop dx
    pop cx
    pop ax"""


def expand_pusha(text, mnemonic, expansion, expected):
    pattern = re.compile(r"^(\s*)" + mnemonic + r"\b([^\n]*)$", re.M | re.I)
    count = 0
    def one(match):
        nonlocal count
        count += 1
        return ("    ; 8086 equivalent of " + mnemonic.upper() + match[2] + "\n    "
                + expansion)
    result = pattern.sub(one, text)
    if count != expected:
        raise RuntimeError(f"Expected {expected} {mnemonic}, found {count}")
    return result


def expand_shifts(text, expected):
    # All immediate-count sites in these exact pinned files are plain-register
    # operands and counts 2/3/8. Repeated one-bit operations retain all defined
    # flags (OF was undefined for the original count > 1), and need no scratch
    # register. The final CF, SF, ZF and PF are the original instruction's values.
    pattern = re.compile(r"^([ \t]*)(shl|shr|sal|sar|rol|ror|rcl|rcr)[ \t]+"
                         r"([a-d][xhl]|[sd]i|[bs]p),[ \t]*([2-9])([ \t]*(?:;[^\n]*)?)$",
                         re.I | re.M)
    count = 0
    def one(match):
        nonlocal count
        count += 1
        indent, op, operand, amount, comment = match.groups()
        lines = [f"{indent}{op}\t{operand},1" for _ in range(int(amount))]
        lines[0] += comment + f" ; 8086: {amount} one-bit operations"
        return "\n".join(lines)
    result = pattern.sub(one, text)
    if count != expected:
        raise RuntimeError(f"Expected {expected} immediate shifts, found {count}")
    return result


def port(renderer: Path, repo: Path):
    """Port a fresh build.prepare stage; return machine-readable audit facts."""
    renderer, repo = Path(renderer), Path(repo)
    original = {}
    for name, expected in EXPECTED.items():
        path = repo / name if name.startswith("DDK/") else renderer / name
        text = normalized(path)
        actual = hashlib.sha256(text.encode("latin1")).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Unaudited 8086 input {name}: {actual}; expected {expected}")
        original[name] = text
    changed = {}

    # CMACROS uses IFDEF ?pmd, but ?pmd is defined even in REAL mode. Its .286p
    # therefore silently overrides an .8086 in the main source. Shadow it in
    # the stage and reject any request for the protected/386 prolog variants.
    text = original["DDK/286/INC/CMACROS.INC"]
    text = replace(text, ".286p", ".8086")
    text = """; 8086-only real-mode driver: reject alternate CPU/code-generation modes.
.8086
ifdef PMODE
.err
endif
ifdef ?386regs
if ?386regs
.err
endif
endif
ifdef TEFTI
.err
endif
""" + text
    # These are unreachable when PMODE is absent. Replacing them by explicit
    # assembler errors prevents a future macro change from quietly selecting
    # an incompatible prolog/epilog even if the top guard is bypassed.
    text = replace(text, "enter ???,0", ".err ; protected-mode ENTER is forbidden", 2)
    text = re.sub(r"^leave$", ".err ; protected-mode LEAVE is forbidden", text, flags=re.M)
    changed["INC/CMACROS.INC"] = text

    for name in ("MACROS.INC", "MACROS.MAC"):
        text = replace(original[name], ".286", ".8086")
        text = replace(text, "CPU\tequ\tGENERIC", "CPU\tequ\t88")
        for op in ("shl", "shr", "rcr", "rcl", "rol", "ror", "sar"):
            old = ("if (CPU eq 286) or (CPU eq 386)\n\t" + op + "\tDEST,COUNT\nelse\n"
                   "\tREPT\tCOUNT\n\t" + op + "\tDEST,1\n\tENDM\nendif")
            new = "\tREPT\tCOUNT\n\t" + op + "\tDEST,1\n\tENDM"
            text = replace(text, old, new)
        changed[name] = text

    shift_counts = {"BITBLT.ASM": 1, "CBLT.ASM": 1, "RLSTRBLT.ASM": 6,
                    "RLBLDSTR.ASM": 3, "SPECIAL.INC": 6}
    for name, count in shift_counts.items():
        changed[name] = expand_shifts(original[name], count)
    changed["BITBLT.ASM"] = replace(changed["BITBLT.ASM"], ".286p", ".8086")

    for name, pushes, pops in (("SPECIAL.INC", 4, 5), ("DEBUG.INC", 1, 1)):
        text = changed.get(name, original[name])
        text = expand_pusha(text, "pusha", PUSHA86, pushes)
        text = expand_pusha(text, "popa", POPA86, pops)
        changed[name] = text
    # Save-all expansion lengthens the backward flash-check branch beyond rel8.
    changed["SPECIAL.INC"] = replace(changed["SPECIAL.INC"],
        "\tja\tSHORT EGA_Src_Check_Flash",
        "\tjbe\tSHORT EGA_Src_No_Flash\n\tjmp\tEGA_Src_Check_Flash")

    # Eight run_the_dda macro instantiations push an immediate return address.
    # A CS-relative literal after the unconditional indirect JMP preserves all
    # registers and flags and remains unreachable as code. Each expansion has
    # its own LOCAL label; no cross-procedure address or assumed scratch reg.
    text = original["POLYLINE.ASM"]
    text = replace(text, "\tlocal\ttop_of_run", "\tlocal\ttop_of_run,port8086_dda_return")
    text = replace(text,
        "\tpush\tLineSegOFFSET top_of_run\n\tjmp\tS1\t\t\t; CX = number of pixels to draw",
        "\tpush\tword ptr cs:port8086_dda_return\n"
        "\tjmp\tS1\t\t\t; CX = number of pixels to draw\n"
        "port8086_dda_return dw LineSegOFFSET top_of_run")
    changed["POLYLINE.ASM"] = text

    # AX is already saved by the DebugErr save-all frame, so using it for these
    # arguments does not change DebugErr's register-preservation contract.
    text = changed["DEBUG.INC"]
    text = replace(text, "        push    offset a", "        mov     ax,offset a\n        push    ax")
    text = replace(text, "        push    flags or DBF_GDI",
                   "        mov     ax,flags or DBF_GDI\n        push    ax")
    changed["DEBUG.INC"] = text

    # Memory PUSH is native 8086, does not change registers or flags, and keeps
    # the delimiter's exact stack position. Put its immutable word in rCode.
    text = changed["RLBLDSTR.ASM"]
    text = replace(text, "\tpush\t0ffffh", "\tpush\tword ptr cs:port8086_delimiter", 2)
    text = replace(text, "sEnd\trCode", "port8086_delimiter dw 0ffffh\n\nsEnd\trCode")
    changed["RLBLDSTR.ASM"] = text

    # IMPORTANT: .8086 cannot reject raw opcodes emitted at run time. Generate
    # D0 C0/D0 C8 once per rotate instead of C0 C0/C0 C8 + immediate. CX is zero
    # on entry and after REP; AX still holds the chosen opcode. All downstream
    # offsets and copy lengths derive from DI rather than a hardcoded 3 bytes.
    text = changed["CBLT.ASM"]
    text = replace(text, "I_ROL_AL_N", "I_ROL_AL_1", 2)
    text = replace(text, "I_ROR_AL_N", "I_ROR_AL_1", 2)
    text = replace(text,
        "\tstosw\t\t\t\t;Stuff the phase alignment rotates\n"
        "\tmov\tal,cl\t\t\t;  then the phase alignment code\n\tstosb",
        "\trep\tstosw\t\t\t;8086: emit CL count-one rotates; CX=0")
    changed["CBLT.ASM"] = text
    text = original["GENCONST.INC"]
    for symbol in ("I_ROL_AL_N", "I_ROR_AL_N", "I_FS_OVERRIDE", "I_GS_OVERRIDE"):
        text, count = re.subn(r"^" + symbol + r"\s+equ[^\n]*\n", "", text, flags=re.M)
        if count != 1:
            raise RuntimeError("Unexpected generated-opcode definition: " + symbol)
    changed["GENCONST.INC"] = text
    # At most seven alignment copies: two initial, four inner-loop, one last.
    # Worst growth 7*(8-3)=35, plus inner LOOP 4, plane JNC 3, and
    # outer LOOP 4 when each switches to its long form: 46, rounded up to 48.
    changed["DEVCONST.INC"] = replace(original["DEVCONST.INC"],
        "MAX_BLT_SIZE\t=\t452\t\t;Max stack space a BLT will require",
        "; 8086: <=35 extra rotate bytes, <=11 extra branch bytes (round to 48).\n"
        "MAX_BLT_SIZE\t=\t500\t\t;Original 452 plus 48-byte 8086 allowance")

    for name, text in changed.items():
        path = renderer / name
        path.parent.mkdir(parents=True, exist_ok=True)
        write_dos(path, text)
    return {
        "cpu": "8086/8088", "mode": "Windows real mode",
        "pinned_ddk_inputs": len(EXPECTED),
        "patched_files": sorted(changed),
        "immediate_shift_sites": sum(shift_counts.values()),
        "pusha_sites": 5, "popa_sites": 6, "push_immediate_sites": 5, "push_immediate_instantiations": 12,
        "generated_rotate": "D0 C0/D0 C8 repeated min(phase, 8-phase) times",
        "max_blt_size": 500,
        "include_path_requirement": "R:\\INC must precede C:\\DDK\\286\\INC",
    }


def audit_link(renderer: Path, additional_objects=()):
    """Prove no library executable/data contribution escapes the OBJ audit.

    Parse 16-bit OMF SEGDEF/LNAMES records from every explicit LNK input, apply
    each contribution's actual alignment in input order, and compare the totals
    with the final MAP. The import libraries may supply import records, but any
    extra CODE/DATA bytes (including an unlisted runtime helper) fail this test.
    """
    ega = Path(renderer) / "EGA"
    objects = re.findall(r"\b([a-z0-9_]+\.obj)\b", normalized(ega / "TSOFT.LNK"), re.I)
    base_objects = "TSOFT BITBLT CBLT POLYLINE SCANLINE OUTPUT PIXEL SCANLR RLSTRBLT RLBLDSTR REALFIX REALPRO DITHERS ROBJECT COLORINF ENUM COLORS SETMODE CHKSTK CHARWDTH FB LODITHER TCURSOR".split()
    expected = [name + ".OBJ" for name in base_objects] + [name.upper() for name in additional_objects]
    if len(set(expected)) != len(expected) or len(objects) != len(expected) or {name.upper() for name in objects} != set(expected):
        raise RuntimeError("Unexpected linked object set")
    totals = {}
    details = []
    def omf_index(data, position):
        first = data[position]
        if first & 128:
            return ((first & 127) << 8) | data[position+1], position+2
        return first, position+1
    for name in objects:
        raw = (ega / name.upper()).read_bytes()
        offset, names, contributions = 0, [""], []
        while offset < len(raw):
            if offset + 3 > len(raw):
                raise RuntimeError("Truncated OMF: " + name)
            kind = raw[offset]
            size = int.from_bytes(raw[offset+1:offset+3], "little")
            if size < 1 or offset+3+size > len(raw):
                raise RuntimeError("Invalid OMF record: " + name)
            data = raw[offset+3:offset+2+size]  # exclude record checksum
            offset += 3+size
            if kind == 0x96:  # LNAMES
                position = 0
                while position < len(data):
                    length = data[position]
                    names.append(data[position+1:position+1+length].decode("ascii"))
                    position += 1+length
                if position != len(data):
                    raise RuntimeError("Invalid OMF names: " + name)
            elif kind == 0x99 or kind in (0xC2, 0xC3):
                raise RuntimeError("Unreviewed 32-bit segment/COMDAT: " + name)
            elif kind == 0x98:  # 16-bit SEGDEF
                attribute = data[0]
                alignment_code, combine = attribute >> 5, (attribute >> 2) & 7
                position = 1 + (3 if alignment_code == 0 else 0)
                length = int.from_bytes(data[position:position+2], "little")
                position += 2
                name_index, position = omf_index(data, position)
                class_index, position = omf_index(data, position)
                key = (names[name_index], names[class_index].upper())
                if key[1] not in ("CODE", "DATA"):
                    continue
                if alignment_code not in (1, 2, 3, 4, 5) or combine != 2 or attribute & 3:
                    raise RuntimeError("Unreviewed OMF segment attributes: " + repr((name, key, attribute)))
                alignment = {1: 1, 2: 2, 3: 16, 4: 256, 5: 4}[alignment_code]
                start = totals.get(key, 0)
                start = ((start + alignment-1) // alignment) * alignment
                totals[key] = start + length
                contributions.append({"segment": key[0], "class": key[1],
                                      "start": start, "bytes": length, "alignment": alignment})
        details.append({"object": name.upper(), "contributions": contributions})
    # LINK4 aligns even zero-length contributions and treats CODE class names
    # case-insensitively. Only nonempty final segments appear in this comparison.
    totals = {key: value for key, value in totals.items() if value}
    mapped = {}
    for length, name, kind in re.findall(
            r"^\s+[0-9A-F]{4}:[0-9A-F]{4}\s+([0-9A-F]+)H\s+(\S+)\s+(CODE|DATA)\s*$",
            normalized(ega / "TSOFT.MAP"), flags=re.I | re.M):
        if int(length, 16):
            key = (name, kind.upper())
            if key in mapped:
                raise RuntimeError("Duplicate nonempty MAP segment: " + name)
            mapped[key] = int(length, 16)
    if not mapped or totals != mapped:
        raise RuntimeError("Unaccounted linked CODE/DATA bytes: objects=" + repr(totals) + "; map=" + repr(mapped))
    return {"result": "PASS", "explicit_objects": len(objects), "extra_library_code_bytes": 0,
            "segments": [{"name": key[0], "class": key[1], "bytes": value}
                         for key, value in sorted(totals.items())], "objects": details}
