#!/usr/bin/env python3
r"""Enable uncompressed DIB conversion and shadow-screen blits in the 8088 stage.

Call port(renderer, repo) AFTER build.prepare() and PORT8086.port(). Only
staged files are changed. The original DDK and frozen V1 remain untouched.

DDAG31.TXT lines 1543-1545 documents why RC_DI_BITMAP matters: without it GDI
simulates DIB conversion using monochrome bitmaps. Export the DDK's memory
conversion entry points 19 and 20 and a new shadow-only entry 21.
RC_DIBTODEV uses SDIB88, never the original hardware DISCREEN module.
BMC_ETI/ITE retain the DDK's scan-interleaved small/huge bitmap layouts,
DIB DWORD pitch and bottom-up scan handling. SDIB88 bounds temporary storage
to a private 1064-byte header/palette and one four-plane row (at most 16 KiB).

Only BI_RGB (the complete biCompression DWORD == 0) is supported. All RLE
and other compressed formats return AX=0 before any transfer or output-header
mutation. No RLEBitBlt import or hardware EGA conversion path is linked.

CPU audit: every immediate multi-bit shift in these modules uses shiftl/shiftr
from the already audited, staged MACROS.INC. Direct shifts use count 1 or CL.
The numeric tables are color thresholds and pixel-expansion data, never code;
address tables target ordinary audited routines. There is no generated-code
path. The full MASM listings must still pass AUDIT88, and the integrated build
must account for all 27 linked objects through the OMF/MAP closure audit.
"""
from pathlib import Path
import hashlib
import re

# SHA-256 of Latin-1 source after CRLF and DOS EOF normalization.
# BMC includes are already pinned by PORT8086; no new unique include is needed.
EXPECTED = {
    "BMC_MAIN.ASM": "1f2da6bb6d9a3b1132015b3dced43cac50f6a7e67dd4258397d6e3fe639e1270",
    "BMC_ETI.ASM": "a042ad920ca232006a1dddf64e98f5f56dd7c1ae4be9fdee332c5a138fd80d13",
    "BMC_ITE.ASM": "aed252ef7b98acfdfc7f5166b6c129163d64a5e68ebe5d79e07fcc4babc4d782",
    "EGA/EGA.ASM": "47650bfde2109e816fb22d3c9d595a6832bd11e1311dccd5f45eca7bd944719a",
}
# Fail before editing unless the strict 8086 macro port really ran. Shared
# unmodified includes and assembler definitions are verified by PORT8086.
STAGED_REQUIRED = {
    "INC/CMACROS.INC": "28282d158c0cabaa730479a8dcfd544e88e70a60870d48eb638731175ed160f2",
    "MACROS.INC": "c3087f15c6e8d4e4a6ce4c61a867d3a74ff4d8433d13f387139099338c79cf21",
    "DISPLAY.INC": "204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a",
    "MFLAGS.INC": "4b052ddc2d394daf575b8b2950c1f8ed6be2e546fb9066b82746a9d1863b1825",
    "LINES.INC": "9fcfd68bffb0c34c9f54601ded798da6923a3c6ac3f4df7421c00df2e8a0018d",
}
MODULES = ("BMC_MAIN", "BMC_ETI", "BMC_ITE", "SDIB88")


def normalized(path):
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\x1a", b"").decode("latin1")


def write_dos(path, text):
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1"))


