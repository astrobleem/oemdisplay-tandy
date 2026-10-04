#!/usr/bin/env python3
"""Stage the two-color contract without modifying the DDK or frozen V1.

Call port(renderer, repo, profile) after build.prepare(), PORT8086.port(),
PORTDIB.port() and MODEEXT.port(). MODEPROF owns geometry, GDI and resources.
The 640x200x2 screen retains four scan-interleaved one-bit DDB planes and a
64000-byte shadow; C0 alone is visible. Canonical indices 0/15 duplicate C0
through all planes and are closed under every per-plane Boolean ROP.

All raw indices alias by index & 1 in GetPixel, IndexToColor, DIB exports,
ScanLR/FloodFill and color-to-mono BitBlt. RGB import/ColorInfo/pens/brushes
map to the squared-distance-nearest black/white solid. Color pattern brushes
canonicalize C1/C2/C3 from C0. Indexed exports retain sixteen RGBQUAD slots
because canonical white index 15 is legal; public enumeration has two colors.

The separate fifth brush plane intentionally retains the DDK monochrome-DC
weighted luminance dither. It cannot feed the color screen's four planes.
Pure black/white brushes are solid in all five planes; indexed/pattern brush
monochrome bits follow their low-bit alias. The sixteen-color color dither
is unreachable. No GUI, physical hardware or broad Windows acceptance claim
is implied by this source transform or its isolated machine-code tests.
"""
from pathlib import Path
import hashlib
import re

PALETTE = ((0, 0, 0), (255, 255, 255))
INDICES = (0, 15)
HARDWARE = (0, 15)
EXPECTED = {
    "COLORS.ASM": "c351302b2c5ce2b09a4c9e26df3d35edfee23d75f1a1e1567c65d04b58a8082b",
    "ROBJECT.ASM": "482f446663655827b4f66ccdd4c00da8c40e565bb645e0e110e51bdeebe7663e",
    "ENUM.ASM": "b875948da157f1ed4f50707c64d1038635dea7b6df0e363383e7972391896c44",
    "BMC_ITE.ASM": "aed252ef7b98acfdfc7f5166b6c129163d64a5e68ebe5d79e07fcc4babc4d782",
    "CBLT.ASM": "c29c238b411c5da98115157b522c9483db6bd86495dd72f266c2609af1ddbc3f",
    "SCANLR.ASM": "6dbc1d6d2af95f4796cb164ccdfc3795a6254ebd9721a8f881bd56739a2113da",
}


MAPPER_SHA256 = '0a8f957047ac728a24c2314be9dafeba30e996dd367ad8c8033ea24ce6fdf57f'
SOURCE_PINS = {'src/tandysw/V1.ASM': '01c453c170e60e505d4ac2a9d0705c95feaa6d2448dec7a9cc7b96b62ccac608', 'DDK/286/DISPLAY/4PLANE/EGA/EGA.ASM': '47650bfde2109e816fb22d3c9d595a6832bd11e1311dccd5f45eca7bd944719a', 'DDK/286/DISPLAY/4PLANE/DITHER.ASM': '5aaa67fc03cce208a2b4ed1085dc93008586f781007d4d429d10b79c2e791d92'}


def normalized(path):
    return Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\x1a", b"").decode("latin1")


def write_dos(path, value):
    Path(path).write_bytes(value.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1"))


def replace(text, old, new, count=1):
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"Two-color patch mismatch: {old!r}: {actual}, expected {count}")
    return text.replace(old, new)


def checked(path, expected):
    value = normalized(path)
    actual = hashlib.sha256(value.encode("latin1")).hexdigest()
    if actual != expected:
        raise RuntimeError(f"Unaudited two-color input {path}: {actual}; expected {expected}")
    return value


def span(text, first, last):
    if text.count(first) != 1 or text.count(last) != 1:
        raise RuntimeError(f"Two-color section mismatch: {first!r}, {last!r}")
    start = text.index(first)
    stop = text.index(last, start)
    return text[start:stop]


