COMMDLG Win16 native keyboard-message regression probe
===================================================

This independent caller compiles with the owned Microsoft C toolchain using
/G0 /Gw /AS and links the historical C:\LIB\COMMDLG.LIB. CDTEST.H declares
the 72-byte Win16 OPENFILENAME structure independently of the DLL source.

Scope and limits
----------------
The test exercises real native Windows 3.0 controls and DialogBox message
loops under Windows /R. It posts synthetic WM_CHAR, WM_KEYDOWN, and WM_KEYUP
messages to the actual focused control. It is NOT physical keyboard input,
BIOS scan-code input, a screenshot assertion, or a hardware-speed benchmark.
No WM_COMMAND is injected for a passing case. WM_COMMAND IDCANCEL exists
only in bounded watchdog failure recovery, after recording a test failure.

The runner clones an owned-media installed Windows guest to a NEW output
folder, installs the selected candidate DLL only in that clone, and creates
only C:\CDKEY fixture files in the clone. It does not change installed-media
originals or the candidate DLL source. Every run records the exact DLL/caller
hashes, configuration, native log, host log, outcome, and DOS-return marker.

Cases
-----
0: Initially empty Open: filename Edit focus, queued Escape cancellation.
1: Initially empty Save: queued WM_CHAR types KEYTEST, queued Return accepts
   KEYTEST.TXT with the default extension, and the caller creates/writes it.
2: Prefilled Open: EM_GETSEL must be (0,11); queued Return accepts the path,
   and the caller opens/reads the exact payload written by case 1.
3: Initially empty Open: queued Tab moves from Edit to native ListBox,
   then queued Escape cancels.
4: Prefilled Save with OVERWRITEPROMPT: EM_GETSEL=(0,11), queued Return
   opens the prompt; No must own focus and BS_DEFPUSHBUTTON style; queued
   Return chooses No, then queued Escape cancels the restored file dialog.
   The original real file is reopened and its payload must be unchanged.
5: Reopen empty Open and queued Escape.
6: Reopen prefilled Open, verify all-selected again, and queued Escape.
7,8: Repeat empty Open/Escape twice more.
Every case checks stack/DS preservation, caller buffer canaries and restored
working directory. All cancellation outcomes require extended error zero.

Build (run from the shared workspace, substituting paths as needed)
------------------------------------------------------------------
python cdlg-key-src/BUILD.PY \
 --dosbox /workspace/shared/dosbox-x/squashfs-root/usr/bin/dosbox-x \
 --repo tandy-cookie --out cdlg-key-build01

Run one mode (output path must be new)
-------------------------------------
python cdlg-key-src/RUNKEY.PY \
 --guest /workspace/shared/tandy-modes-installed-160/guest \
 --dll cdlg-resume-focus-build/COMMDLG.DLL \
 --caller cdlg-key-build01/CDTEST.EXE \
 --dosbox /workspace/shared/dosbox-x/squashfs-root/usr/bin/dosbox-x \
 --out cdlg-key-160-01 --mode 160 --cycles 100000

The same run works with baseline, 3204, 6404 and 6402 guest suffixes.
Each run uses 640 KiB base RAM, 8086_prefetch, Windows /R, and no EMS,
XMS or UMB. Fixed cycles=100000 expedites QA; this is not 4.77 MHz timing.
Native watchdog: 150 timer ticks, then bounded failure recovery. Host runner
has a 180-second timeout by default; --timeout can raise that bound on a
busy host without changing the native probe.

Acceptance
----------
RESULT.JSON must show nine completed cases, 107 passed checks, no failures,
SUITE PASS and FINAL PASS, DOS return, and no CD*.TMP leftovers.
Guest CDTEST.LOG includes explicit SYNTHETIC KEYBOARD-MESSAGE labeling.
