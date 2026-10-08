# Project: Tandy 1000 EX/HX Display Driver (Windows 3.0)

## 1. Environment & Tools
- **Host OS:** Windows packaging entry point; portable Python backend also tested on Linux.
- **Emulator:** separately supplied DOSBox-X; pass its explicit path via `--dosbox`.
- **Assembler:** pinned external MASM 5.10; see tools/BUILDDEPS/README.MD.
- **Linker:** LINK4 (Segmented Executable Linker v5.x).
- **Current Build:** `python3 src/tandysw/BUILD88.PY --dosbox <dosbox-x> --out <new-path> [--mode <profile>]`; five profiles are in `docs/MODES.MD`. Omitted mode selects 320x200x16 in the current development pipeline; see docs/TRIAL4/README.MD.
- **Legacy Build:** old TNDY16 source/builders are preserved in [DEV](docs/DEV.MD); use current external source views.
- **Packaging:** current public Windows XT uses `tools/FLASHDISK/MAKEIMG.PY`; test with `TESTFAT.PY` and `TESTPKG.PY`. Root `MAKEDISK` is historical TANDY88 reproduction only. See `BUILDING.MD`.
- **Install:** current own-media WINXT disk, six Windows Setup Other display choices, and guarded `C:\WINXT\WINXT` launcher. Every profile selects approved `WXTSPL01.RLE`; the old Tandy picture is retired. Never use manual INI edits as normal install instructions.

## 2. File Handling Rules
- **Line Endings:** **CRLF** (Windows style) is MANDATORY.
    - *Reason:* MASM 5.10 and the `multi_replace_file_content` tool can fail with mixed or LF-only line endings.
    - *Action:* Ensure all edits preserve `\r\n`.
- **Filenames:** 8.3 format, uppercase preferred for DOS compatibility (e.g., `TANDY16.DRV`).

## 3. Coding Standards
- **Language:** 8086 Assembly (MASM 5.1 syntax).
- **Calling Convention:** Pascal (`?PLM=1`) for Windows API compliance (Uppercase exports).
- **Segments:** Use `cmacros.inc` macros (`sBegin`, `sEnd`, `cProc`) to ensure correct segment ordering (`_TEXT`, `_DATA`, etc.).

## 4. Development builds and historical OEM package preservation

The updated BUILD88 source produces the experimental Output-row family recorded
in docs/TRIAL4/BUILDS.JSN. Existing packaged payloads and exact MAKEDISK pins
remain historical accepted artifacts. Do not replace those payloads or relax
pins merely because a development rebuild succeeds. Trial overlays live only
in experiments/TRIAL4 and require owned support files. REPCOPY88.PY is a
retained, host-only nine-character filename; DOS payload names stay 8.3.

1. Preserve the accepted candidate05 `src/tandysw/bin/TANDY88.DRV` (SHA256 `ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee`), `RESERVE.COM`, shared launcher and custom `TNDYLOGO.RLE` unless explicitly in scope. Main commit `54fdd714` and the custom-splash work have been merged locally; do not regress them.
2. Rebuild with `BUILD88.PY` and review `RESULT.json`; run the documented CPU, memory and framebuffer tests.
3. Package through `MAKEDISK.BAT` on Windows or `MAKEDISK.PY` elsewhere. Exact binary pins deliberately reject an unaccepted rebuild.
4. Use `--windows-files <owned-media-files> --local-out <new-disk-directory>` for a complete installable disk. The normal TANDY88.ZIP includes all five pinned drivers, eight pinned Windows 3.0 OEM support files and the pinned first-party TNDYLOGO.RLE. Only CGASYS.FON, CGAFIX.FON and CGAOEM.FON are new Windows dependencies.
5. Test Windows Setup and the resulting installation without manually editing SYSTEM.INI. Keep full OS media, guest installations and unrelated toolchains out of publication. Only the eight pinned Windows OEM dependencies and first-party TNDYLOGO.RLE belong alongside the drivers/helpers and documented text/metadata in the complete runtime ZIP.
6. Rebuild/reverify the package after changing a payload source such as FILE_ID.DIZ. The current measured FAT12 total is 326,656/368,640 bytes, including allocation/overhead, with 41,984 bytes free; remeasure after final edits.
7. See `docs/MODES.MD` and `docs/OEMDISK.MD` for acceptance, failure checks and limits. All five native Setup switches and cloned-install GDI checks have passed; the final only-C-drive cold GUI/reopen and rebuilt-package acceptance also passed (docs/modes/oem/COLD.JSON). Native Windows host-wrapper execution and physical Tandy hardware remain separate verification requirements.

