# Project: Tandy 1000 EX/HX Display Driver (Windows 3.0)

## 1. Environment & Tools
- **Host OS:** Windows.
- **Emulator:** DOSBox-X (Path: `DOSBox-X\dosbox-x.exe`).
- **Assembler:** MASM 5.10.
- **Linker:** LINK4 (Segmented Executable Linker v5.x).
- **Build Script:** `build_driver.bat` (Host) -> `BLDTNDY.BAT` (Guest).
- **Packaging:** `makedisk.bat` (Host - Windows/PowerShell).

## 2. File Handling Rules
- **Line Endings:** **CRLF** (Windows style) is MANDATORY.
    - *Reason:* MASM 5.10 and the `multi_replace_file_content` tool can fail with mixed or LF-only line endings.
    - *Action:* Ensure all edits preserve `\r\n`.
- **Filenames:** 8.3 format, uppercase preferred for DOS compatibility (e.g., `TANDY16.DRV`).

## 3. Coding Standards
- **Language:** 8086 Assembly (MASM 5.1 syntax).
- **Calling Convention:** Pascal (`?PLM=1`) for Windows API compliance (Uppercase exports).
- **Segments:** Use `cmacros.inc` macros (`sBegin`, `sEnd`, `cProc`) to ensure correct segment ordering (`_TEXT`, `_DATA`, etc.).

## 4. Build Process
1.  **Edit:** Modify `.asm` files in `src\tandy16`.
2.  **Build:** Run `build_driver.bat` from the host terminal.
3.  **Verify:** Check `BUILD.LOG` for errors.
    - *Success:* `TNDY16.DRV` is created.
    - *Failure:* Fix errors and retry.

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
