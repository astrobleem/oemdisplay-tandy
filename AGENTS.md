# Project: Tandy 1000 EX/HX Display Driver (Windows 3.0)

## 1. Environment & Tools
- **Host OS:** Windows packaging entry point; portable Python backend also tested on Linux.
- **Emulator:** DOSBox-X (Path: `DOSBox-X\dosbox-x.exe`).
- **Assembler:** MASM 5.10.
- **Linker:** LINK4 (Segmented Executable Linker v5.x).
- **Current Build:** `python3 src/tandysw/BUILD88.PY --dosbox <dosbox-x> --out <new-path>`.
- **Legacy Build:** `build_driver.bat` -> `BLDTNDY.BAT` builds the old `TNDY16.DRV`, not the accepted driver.
- **Packaging:** `MAKEDISK.BAT` -> `MAKEDISK.PY` (Python 3.8+). See `BUILDING.MD`.
- **Install:** completed own-media OEM disk, Windows Setup Other display, and fail-closed `C:\TANDY88\TANDY88` launcher. Never use manual INI edits as normal install instructions.

## 2. File Handling Rules
- **Line Endings:** **CRLF** (Windows style) is MANDATORY.
    - *Reason:* MASM 5.10 and the `multi_replace_file_content` tool can fail with mixed or LF-only line endings.
    - *Action:* Ensure all edits preserve `\r\n`.
- **Filenames:** 8.3 format, uppercase preferred for DOS compatibility (e.g., `TANDY16.DRV`).

## 3. Coding Standards
- **Language:** 8086 Assembly (MASM 5.1 syntax).
- **Calling Convention:** Pascal (`?PLM=1`) for Windows API compliance (Uppercase exports).
- **Segments:** Use `cmacros.inc` macros (`sBegin`, `sEnd`, `cProc`) to ensure correct segment ordering (`_TEXT`, `_DATA`, etc.).

## 4. Current Build and Package Process
1. Preserve the accepted candidate05 `src/tandysw/bin/TANDY88.DRV` and `RESERVE.COM` unless a driver change is explicitly in scope.
2. Rebuild with `BUILD88.PY` and review `RESULT.json`; run the documented CPU, memory and framebuffer tests.
3. Package through `MAKEDISK.BAT` on Windows or `MAKEDISK.PY` elsewhere. Exact binary pins deliberately reject an unaccepted rebuild.
4. Use `--windows-files <owned-media-files> --local-out <new-disk-directory>` for a complete installable disk. The normal TANDY88.ZIP includes precisely the five pinned Windows 3.0 OEM support files plus the pinned first-party TNDYLOGO.RLE.
5. Test Windows Setup and the resulting installation without manually editing SYSTEM.INI. Keep full OS media, guest installations and unrelated toolchains out of publication. Only the five pinned Windows OEM dependencies and first-party TNDYLOGO.RLE belong in the complete runtime ZIP.
6. See `docs/OEMDISK.MD` for acceptance, failure checks and limits. Native Windows host-wrapper execution and physical Tandy hardware remain separate verification requirements.

## 5. Common Pitfalls
- **Syntax Errors:** `?PLM=1` ensures Pascal calling convention (uppercase symbols). Mixing calls with C-style functions (`externNP`) without `externFP` or aliases can cause link errors.
- **Fixup Overflows:** `NEAR` calls to distant segments. Use `FAR` calls or rearrange segments.
- **Linker Errors:** `L2022` (undefined) or `L2023` (alias import conflict) often relate to DEF file export naming vs. source code mangling.

## 6. Milestones
- **[x] Milestone 1: First Successful Build (2025-12-02)**
    - `TNDY16.DRV` builds and links successfully without stubs.
- **[x] Milestone 2: Linker Error Resolution (2025-12-05)**
    - Switched to `LINK4.EXE` for Windows 3.x compatibility.
    - Standardized on Pascal (`?PLM=1`) convention.
    - Resolved export conflicts (Enable/Disable renamed).
- **[x] Milestone 3: Packaging (2025-12-05)**
    - `makedisk.bat` updated for Windows/PowerShell.
    - Produces `TNDY16.ZIP` ready for distribution.
