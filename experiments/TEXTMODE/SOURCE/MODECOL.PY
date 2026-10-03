#!/usr/bin/env python3
"""Stage the four-color contract without modifying the DDK or frozen V1.

Call port(renderer, repo, profile) after build.prepare(), PORT8086.port(),
and PORTDIB.port(). Geometry, GDI NUMCOLORS, palette hardware programming,
and shadow flush belong to MODEPROF, not this module.

The logical DDB stays four-plane, one bit/plane. Canonical color indices are
0,5,10,15: redundant copies of the two physical bits. Every per-plane ROP
preserves that invariant. All sixteen raw DDB index values have defined
low-two-bit aliases on GetPixel, IndexToColor and 1/4/8/24-bit DIB export.
RGB DIB import, ColorInfo, pens and solid/hatch brushes produce canonical
indices. Color pattern brushes also canonicalize their two unused planes.

The first milestone uses nearest solid colors, not sixteen-color dithering.
The original monochrome brush dither remains available. Enumerate four
actual solid colors rather than the old 125-color dithered-brush promise.

Indexed DIB export must retain sixteen RGBQUAD entries: canonical indices
5,10,15 remain legal pixel values despite the four distinct display colors.
GETCOLORTABLE and object enumeration instead expose a dense four-entry table.
DIB imports with all sixteen source colors quantize through sum_RGB_alt_far.
Two fixed palettes are supported: black/cyan/magenta/white ([0,11,13,15])
and black/red/green/white ([0,12,10,15]). Idealized DDK RGB uses 0/255,
while physical RGBI levels include an 85 component for high-intensity colors.
Nearest monochrome uses the selected palette color's unweighted RGB sum:
white iff R+G+B >= 383. This is exact nearest squared-distance to black/white.
Thus cyan/magenta map to white, red/green map to black. The same rule controls
ColorInfo/IndexToColor accelerators, pattern monochrome and DIB mono export.
Color-to-mono BitBlt instead uses equality to the caller's background color.

Raw noncanonical DDB uploads retain their four-plane bytes. ScanLR/FloodFill
and color-to-mono BitBlt compare only C0/C1, making aliases equivalent even
when the upper two planes differ. Storage/row addressing remains four-plane.
"""
from pathlib import Path
import hashlib
import re

PALETTE = ((0, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 255))
INDICES = (0, 5, 10, 15)
HARDWARE = (0, 11, 13, 15)
PALETTE_RG = ((0, 0, 0), (255, 0, 0), (0, 255, 0), (255, 255, 255))
HARDWARE_RG = (0, 12, 10, 15)
PALETTES = {HARDWARE: PALETTE, HARDWARE_RG: PALETTE_RG}
EXPECTED = {
    "COLORS.ASM": "c351302b2c5ce2b09a4c9e26df3d35edfee23d75f1a1e1567c65d04b58a8082b",
    "ROBJECT.ASM": "482f446663655827b4f66ccdd4c00da8c40e565bb645e0e110e51bdeebe7663e",
    "ENUM.ASM": "b875948da157f1ed4f50707c64d1038635dea7b6df0e363383e7972391896c44",
    "BMC_ITE.ASM": "aed252ef7b98acfdfc7f5166b6c129163d64a5e68ebe5d79e07fcc4babc4d782",
    "CBLT.ASM": "c29c238b411c5da98115157b522c9483db6bd86495dd72f266c2609af1ddbc3f",
    "SCANLR.ASM": "6dbc1d6d2af95f4796cb164ccdfc3795a6254ebd9721a8f881bd56739a2113da",
}


def normalized(path):
    return Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\x1a", b"").decode("latin1")


def write_dos(path, value):
    Path(path).write_bytes(value.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1"))


def replace(text, old, new, count=1):
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"Four-color patch mismatch: {old!r}: {actual}, expected {count}")
    return text.replace(old, new)


def checked(path, expected):
    value = normalized(path)
    actual = hashlib.sha256(value.encode("latin1")).hexdigest()
    if actual != expected:
        raise RuntimeError(f"Unaudited four-color input {path}: {actual}; expected {expected}")
    return value


def span(text, first, last):
    if text.count(first) != 1 or text.count(last) != 1:
        raise RuntimeError(f"Four-color section mismatch: {first!r}, {last!r}")
    start = text.index(first)
    stop = text.index(last, start)
    return text[start:stop]


def nearest_index(red, green, blue, palette=PALETTE):
    """Independent, explicit squared-distance specification for test oracles."""
    if any(not isinstance(v, int) or not 0 <= v <= 255 for v in (red, green, blue)):
        raise ValueError("RGB components must be integers in 0..255")
    rgb = (red, green, blue)
    return INDICES[min(range(4), key=lambda i: sum((a-b)**2 for a, b in zip(rgb, palette[i])))]


