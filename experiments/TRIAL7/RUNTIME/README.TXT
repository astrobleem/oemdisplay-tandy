TRIAL7 - BORDER/TEXT PRIVATE TEST OVERLAY
=======================================
Test-only. No installation on your computer has been performed for you.

This kit is intentionally ONE-SHOT and tests ONE ALREADY ACTIVE mode.
It supports only the exact pinned WindowsXT TR5 drivers and helpers at
C:\WINXT with Windows at C:\WINDOWS. Other paths/builds safely refuse.
Do not delete USED.TAG or reuse BACKUP to apply another mode.

IF TR6 IS CURRENTLY APPLIED
Restore it first using its own original DIBTR6 kit and saved backup:
  C:
  CD \DIBTR6
  RESTORE 6404 YES
Use your active mode code in place of 6404 and wait for RESTORE VERIFIED.
Then follow the TRIAL7 instructions below. Do not copy drivers by hand,
rename old backups, or bypass the identity guard. TRIAL7 deliberately
rejects the exact TR6 installed bytes; it accepts only exact original TR5.
Keep the DIBTR6 kit and its backup unchanged.

WHAT IT DOES
Replaces only the selected active C:\WINDOWS\SYSTEM\TR5*.DRV after
saving and byte-verifying the actual installed original in BACKUP.
The NEW files contain TRIAL7 border/text candidate bytes, with the retained
TR6 DIB optimization, under TR5 filenames so the launcher still recognizes
this display. Their filenames do not identify the original TR5 bytes.
No Setup/OEM install, INI edit, font change, shell change or media overwrite.
C:\WINXT originals, configuration, launchers and existing backups stay put.

BEFORE STARTING
- Have a separate backup of your CF/storage and a working DOS boot route.
- Use the existing working WindowsXT installation. Exact official
  SHELLSEL.EXE and TSCHECK.EXE from commit 1eac04fd are required in WINXT.
  They are checked by SHA-256 and are not bundled in this overlay.
- Unpack this whole directory to C:\TRIAL7 on a writable C: drive.
  Keep NEW, TR5, BACKUP and the supplied program/scripts together.
- Use DOS 3.3 or later. Exit Windows completely; a Windows DOS box is refused.
- Finish any existing shell recovery with your normal WINXT launcher first.
  This kit refuses pending shell journals and does not repair/edit INIs.
- Have at least 192 KB free on C:. Hash checks can take time on an 8088.
  Do not interrupt them. No EMS, XMS, UMB or 386 option is needed.

APPLY THE CURRENT MODE ONLY
At plain DOS:
  C:
  CD \TRIAL7
  APPLY 6404 YES

Replace 6404 above with the code for your CURRENT selected display:
  16016 = 160x200x16  (TR51616.DRV)
  32016 = 320x200x16  (TR53216.DRV)
  3204  = 320x200x4   (TR53204.DRV)
  6404  = 640x200x4   (TR56404.DRV, black/red/green/white)
  6402  = 640x200x2   (TR56402.DRV)

Wait for APPLY VERIFIED. Then use your EXISTING C:\WINXT\WINXT launcher
and test the same screen/app workload. Do not use Setup to switch modes
while this overlay is active. This kit does not start Windows for you.

RESTORE AFTER TESTING OR AFTER AN INTERRUPTED APPLY
Exit Windows completely, or boot to plain DOS if Windows cannot start:
  C:
  CD \TRIAL7
  RESTORE 6404 YES

Use the same mode code as APPLY. RESTORE uses your saved installed backup,
never a substitute from the shipped TR5 directory. It verifies the backup
before writing and verifies the restored file afterward. Wait for
RESTORE VERIFIED before using the normal launcher. Keep the backup.

Restore may be repeated. APPLY may not: USED.TAG and the original backup
remain even after a successful restore. If APPLY stopped during its first
backup, the active driver has not been overwritten; a partial backup is
refused and must be inspected. If it stopped while copying the test into
the active driver, RESTORE can repair that present-but-truncated file.
An arbitrarily missing target, changed active mode, damaged backup/marker,
unknown helper build, or unreadable disk is refused for manual inspection.
Do not delete files or bypass checks to force an operation.

LIMITS
This is a reversible experiment, not a newly accepted WindowsXT release.
Emulator tests do not establish physical Tandy/CF/power-loss reliability.
The kit cannot protect against disk failure or corrupted filesystem data.
Optimization measurements and remaining limitations are in the separate
experiment report. The driver retains the existing logical planes,
physical color depths and memory-reservation requirements.

FILES
NEW\       Exact approved TRIAL7 drivers under installed TR5 filenames.
TR5\       Exact pinned originals, used for preflight identity checks.
BACKUP\    The original active driver saved by APPLY; keep it intact.
T7SAFE.EXE First-party 8086 DOS guard/copy/check program.
APPLY.BAT / RESTORE.BAT  Entry points; explicit uppercase YES required.
SOURCE\    Guard source, embedded SHA-256 pins and build instructions.
TESTS.TXT   Validation scope, results and emulator/hardware limitations.
MANIFEST.SHA  Package SHA-256 inventory (check on a modern machine).

Source of required existing helpers and original distribution:
https://github.com/astrobleem/oemdisplay-tandy/tree/1eac04fdc571f73037b502ecf1f085028271866e/distributions/WINXT