def nearest_index(red, green, blue):
    """Independent, explicit squared-distance specification for test oracles."""
    if any(not isinstance(v, int) or not 0 <= v <= 255 for v in (red, green, blue)):
        raise ValueError("RGB components must be integers in 0..255")
    rgb = (red, green, blue)
    return INDICES[min(range(2), key=lambda i: sum((a-b)**2 for a, b in zip(rgb, PALETTE[i])))]


def decode_index(index):
    return PALETTE[index & 1]


def accelerators(index):
    return (0x10 if index & 1 else 0) | (0x20 if index in (0, 15) else 0)


def dd_table(label, colors, dib=False):
    result = label + "\n; Two-color profile: logical RGB; raw DDB aliases follow low bit.\n"
    for rgb in colors:
        r, g, b = rgb
        value = ((r << 16) | (g << 8) | b) if dib else ((b << 16) | (g << 8) | r)
        result += f"    dd 0{value:08x}h\n"
    return result + "\n"


def port(renderer, repo, profile):
    """Patch a fresh audited stage atomically with respect to validation."""
    if profile["colors"] != 2:
        return {"feature": "two-color mapping", "changed": False}
    if tuple(profile["palette"]) != HARDWARE:
        raise ValueError("Two-color mapper requires Tandy palette [0,15]")
    renderer, repo = Path(renderer), Path(repo)
    for name, sha in SOURCE_PINS.items():
        checked(repo / name, sha)
    # The retained monochrome dither must still be the audited DDK version.
    checked(renderer / "DITHER.ASM", SOURCE_PINS["DDK/286/DISPLAY/4PLANE/DITHER.ASM"])
    original = {}
    for name, sha in EXPECTED.items():
        checked(repo / "DDK/286/DISPLAY/4PLANE" / name,
                "92f6fcded6c321b44d6575e43f2880df50ddd3cf126bc6ca5f3a63657fcaaa58"
                if name == "ROBJECT.ASM" else
                "6f610b400220521739c9366fe10c2d6e8353d80ad6240649a868e9602bb3fee5"
                if name == "CBLT.ASM" else sha)
        original[name] = checked(renderer / name, sha)
    changed = {"COLORS.ASM": checked(repo / "src/tandysw/MONOCOL.ASM", MAPPER_SHA256)}
    driver = normalized(renderer / "EGA/TSOFT.ASM")
    baseline = normalized(repo / "src/tandysw/V1.ASM")
    if not re.search(r"^COLOR_FORMAT equ 0104h$", driver, re.M):
        raise RuntimeError("Two-color mapping requires retained 0104h DDB format")
    if "DIMapSeg_color_table label\tdword" not in driver:
        raise RuntimeError("PORTDIB must run before two-color mapping")
    for anchor in ("SCREEN_WIDTH equ 640", "SCREEN_W_BYTES equ 80",
                   "shadow_bits db 64000 dup (0)", "    mov ax,0006h\n    int 10h\n"):
        if driver.count(anchor) != 1:
            raise RuntimeError("MODEEXT 640x200x2 must run before two-color mapping: " + anchor)

    # Use exact original table sections as anchors. Geometry may already vary.
    first, last = "PAccelTable label   byte", "PColorTable label   byte"
    old = span(baseline, first, last)
    new = first + "\n" + "".join(f"    db 0{accelerators(i):02x}h\n" for i in range(16)) + "\n"
    driver = replace(driver, old, new)
    first, last = "PColorTable label   byte", ";----------------------------------------------------------------------------;\n; define two hack routines"
    old = span(baseline, first, last)
    new = first + "\n" + "".join("    db " + ",".join(str(v) for v in decode_index(i)) + "\n" for i in range(16)) + "\n"
    driver = replace(driver, old, new)
    driver = replace(driver, "COLOR_TBL_SIZE\tequ\t16\t\t;16 entries in the table",
                     "COLOR_TBL_SIZE equ 2 ;two distinct colors for escape/enumeration")
    for first, last, colors in (
        ("PixelSeg_color_table\tlabel\tdword", "sEnd\tPixelSeg", [decode_index(i) for i in range(16)]),
        ("BlueMoonSeg_color_table label\tdword", "sEnd\tBlueMoonSeg", PALETTE),
    ):
        driver = replace(driver, span(baseline, first, last), dd_table(first, colors))
    # PORTDIB owns the staged RGBQUAD section; verify its full original source.
    source = normalized(repo / "DDK/286/DISPLAY/4PLANE/EGA/EGA.ASM")
    first, last = "DIMapSeg_color_table label\tdword", "sEnd\tDIMapSeg"
    driver = replace(driver, span(source, first, last),
                     dd_table(first, [decode_index(i) for i in range(16)], dib=True))
    driver = replace(driver, "    cmp si,16\n    jae control_done",
                     "    cmp si,COLOR_TBL_SIZE\n    jae control_done")
    changed["EGA/TSOFT.ASM"] = driver

    text = original["ROBJECT.ASM"]
    first = "\tpush\tax\t\t\t\n\tpush\tdx\t\t\t;save logical colors"
    last = "; Fill the brush with the solid color."
    old = span(text, first, last)
    text = replace(text, old, """; Two-color profile: nearest solid, never the old sixteen-color dither.
    cCall rgb_to_ipc
    mov brush_accel,dh

""")
    text = replace(text, last, "RSModeSolid:\n" + last)
    text = replace(text, "RSDitherBrush:\n\tcCall\tColorDither",
                   "RSDitherBrush:\n    jmp short RSModeSolid ; no noncanonical color dither")
    # This legacy indexed helper currently has no callers, but keep its
    # encoding/mono accelerator contract correct rather than leaving a trap.
    start = text.index("txrealize_solid_with_index proc\tnear")
    stop = text.index("txrealize_solid_with_index endp", start)
    text = text[:start] + """txrealize_solid_with_index proc near
    mov dh,al
    call IndexToColor             ; canonical index and mono accelerator
    mov dl,dh
    mov bx,4
bw_index_plane:
    mov cx,4
    shr dh,1
    sbb ax,ax
    rep stosw
    dec bx
    jnz bw_index_plane
    shr dh,1                     ; MONO_BIT after four color bits
    sbb ax,ax
    mov cx,4
    rep stosw
    or dl,SOLID_BRUSH
    mov bx,BS_SOLID
    ret
""" + text[stop:]
    # Normalize color pattern brushes, including caller-supplied raw DDBs.
    old = "\tor\tbx,bx\t\t\t;Monochrome?\n\tjz\trealize_pattern_10\t;  Yes, just copy mono data again\n"
    new = old + """; Propagate C0 over C1/C2/C3 using intentional forward overlap.
; The eighth source byte is consumed before it is reused in the next plane.
    push ds
    push si
    push di
    push cx
    push ax
    mov ax,es
    mov ds,ax
    lea si,[di][-4*SIZE_PATTERN]
    sub di,3*SIZE_PATTERN
    mov cx,3*SIZE_PATTERN/2
    rep movsw
    pop ax
    pop cx
    pop di
    pop si
    pop ds
"""
    text = replace(text, old, new)
    changed["ROBJECT.ASM"] = text

    # Enumerate real black/white solids instead of 125 nominal dither colors.
    text = original["ENUM.ASM"]
    first = "\tmov\tsi,NUMBER_GREYS \t\t;Initialize red   index"
    last = ";\tNow enumerate the hatched brushes."
    old = span(text, first, last)
    new = """; Two-color profile exposes exactly the two nearest-solid choices.
    lea di,obj_area.lbColor
    call do_color

"""
    text = replace(text, old, new)
    # Public debug symbols only exist in the old triple loop; remove those.
    for name in ("enum_brush_10", "enum_brush_20", "enum_brush_30"):
        text = replace(text, "\tpublic\t" + name + "\n", "")
    changed["ENUM.ASM"] = text

    # Indexed and RGB export already uses DIMapSeg; mono has a separate LUT.
    text = original["BMC_ITE.ASM"]
    first, last = "ColorToMono label byte", "\t.errnz\t(size RGBQuad)-4\n\n\tassumes ds,nothing"
    text = replace(text, span(text, first, last), first + "\n" +
                   "".join(f"    db {i & 1}\n" for i in range(16)) + "\n")
    changed["BMC_ITE.ASM"] = text

    # Emit only a C0 comparison. All instructions are audited 8086 opcodes;
    # code size is derived from DI and four-plane addressing stays unchanged.
    text = original["CBLT.ASM"]
    first = "cblt_3080:\n"
    last = "\tjmp\tshort cblt_3160\t\t;Go create logic code\n"
    old = span(text, first, last)
    new = """cblt_3080:
; Two-color memory compare ignores aliased C1/C2/C3.
; Emitted: LODSB; XOR AL,C0mask; NOT AL.
    mov ax,I_LODSB+(I_XOR_AL_BYTE_I*256)
    stosw
    mov al,[si].SPECIAL
    shr al,1
    sbb al,al
    .errnz C0_BIT - 00000001b
    stosb
    errnz pcol_C0
    mov ax,I_NOT_AL
    stosw
"""
    text = replace(text, old, new)
    changed["CBLT.ASM"] = text

    # ScanLR backs FloodFill. Compare C0 only, retaining COLOR_OP=4,
    # four-plane row multiplication and next_plane=bmWidthBytes unchanged.
    text = original["SCANLR.ASM"]
    first = "\tshr\tal,1\t\t\t;Bit expand C1."
    last = "\tmov\tdx,bx\t\t\t;DL = first byte mask"
    text = replace(text, span(text, first, last),
                   "    xor dh,dh ; high comparison byte unused\n"
                   "    mov C1C0,dx ; C0 expansion retained in low byte\n")
    first = "scan_120:\n"
    last = "\tor\tal,dh\t\t\t;Combine with previous saved colors\n"
    text = replace(text, span(text, first, last) + last, """scan_120:
    lodsb                        ; C0 only, respect the scan direction
    xor al,byte ptr C1C0          ; compare to low-bit alias

""")
    first = "scan_140:\n"
    last = "\txor\tal,dl\t\t\t;Invert if needed"
    text = replace(text, span(text, first, last), """scan_140:
    lodsb                        ; C0 only, respect the scan direction
    xor ax,bp                    ; only AL is consumed; BP low byte is C0
""")
    changed["SCANLR.ASM"] = text

    for name, value in changed.items():
        write_dos(renderer / name, value)
    return {
        "feature": "two physical colors with redundant four-plane DDB indices",
        "changed": True,
        "patched_files": sorted(changed),
        "logical_rgb": PALETTE,
        "hardware_palette": HARDWARE,
        "canonical_indices": INDICES,
        "raw_ddb_aliases": "index & 1; readback, ScanLR/FloodFill and color-to-mono BitBlt agree",
        "ddb_format": "4 planes, 1 bit per pixel per plane (0104h)",
        "color_quantization": "nearest RGB squared distance; white iff R+G+B >= 383; no integer ties",
        "brushes": "nearest solid color; fifth-plane mono-DC dithering retained; hatch/pattern canonical",
        "public_palette_entries": 2,
        "dib_indexed_palette_entries": 16,
        "dib_formats": "1/4/8/24-bit BI_RGB imports and exports use the same palette",
        "cpu": "8086 mapper; CBLT emits audited LODSB/XOR/NOT opcodes",
        "mapper_sha256": hashlib.sha256(changed["COLORS.ASM"].encode("latin1")).hexdigest(),
    }
