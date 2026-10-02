# Verification record

Date: 2026-10-01

## Passed for frozen V1

- Fresh stock-CGA Windows 3.0 control boot on machine=tandy
- Canonical display exports/module identity and required OEMBIN resources
- Real Windows 3.00 Program Manager desktop, icons, text, colors and menus
- Maximize and redraw; Run dialog; application startup
- Notepad typing/caret and selection/copy/paste
- Application close and background repaint
- Paintbrush startup and visible color palette
- Software cursor movement and background restoration using COM1 serial mouse
- Clean Windows shutdown back to DOS
- Multiple complete source rebuilds matching the exact GUI-tested binary
- Clean build using only BIN/LIB/DDK materialized from main commit d57e9a2515391102d47849dc8878f95e9a07e703

Expected driver: 46288 bytes
SHA256: 995d0079278a42254d997684fb51bd4285bd19bedc2e32cca3bf5065d3cfc61a

Expected resources: 15711 bytes, 74 records
SHA256: 0b61538aa777b0ceafacb54669ab6a8ff7b63e703f01eeb39c2e789b621b11ee

## Exact tested environment

DOSBox-X 2026.08.31 SDL2, Sep 28 nightly; machine=tandy; cputype=386; core=normal; cycles=100000; memsize=16; expanded-base-memory option enabled; serial1=serialmouse. Windows 3.00, real mode via WIN /R, EGA system/fixed/OEM fonts.

## Not passed or not run

- Actual 8086/8088 CPU execution and physical Tandy hardware
- Mouse click/drag and actual Paintbrush drawing
- Full GDI/application regression suite
- Standard/enhanced Windows modes and matching grabbers
- Normal 640KB shared-memory operation without a pre-Windows reservation helper
- Later dirty-rectangle candidate GUI regression

Do not infer these from a clean build or a successful desktop.

## Earlier root causes established

The supplied legacy branch combined multiple independent failures: invalid loader-time video-mode call/return, malformed GDIINFO size/alignment, selector/segment issues, noncanonical DDI ordinals, and absent named display resources. Direct GDI inspection confirmed ordinal lookup and the OEMBIN/FONTS resource gate.

After those gates were cleared, BIOS mode09's extra shared video memory overwrote Windows allocations. The expanded Tandy memory setting fixed that overlap in the tested emulator. Default PS/2 mouse detection separately rejected the Tandy machine model; serial-mouse emulation enabled the cursor.

The software-memory raster backend supplies the drawing routines required beyond those loader fixes. V1's full-screen flush is correct in the exercised cases but slow.

## Reproduction

Run build.py with a fresh output directory. RESULT.json is written only after the exact resource and driver hashes match. DOS batch exit status alone is insufficient; assembler/linker logs and the final hash are checked.

The separate performance candidate has conversion/DDI test work in progress. It is intentionally not substituted for this known GUI-tested binary.
