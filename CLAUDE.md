# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OEMDisplay-Tandy is a **Windows 3.x OEM display driver** for the Tandy 1000 series, enabling native TGA (Tandy Graphics Adapter) 320x200 16-color mode. This is a **16-bit real-mode** driver built with vintage DOS tooling — not a modern project.

## Build System

All compilation happens inside **DOSBox-X** using bundled tools in `BIN/`. You cannot build from a Linux shell.

### Prerequisites
```bash
sudo apt-get install -y dosbox-x unix2dos file dos2unix
```

### Build Commands
```bash
# Automated build (recommended) — spawns DOSBox-X, runs 5-stage build
build_driver.bat

# Package for distribution (creates TNDY16.ZIP)
makedisk.bat

# Manual build inside DOSBox-X (stages 1-5, resumable)
BLDTNDY.BAT 1   # Assemble core: TANDY, CURSORS, INQUIRE, SETMODE
BLDTNDY.BAT 2   # Assemble: DISABLE, COLOR, BLKWHITE, CHKSTK, COLORINF
BLDTNDY.BAT 3   # Assemble: CONTROL, FB, CHARWDTH, DITHER (-DLORES)
BLDTNDY.BAT 4   # Assemble: DITHER (-DHIRES), SSWITCH, TGAVID, cursor, ENABLE, stubs
BLDTNDY.BAT 5   # Link all OBJ files → TANDY16.DRV via LINK4
```

### Build Output
- `TNDY16.DRV` — the driver binary (copied to project root on success)
- `BUILD.LOG` — build log (check for errors)
- `TNDY16.MAP` — linker map file (useful for debugging symbol issues)

### No Automated CI
Manual DOSBox-X builds are required. The GitHub Actions workflow (`release.yml`) only packages pre-built binaries.

## Architecture

### Toolchain
- **Assembler:** MASM 5.10 (`BIN/MASM.EXE`)
- **Linker:** LINK4.EXE — Windows 3.x Segmented Executable Linker (`BIN/LINK4.EXE`)
- **C Compiler:** Microsoft C 6.0 (`BIN/CL.EXE`) — C89 only
- **DDK headers:** `DDK/INC/` and `DDK/286/INC/` (cmacros.inc, gdidefs.inc, etc.)

### Source Layout
All driver source lives in `src/tandy16/`. The driver is a Windows DLL (`.DRV`) that exports 7 GDI entry points defined in `tandy16.def`:

| Export | Ordinal | Source |
|--------|---------|--------|
| ENABLE (=TandyEnable) | @1 | ENABLE.ASM |
| DISABLE (=TandyDisable) | @2 | DISABLE.ASM |
| COLORINFO | @3 | COLORINF.ASM |
| REALIZEOBJECT | @4 | stubs.asm |
| BITBLT | @5 | stubs.asm |
| OUTPUT | @6 | stubs.asm |
| DEVICEMODE | @7 | SETMODE.ASM |

### Key Modules
- **TANDY.ASM** — Physical device structure (GDIINFO/PDEVICE)
- **TGAVID.ASM / TGAVID.H** — Hardware abstraction: TGA detection, mode setting, plane info
- **FB.ASM** — Framebuffer/shadow buffer operations
- **SSWITCH.ASM** — Int 2Fh screen switching hook
- **COLOR.ASM / COLORINF.ASM** — Palette realization, RGB color handling
- **DITHER.ASM** — Compiled twice: once with `-DLORES`, once with `-DHIRES`
- **CURSORS.ASM / cursor.asm** — Cursor rendering
- **tandy16.def** — Module definition with exports and Windows API imports
- **tandy16.lnk** — Linker response file (object file order matters)

### Calling Convention
All assembly uses **Pascal calling convention** (`?PLM=1`). This produces uppercase, undecorated symbol names. Mixing C convention (`?PLM=0`) causes L2029 linker errors — all modules must consistently use `?PLM=1`.

The `cmacros.inc` macros (`sBegin`, `sEnd`, `cProc`, `cBegin`, `cEnd`) handle segment setup and procedure framing. These are required for Windows driver compatibility.

## File Format Requirements

- **Line endings:** CRLF (`\r\n`) is **mandatory** — MASM 5.10 fails on LF-only files. Use `unix2dos` if needed.
- **Filenames:** 8.3 format, uppercase (e.g., `TANDY.ASM`, not `tandy.asm`).
- **Encoding:** ASCII only, no UTF-8 BOM.

## Coding Standards

- **Assembly:** MASM 5.1 syntax, 8086 instruction set, Pascal calling convention
- **C code:** Strictly C89 — no C99 or C++ features
- **Indentation:** 4 spaces, no tabs
- **Line length:** 80 columns max
- **Integer types:** Use explicit-width types (`uint8_t`, `WORD`, `DWORD`)

## Common Linker Errors

| Error | Cause | Fix |
|-------|-------|-----|
| L2029 Unresolved External | Missing symbol or calling convention mismatch | Verify `?PLM=1` in all ASM files; check DEF exports |
| L2023 Export Imported | Symbol exported by driver but also in LIBW.LIB | Use `/NOE` linker flag; rename export alias in DEF |
| L2022 Export Undefined | DEF exports symbol not found in OBJ | Check `cProc` macro expansion; verify PUBLIC declaration |
| Fixup Overflow | NEAR call across distant segments | Convert to FAR call or rearrange segments |

## Testing

No automated tests exist. Validation requires:
1. Build driver (`build_driver.bat`)
2. Check `BUILD.LOG` for errors
3. Install `TNDY16.DRV` on a Windows 3.0/3.1 system (real or emulated)
4. Run Windows Setup, select the Tandy driver, verify 320x200 16-color display

## Current Development Status

**Milestones 1-3 complete**: Driver builds, links, and packages successfully.

**Remaining linker issues** (see `handoff.md` for details):
- L2023: `Enable`/`Disable` export conflicts with LIBW.LIB
- L2022: `DeviceMode`/`ColorInfo` symbol visibility issues
- Unresolved: `_sum_RGB_colors_alt`, `COLOR_FORMAT` (likely missing from COLOR.ASM)