def replace(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        raise RuntimeError(f"DIB patch mismatch: {old!r}: {found}, expected {count}")
    return text.replace(old, new)


def checked(path, expected):
    text = normalized(path)
    actual = hashlib.sha256(text.encode("latin1")).hexdigest()
    if actual != expected:
        raise RuntimeError(f"Unaudited DIB input {path}: {actual}; expected {expected}")
    return text


def port(renderer: Path, repo: Path):
    """Modify a fresh strict-8086 stage and return machine-readable audit facts."""
    renderer, repo = Path(renderer), Path(repo)
    original = {}
    for name, expected in EXPECTED.items():
        # Verify both the tracked provenance and the unmodified staged input.
        checked(repo / "DDK/286/DISPLAY/4PLANE" / name, expected)
        original[name] = checked(renderer / name, expected)
    for name, expected in STAGED_REQUIRED.items():
        checked(renderer / name, expected)
    changed = {}
    changed["SDIB88.ASM"] = normalized(repo / "src/tandysw/SDIB88.ASM")

    text = original["BMC_MAIN.ASM"]
    text = replace(text, "\texternFP\tRLEBitBlt\t\t; in ./rlebm.asm\n", "")
    text = replace(text, "\tlocalV\tRLEClipRect,8\t\t; clipping rectangle for RLE\n", "")
    first = "; if the DIB is RLE encoded or wants the RLE encoding back, call off to"
    start = text.index(first)
    stop = text.index("format_error:", start)
    # JMP is near; only the local JZ needs a short displacement. AX is scratch
    # here and is overwritten by the existing set/get paths. DS:SI and ES:DI
    # still address the same bitmap descriptor and BITMAPINFOHEADER.
    text = text[:start] + """; Memory-only 8088 driver: reject all non-BI_RGB compression values.
; Read both WORDs; testing only the original low BYTE would accept 00000100h.
; No output bits or BITMAPINFOHEADER fields have been changed at this point.
;----------------------------------------------------------------------------;
    mov ax,word ptr es:[di].biCompression
    or ax,word ptr es:[di].biCompression+2
    jz short test_color
    jmp error_detected

""" + text[stop:]
    if re.search(r"^\s*(?:externFP|cCall)\s+RLEBitBlt\b", text, re.M | re.I):
        raise RuntimeError("Unexpected remaining RLE dependency")
    changed["BMC_MAIN.ASM"] = text

    # Exact palette segment from pinned EGA.ASM, including the NUMBER_PLANES
    # conditional. Our pinned DISPLAY.INC fixes that number at four. The
    # DWORDs are xxRRGGBB so their in-memory bytes form DIB B,G,R,0 entries.
    source = original["EGA/EGA.ASM"]
    start = source.index("createSeg  _DIMAPS,DIMapSeg,word,public,code")
    stop = source.index("sEnd\tDIMapSeg", start) + len("sEnd\tDIMapSeg")
    palette = source[start:stop]
    palette = replace(palette, "DIMapSeg_color_table label\tdword",
                      "public DIMapSeg_color_table\nDIMapSeg_color_table label\tdword")
    text = normalized(renderer / "EGA/TSOFT.ASM")
    text = replace(text,
        "dw RC_BITBLT+RC_BITMAP64+RC_GDI20_OUTPUT+RC_OP_DX_OUTPUT",
        "dw RC_BITBLT+RC_BITMAP64+RC_GDI20_OUTPUT+RC_OP_DX_OUTPUT+RC_DI_BITMAP+RC_DIBTODEV")
    text = replace(text, "end driver_initialization",
                   palette + "\n\nend driver_initialization")
    changed["EGA/TSOFT.ASM"] = text

    text = normalized(renderer / "EGA/TSOFT.DEF")
    text = replace(text, " _SHADOW PRELOAD FIXED\n",
                   " _SHADOW PRELOAD FIXED\n _DIMAPS PRELOAD FIXED SHARED\n")
    text = replace(text, " SetAttribute @18 NODATA\n",
                   " SetAttribute @18 NODATA\n DeviceBitmapBits @19\n CreateBitmap @20\n DIBScreenBlt @21\n")
    changed["EGA/TSOFT.DEF"] = text

    text = normalized(renderer / "EGA/TSOFT.LNK")
    text = replace(text, "fb.obj lodither.obj tcursor.obj\n",
        "fb.obj lodither.obj tcursor.obj +\nbmc_main.obj bmc_eti.obj bmc_ite.obj sdib88.obj\n")
    changed["EGA/TSOFT.LNK"] = text
    text = normalized(renderer / "BLDCOR.BAT")
    commands = "".join(
        "C:\\BIN\\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T "
        + "..\\" + name.lower() + ".asm," + name.lower()
        + ".obj," + name.lower() + ".lst; >> BUILD0.LOG\n"
        for name in MODULES)
    text = replace(text, "echo DONE >> BUILD0.LOG\n", commands + "echo DONE >> BUILD0.LOG\n")
    changed["BLDCOR.BAT"] = text

    for name, text in changed.items():
        write_dos(renderer / name, text)
    return {
        "feature": "uncompressed DIB conversion and shadow-backed screen transfer",
        "pinned_new_ddk_inputs": len(EXPECTED),
        "shared_includes": "all previously pinned by PORT8086; strict staged macros verified",
        "patched_files": sorted(changed),
        "new_objects": [name + ".OBJ" for name in MODULES],
        "exports": {"19": "DeviceBitmapBits", "20": "CreateBitmap", "21": "DIBScreenBlt"},
        "capability": "RC_DI_BITMAP | RC_DIBTODEV (shadow-only)",
        "screen_bridge_sha256": hashlib.sha256(changed["SDIB88.ASM"].encode("latin1")).hexdigest(),
        "screen_temporary_storage": "1064-byte private header/palette plus one four-plane row <=16384 bytes",
        "screen_mapping": "bottom-up supplied band; signed clipping against 320x200 and caller rectangle; one FlushShadow",
        "compression": "BI_RGB only; complete nonzero biCompression DWORD returns AX=0",
        "raw_data_audit": "pixel/threshold data and routine-address tables only; no code templates",
        "include_path_requirement": "R:\\INC must precede C:\\DDK\\286\\INC",
    }
