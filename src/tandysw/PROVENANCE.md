# Provenance and publication scope

This directory is additive. It does not replace the existing src/tandy16 implementation, overwrite the user's newer local source, or import a whole working archive.

## Build baseline

Verified repository baseline:

    d57e9a2515391102d47849dc8878f95e9a07e703

The supplied newer local repository had the same Git HEAD plus later uncommitted work. The relevant DDK source/header/library inputs were checked against that commit: apparent differences were CRLF/DOS Ctrl-Z normalization, not semantic changes. The clean reproducibility test materialized BIN, LIB and DDK directly from the recorded Git commit.

The successful standalone backend does not depend on unpublished modifications to the older Tandy driver.

## Existing third-party inputs

- Generic renderer: DDK/286/DISPLAY/4PLANE
- Cursor/icon/bitmap resources and low-resolution resource script: DDK/286/DISPLAY/1PLANE/RC_LOW
- Font descriptors and color table: DDK/286/DISPLAY/4PLANE/RC_MED
- Headers/macros: DDK/286/INC before DDK/INC
- MASM/LINK/EXE2BIN and import libraries: existing BIN, DDK/TOOLS and LIB

V1.ASM includes hatch, color-match and line-style table material derived from the existing DDK EGA/EGA.ASM. The table provenance is stated in its header. Existing Microsoft notices in reused files are retained in the generated build tree.

This change supplies no new license for third-party material and makes no claim that existing repository inclusion grants redistribution rights. It avoids duplicating the DDK tree, compiler binaries, import libraries, Windows/DOS media or system fonts.

## Local transformations

build.py normalizes prepared legacy text to CRLF and removes DOS EOF bytes, then makes these ten source edits in the output copy only:

- CHARWDTH.ASM, PIXEL.ASM, ROBJECT.ASM: early .286 directive to .8086 (not sufficient by itself for whole-driver 8086 compatibility)
- DISPLAY.INC: disable hardware cursor exclusion in generic memory paths
- FB.ASM: call the outer TBitBlt wrapper
- POLYLINE.ASM and RLSTRBLT.ASM: correct same-segment stack-check declarations to NEAR
- RLSTRBLT.ASM, RLBLDSTR.ASM, REALFIX.ASM, REALPRO.ASM: include MFLAGS before real-mode paths need it

The five repeated includes in REALFIX/REALPRO are harmless frozen-build residue and are intentionally retained for exact reproduction.

Resource changes reuse tracked assets: low-resolution geometry, EGA color defaults and font descriptors, cxBorder=1, and one missing comma fixed in COLORTAB.ASM. PACKRES.PY generates and attaches Win16 resource records without requiring a Windows driver binary as a build input.

## Frozen artifact

bin/TANDYV1.DRV is the GUI-tested checkpoint, not the later performance candidate. Its source/resource build was reproduced byte-for-byte before publication.
