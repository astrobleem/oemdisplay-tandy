# Project: Tandy 1000 EX/HX Display Driver (Windows 3.0)

## 1. Environment & Tools
- **Host OS:** Windows.
- **Emulator:** DOSBox-X (Path: `DOSBox-X\dosbox-x.exe`).
- **Assembler:** MASM 5.10.
- **Linker:** Microsoft Overlay Linker 3.64.
- **Build Script:** `build_driver.bat` (Host) -> `BLDTNDY.BAT` (Guest).

## 2. File Handling Rules
- **Line Endings:** **CRLF** (Windows style) is MANDATORY.
    - *Reason:* MASM 5.10 and the `multi_replace_file_content` tool can fail with mixed or LF-only line endings.
    - *Action:* Ensure all edits preserve `\r\n`.
- **Filenames:** 8.3 format, uppercase preferred for DOS compatibility (e.g., `TANDY16.DRV`).

## 3. Coding Standards
- **Language:** 8086 Assembly (MASM 5.1 syntax).
- **Calling Convention:** Pascal (`?PLM=0`) for Windows API compliance.
- **Segments:** Use `cmacros.inc` macros (`sBegin`, `sEnd`, `cProc`) to ensure correct segment ordering (`_TEXT`, `_DATA`, etc.).

## 4. Build Process
1.  **Edit:** Modify `.asm` files in `src\tandy16`.
2.  **Build:** Run `build_driver.bat` from the host terminal.
3.  **Verify:** Check `BUILD.LOG` for "Severe Errors".
    - *Success:* `TNDY16.DRV` is created.
    - *Failure:* Fix errors and retry.

## 5. Common Pitfalls
- **Syntax Errors:** `?PLM=0` fails; use `?PLM = 0` (spaces required).
- **Fixup Overflows:** `NEAR` calls to distant segments. Use `FAR` calls or rearrange segments.
- **Tool Issues:** If `replace_file_content` fails, check for whitespace mismatches or non-unique context. Use `view_file` to confirm exact content first.

## 6. Milestones
- **[x] Milestone 1: First Successful Build (2025-12-02)**
    - `TNDY16.DRV` builds and links successfully without stubs.
    - Windows API symbols (`AllocCSToDSAlias`, `FreeSelector`, etc.) are correctly linked to `KERNEL.LIB` and `LIBW.LIB`.
    - Build process automated via `build_driver.bat`.
