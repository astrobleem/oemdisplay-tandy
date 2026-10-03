# TSHELL Run/Browse verification

## Production binary and target

TSHELL.EXE: 12,355 bytes. SHA256:
647031075ae35442c1a379ec37196f810c3d33f2bb1c45233498029a2ec90b25

Two clean Microsoft C /G0 /Gw /AS builds match byte for byte. The NE expected
Windows version is 3.0; the protected-mode-only bit is clear. Imports are
KERNEL, GDI and USER only. No COMMDLG DLL, header or import library is used.
A scoped disassembly audit followed 3,786 reachable instructions from the NE
entry and four exported callbacks without finding post-8088 instructions.
Unresolved indirect branches and Windows imports are outside that audit;
it is not an exhaustive instruction or physical-hardware certification.

## Five-profile native regression

All five isolated Windows 3.0 real-mode profiles passed the final-source
Run/Browse probe: 160x200x16, 320x200x4, 640x200x4, 640x200x2 and baseline
320x200x16. Each boots with shell=tshell.exe and the accepted display driver,
reservation helper and fonts. The emulator is DOSBox-X, machine=tandy,
8086_prefetch, 640 KB conventional memory, and no EMS/XMS/UMB. The fixed
cycle count is a test convenience, not a physical Tandy speed measurement.

The probe uses the production source with test callbacks and logging added.
It executes the native dialogs and controls, rather than modeling them:

- Run and Browse outer bounds and all controls fit the physical screen
- Run edit starts focused; file list starts focused in Browse
- Empty, whitespace-only, overlong and missing-program commands stay open
  with the expected short status; failed launches are not reported as success
- 140 native WM_CHAR inputs stop at the 127-character guard; commands longer
  than 126 are rejected before copying into the 128-byte command buffer
- Browse navigates to the root and back, changes EXE/COM/BAT filters, locates
  the real test executable, and accepts it through a double-click notification
- Browse Cancel leaves command text and the original working directory intact
- Choosing an executable preserves arguments and restores the working directory
- The chosen native child receives the exact arguments and expected directory
- Run closes after successful launch; reopening and WM_CLOSE cancel safely;
  the shell survives both modal sessions

CHECKS.JSON contains the aggregate assertions and source/binary identities.
Per-profile RUNTEST.LOG files contain the raw results. The callback source,
child source, build inputs and configuration templates are included.
The typed-limit check temporarily suppresses edit repaint while delivering
WM_CHAR; text handling and the guard are native. It is not a typing-speed test.

## Pixel inspection and exact-binary observations

CAPTURES contains raw B800 framebuffer snapshots from the final production
EXE and their decoded PNGs. The Start popup includes Run and fits both the
160 profile and the larger-font baseline profile. The 160 Run and Browse
layouts were inspected from actual guest pixels. The decoder does not redraw
the UI; DISPLAY images duplicate 160 horizontal pixels to match DOSBox's
usual 320-pixel capture. The file list visibly accommodates 8.3 filenames.

These captures and the external helper's initialization/control observations
use the unmodified EXE. Functional assertions above use the instrumented
production source. Early asynchronous cross-task harness runs were not used
as functional acceptance: they raced modal cleanup and invoked callbacks
from another cooperative task. Their partial logs are excluded.

Cloud desktop control was unavailable during this revision. No new manual
mouse session, physical Tandy run or complete stock-application compatibility
claim is made. Real keyboard/mouse operation and hardware timing should still
be checked on the user's target installation.

## Additional 160-profile keyboard and directory checks

A second native production-source probe posts real WM_KEYDOWN messages to the
Run edit. Escape cancels; Return launches a drive-relative executable with
its arguments. A 126-character command also launches and delivers all 114
argument characters intact. Run closes, and the shell survives every case.
This verifies Windows dialog key handling, not physical keyboard input.

That probe starts with D:\ONE as drive D's saved directory, browses to
D:\TWO and closes Browse. The original command stays unchanged; C's working
directory and D:\ONE are restored, including after yielding back to Windows.
The drive-relative launch then succeeds. A final Run WM_CLOSE cancels safely.
All five modal sessions complete. Cases return to the normal message loop
between dialogs. KEYQA.LOG and KEYPROBE contain the clean final evidence.

## Size and memory

NE code is 9,996 bytes; minimum data is 2,448 bytes, heap 2,048 and stack 4,096.
The included external loader at 160 launches the unmodified production EXE,
closes only its bar, and verifies that COMMDLG is absent. It observed a
10,848-byte GetFreeSpace(0) decrease,
a 10,000-byte runtime code block and a 9,648-byte instance data block. The
availability change and block sizes overlap and must not be added together.
This is a snapshot, not a complete resident-memory census or measured peak.

Browse temporarily allocates 3,744 bytes to preserve visited drives' current
directories, and releases that buffer on return. Allow roughly 32 KiB for the
bar and transient dialogs, plus memory for launched applications and shared
Windows resources. That is a planning estimate, not a measured upper bound.
There is no full-screen bitmap allocation in the shell.

## Historical scope and reproduction

LEGACY09 preserves the earlier 7,423-byte shell's tests, captures, clock,
exit/rollback and Program Manager results. Those are explicitly historical;
they are not presented as a rerun of this binary. The Run/Browse work does
not change accepted display drivers, launcher, reservation helper or splash.

Build production with BUILD.PY from examples/TSHELL in the existing repository.
For the included helper/probe copies, pass --repo explicitly. Supply isolated
Windows 3.0 installations from owned media and the accepted five profiles;
CONFIG.TXT documents the settings. No Windows media, guest installations,
Microsoft compiler/library binaries or stock applications are included.