def decode_index(index, palette=PALETTE):
    return palette[index & 3]


def mono_index(index, palette=PALETTE):
    """Nearest black/white from selected physical color, not background match."""
    return int(sum(decode_index(index, palette)) >= 383)


def accelerators(index, palette=PALETTE):
    return (0x10 if mono_index(index, palette) else 0) | (0x20 if index in (0, 15) else 0)


def dd_table(label, colors, dib=False):
    result = label + "\n; Four-color profile: logical RGB; raw DDB aliases follow low two bits.\n"
    for rgb in colors:
        r, g, b = rgb
        value = ((r << 16) | (g << 8) | b) if dib else ((b << 16) | (g << 8) | r)
        result += f"    dd 0{value:08x}h\n"
    return result + "\n"


def port(renderer, repo, profile):
    """Patch a fresh audited stage atomically with respect to validation."""
    if profile["colors"] != 4:
        return {"feature": "four-color mapping", "changed": False}
    hardware = tuple(profile["palette"])
    if hardware not in PALETTES:
        raise ValueError("Four-color mapper requires [0,11,13,15] or [0,12,10,15]")
    palette = PALETTES[hardware]
    renderer, repo = Path(renderer), Path(repo)
    original = {}
    for name, sha in EXPECTED.items():
        checked(repo / "DDK/286/DISPLAY/4PLANE" / name,
                "92f6fcded6c321b44d6575e43f2880df50ddd3cf126bc6ca5f3a63657fcaaa58"
                if name == "ROBJECT.ASM" else
                "6f610b400220521739c9366fe10c2d6e8353d80ad6240649a868e9602bb3fee5"
                if name == "CBLT.ASM" else sha)
        original[name] = checked(renderer / name, sha)
    mapper = normalized(repo / "src/tandysw/MODECOL.ASM")
    marker = "MODECOL_RG equ 0 ; MODECOL.PY sets 1 for black/red/green/white"
    mapper = replace(mapper, marker, marker.replace("equ 0", "equ " + str(int(hardware == HARDWARE_RG))))
    changed = {"COLORS.ASM": mapper}
    driver = normalized(renderer / "EGA/TSOFT.ASM")
    baseline = normalized(repo / "src/tandysw/V1.ASM")
    if not re.search(r"^COLOR_FORMAT equ 0104h$", driver, re.M):
        raise RuntimeError("Four-color mapping requires retained 0104h DDB format")
    if "DIMapSeg_color_table label\tdword" not in driver:
        raise RuntimeError("PORTDIB must run before four-color mapping")

    # Use exact original table sections as anchors. Geometry may already vary.
    first, last = "PAccelTable label   byte", "PColorTable label   byte"
    old = span(baseline, first, last)
    new = first + "\n" + "".join(f"    db 0{accelerators(i, palette):02x}h\n" for i in range(16)) + "\n"
    driver = replace(driver, old, new)
    first, last = "PColorTable label   byte", ";----------------------------------------------------------------------------;\n; define two hack routines"
    old = span(baseline, first, last)
    new = first + "\n" + "".join("    db " + ",".join(str(v) for v in decode_index(i, palette)) + "\n" for i in range(16)) + "\n"
    driver = replace(driver, old, new)
    driver = replace(driver, "COLOR_TBL_SIZE\tequ\t16\t\t;16 entries in the table",
                     "COLOR_TBL_SIZE equ 4 ;four distinct colors for escape/enumeration")
    for first, last, colors in (
        ("PixelSeg_color_table\tlabel\tdword", "sEnd\tPixelSeg", [decode_index(i, palette) for i in range(16)]),
        ("BlueMoonSeg_color_table label\tdword", "sEnd\tBlueMoonSeg", palette),
    ):
        driver = replace(driver, span(baseline, first, last), dd_table(first, colors))
    # PORTDIB owns the staged RGBQUAD section; verify its full original source.
    source = normalized(repo / "DDK/286/DISPLAY/4PLANE/EGA/EGA.ASM")
    first, last = "DIMapSeg_color_table label\tdword", "sEnd\tDIMapSeg"
    driver = replace(driver, span(source, first, last),
                     dd_table(first, [decode_index(i, palette) for i in range(16)], dib=True))
    driver = replace(driver, "    cmp si,16\n    jae control_done",
                     "    cmp si,COLOR_TBL_SIZE\n    jae control_done")
    changed["EGA/TSOFT.ASM"] = driver

    text = original["ROBJECT.ASM"]
    first = "\tpush\tax\t\t\t\n\tpush\tdx\t\t\t;save logical colors"
    last = "; Fill the brush with the solid color."
    old = span(text, first, last)
    text = replace(text, old, """; Four-color profile: nearest solid, never the old sixteen-color dither.
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
mc_index_plane:
    mov cx,4
    shr dh,1
    sbb ax,ax
    rep stosw
    dec bx
    jnz mc_index_plane
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
    new = old + """; Copy C0/C1 over C2/C3 before deriving monochrome pattern bits.
    push ds
    push si
    push di
    mov ax,es
    mov ds,ax
    lea si,[di][-4*SIZE_PATTERN]
    sub di,2*SIZE_PATTERN
    mov cx,SIZE_PATTERN
    rep movsw
    pop di
    pop si
    pop ds
"""
    text = replace(text, old, new)
    changed["ROBJECT.ASM"] = text

    # Enumerate real, available colors instead of 125 nominal dither colors.
    text = original["ENUM.ASM"]
    first = "\tmov\tsi,NUMBER_GREYS \t\t;Initialize red   index"
    last = ";\tNow enumerate the hatched brushes."
    old = span(text, first, last)
    new = """; Four-color profile exposes exactly the four nearest-solid choices.
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
                   "".join(f"    db {mono_index(i, palette)}\n" for i in range(16)) + "\n")
    changed["BMC_ITE.ASM"] = text

    # Treat all raw DDB aliases identically in color-to-mono BitBlt.
    # Generate only C1/C0 comparisons. Four-plane address/loop handling
    # elsewhere is unchanged. Every emitted opcode is already an audited
    # 8086 GENCONST instruction; generated length is derived from DI.
    text = original["CBLT.ASM"]
    first = "cblt_3080:\n"
    last = "\tmov\tax,I_LODSB+(I_XOR_AL_BYTE_I*256)\n"
    old = span(text, first, last)
    new = """cblt_3080:
; Four-color memory compare ignores the redundant/aliased C2 and C3.
; Emitted: MOV AH,[SI+plane_w]; XOR AX,C1mask*256;
; then existing LODSB; XOR AL,C0mask; OR AL,AH; NOT AL.
    mov ax,I_MOV_AH_SI_DISP16
    stosw
    mov ax,gl_src.plane_w
    stosw
    mov al,I_XOR_AX_WORD_I
    stosb
    mov ah,[si].SPECIAL
    and ah,C1_BIT
    neg ah
    sbb ah,ah
    xor al,al
    stosw
"""
    text = replace(text, old, new)
    changed["CBLT.ASM"] = text

    # ScanLR backs FloodFill. Compare low two planes, retaining COLOR_OP=4,
    # four-plane row multiplication and next_plane=bmWidthBytes unchanged.
    text = original["SCANLR.ASM"]
    first = "\tshr\tal,1\t\t\t;Bit expand C2."
    last = "\tmov\tdx,bx\t\t\t;DL = first byte mask"
    text = replace(text, span(text, first, last),
                   "; Four-color aliases compare only the C1/C0 mask.\n")
    for label, end in (("scan_120:\n", "\tmov\tah,[si] \t\t;Get C1 byte"),
                       ("scan_140:\n", "\tmov\tah,[si] \t\t;Get C1's color")):
        text = replace(text, span(text, label, end), label +
                       "    add si,bx ; locate C1; C2/C3 are irrelevant aliases\n")
    text = replace(text, "\tor\tal,dh\t\t\t;Combine with previous saved colors\n", "")
    text = replace(text, "\tor\tal,dh\t\t\t;Get C2 and C3 result\n", "")
    changed["SCANLR.ASM"] = text

    for name, value in changed.items():
        write_dos(renderer / name, value)
    return {
        "feature": "four physical colors with redundant four-plane DDB indices",
        "changed": True,
        "patched_files": sorted(changed),
        "logical_rgb": palette,
        "hardware_palette": hardware,
        "canonical_indices": INDICES,
        "raw_ddb_aliases": "index & 3; readback, ScanLR and color-to-mono BitBlt agree",
        "ddb_format": "4 planes, 1 bit per pixel per plane (0104h)",
        "color_quantization": "nearest RGB squared distance; ties in physical palette order",
        "mono_quantization": "nearest black/white of selected palette color; RGB sum >= 383",
        "brushes": "nearest solid color; monochrome dithering retained; hatch/pattern canonical",
        "public_palette_entries": 4,
        "dib_indexed_palette_entries": 16,
        "dib_formats": "1/4/8/24-bit BI_RGB imports and exports use the same palette",
        "cpu": "8086 mapper; CBLT emits audited MOV/XOR/LODSB/OR/NOT opcodes",
        "mapper_sha256": hashlib.sha256(changed["COLORS.ASM"].encode("latin1")).hexdigest(),
    }