## 5. Selectable-Mode Contracts
- Target original EX/HX, Windows 3.0 real mode, normal 640 KB and enforced 8086/8088 semantics. Do not introduce 386, expanded-memory, EMS/XMS or UMB workarounds.
- Setup choices: TANDY88.DRV = 320x200x16; TNDY6404.DRV = 640x200x4 black/red/green/white; TNDY160.DRV = 160x200x16; TNDY3204.DRV = 320x200x4 black/cyan/magenta/white; TNDY6402.DRV = 640x200x2 black/white.
- BIOS 0Ah is four colors on original EX/HX. Never describe it as 640x200x16.
- Keep four logical DDB planes; NUMCOLORS reports actual physical colors. Logical planes do not increase physical depth. Shadow buffers are exactly 16,000/32,000/64,000 bytes by width; hardware buffers are 16,384 bytes except modes 09h/0Ah at 32,768 bytes.
- New modes use eight-pixel CGASYS/CGAFIX/CGAOEM fonts and resource/Setup tuple 200,96,48. Default keeps EGA fonts and 133,96,72.
- The shared RESERVE helper conservatively protects the extra 16 KB overlap for every mode. Lower-color modes do not permit bypassing the launcher.
- Retain historical evidence. docs/modes/6404 is the experimental cyan/magenta checkpoint; docs/modes/6404rg is the current red/green profile.
- Do not turn oracle self-tests or mathematical color/ROP proofs into claims of complete Windows/hardware coverage. Current Windows probes cover solid brushes, SRCCOPY and SRCINVERT; NULL-buffer GetDIBits is unsupported.
- Recommend stock-CGA Windows installation first, then Setup's Other display selection of 640x200x4. At 160/320 pixels, desktop and Setup dialogs can clip.

## 6. Common Pitfalls
- **Syntax Errors:** `?PLM=1` ensures Pascal calling convention (uppercase symbols). Mixing calls with C-style functions (`externNP`) without `externFP` or aliases can cause link errors.
- **Fixup Overflows:** `NEAR` calls to distant segments. Use `FAR` calls or rearrange segments.
- **Linker Errors:** `L2022` (undefined) or `L2023` (alias import conflict) often relate to DEF file export naming vs. source code mangling.

## 7. Milestones
- **[x] Milestone 1: First Successful Build (2025-12-02)**
    - `TNDY16.DRV` builds and links successfully without stubs.
- **[x] Milestone 2: Linker Error Resolution (2025-12-05)**
    - Switched to `LINK4.EXE` for Windows 3.x compatibility.
    - Standardized on Pascal (`?PLM=1`) convention.
    - Resolved export conflicts (Enable/Disable renamed).
- **[x] Milestone 3: Packaging (2025-12-05)**
    - `makedisk.bat` updated for Windows/PowerShell.
    - Produces `TNDY16.ZIP` ready for distribution.

Source rebuilds use a fresh pinned external workspace; pass that workspace
through each script's --repo or --toolchain parameter. Main contains no
bundled DDK/compiler/emulator. Current package CI uses accepted binaries
and runs host checks, including the current lowercase TSHELL idle/Hold tests.
