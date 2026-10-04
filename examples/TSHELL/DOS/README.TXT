SHELLSEL - optional TSHELL shell selection and recovery

USE FROM DOS, AFTER COMPLETELY EXITING WINDOWS
  SHELLSEL STATUS  C:\WINDOWS\SYSTEM.INI
  SHELLSEL SELECT  C:\WINDOWS\SYSTEM.INI
  SHELLSEL RECOVER C:\WINDOWS\SYSTEM.INI
  SHELLSEL FINISH  C:\WINDOWS\SYSTEM.INI

Exit code: 0 = requested operation verified; 1 = safety or I/O failure;
2 = usage. SELECT by itself does not reserve video RAM or start Windows.
Use the optional TSTART.BAT to launch. Never bypass the accepted RESERVE.

Place SHELLSEL.EXE, TSTART.BAT and RECOVER.BAT in C:\TSTART.
Place the separately built TSHELL.EXE beside Windows' SYSTEM.INI.
Keep the accepted RESERVE.COM at C:\TANDY88\RESERVE.COM; this package
must not replace or redistribute it as a new helper. Edit the four path
settings at the top of TSTART.BAT if needed, and match RECOVER.BAT's two
settings. All paths must be absolute DOS 8.3 paths without spaces.
TSTART takes no arguments. It recovers first, invokes RESERVE, refuses
any RESERVE failure, selects TSHELL, runs WIN /R, then recovers on return.
If selection fails, it attempts recovery once and does not launch Windows.
RECOVER.BAT only recovers; it never starts Windows. After successful
recovery, the original accepted TANDY88 launcher remains the normal path
for starting the original shell. No WINPM wrapper is supplied.

TRANSACTION CONTRACT
Only the bytes of [boot]'s shell value change. Spelling, spacing, comments,
line endings, other sections and later unrelated edits remain intact.
Recovery uses the current INI plus the original shell in the active
TSHELL.JRN, rather than replacing the whole INI with an old backup.

Fixed sibling files, all in the SYSTEM.INI directory:
  TSHELL.JRN  Active immutable snapshot of the pre-selection INI.
  TSHELL.BAK  Persistent first-good raw INI backup for manual inspection.
  TSHELL.SAV  Matching ownership/integrity record for TSHELL.BAK.
  TSHELL.NEW  Verified staged output, only while replacing the INI.
  TSHELL.OLD  Verified rename source, only while replacing the INI.
  TSHELL.RST  Snapshot of the current file before recovery replacement.

BAK/SAV are deliberately retained and never automatically overwritten.
They remain the initial known-good backup across later launches. JRN is
the current transaction's full original snapshot, and is the recovery
source. Unknown preexisting sidecars are collisions and stop the helper.
Do not delete, edit, rename, or copy sidecars while a transaction is active.
If a backup record or active journal is corrupt or belongs to a different
absolute INI path, the helper refuses to use it.

SELECT persists and rereads JRN, then BAK/SAV if first use, before touching
the INI. It writes/rereads NEW, renames INI to OLD, promotes NEW, rereads the
result, then removes only a byte-verified OLD. The active JRN remains.
RECOVER snapshots the CURRENT selected file as RST before replacement.
It restores just the saved shell value, including original capitalization
and arguments, and rereads the result before deleting the active journal.
An independently changed shell value is a conflict, never overwritten.

If INI is absent after a known interrupted selection rename, recovery
requires exact OLD and NEW identity before restoring the original OLD.
If recovery's rename was interrupted, it requires exact RST/OLD and staged
output identity before completing. Missing INI without that evidence is
not permission to copy BAK over it. There is no blind whole-file fallback.

Completed-operation interruption checkpoints are automatically recoverable.
Short/torn writes, corrupt files, read/flush failures and unknown collisions
stop safely, preserve evidence, and may require manual inspection. Do not
start Windows until RECOVER succeeds. This is not a claim of atomicity
against arbitrary FAT/disk corruption, power-loss sector tearing or faulty
hardware. DOS commit and disk-reset flushing are used, but cannot repair
such failures. No current or backup file is deliberately truncated in place.

LIMITS
Requires DOS 3.3+ (AH=68h commit); intended physical environment DOS 6.22.
A conservative INT 2Fh 1600h/4680h check rejects detected Windows sessions.
The INI limit is 16,000 bytes; up to 64 uniquely named sections, each at most
63 characters; exactly one [boot] and one nonempty shell key (max 255 bytes).
Duplicate sections/keys, control bytes, malformed sections and ambiguous
inputs are rejected. Supported newlines are CRLF, LF and CR. Files with DOS
read-only, hidden, system, directory or volume-label attributes are not
mutated. File bytes are preserved, but rewrite timestamps/archive metadata
are not preserved. Unknown third-party concurrency is unsupported; use only
one helper from plain DOS, while Windows is not running.

SELECT requires a structurally recognizable Windows NE TSHELL.EXE and
Windows loader WIN.COM beside SYSTEM.INI. These header checks detect obvious
wrong/truncated files; they do not authenticate their publisher or prove
that the programs will run. Recovery does not need either executable.

BUILD / VERIFICATION
MSC 6.0: /c /AS /G0 /W3 /Od, with native DOS SLIBCE.LIB.
LINK4: /NOD /ST:4096. No /Gw, Windows startup, Windows runtime or Win API.
BUILD.BAT expects toolchain C:\BIN, C:\INCLUDE and C:\LIB; run in source dir.
BUILD.CNF is a local test configuration, not a portable runtime file.
TESTSEL.PY builds the exact same source with only syscall/test shims enabled.
It checks byte preservation, all completed filesystem-mutation checkpoints,
restart idempotence, later edits, unknown journals, backup collisions,
invalid executables, short writes, missing files and read-only inputs.
Its crash/short-write environment controls exist ONLY in HOST_TEST builds;
the distributed DOS executable contains no fault-injection controls.

The source, batches and documentation use CRLF. Generated host executables,
DOSBox configurations, test fixtures/logs, OBJ/MAP and locally owned Windows
or compiler files are development evidence, not runtime package contents.
Genuine DOS 6.22 normal-exit and interrupted-session recovery passed in a
Tandy HX emulator. Physical hardware and audio quality are not independently
qualified. See ../TESTS.MD for current scope.



SUCCESS-ONLY FINISH UPDATE (08 AND LATER)

FINISH uses the same conservative restoration as RECOVER, then draws a BIOS
text-mode moon/stars screen only after successful verified journal cleanup.
The message says: It's now safe to turn off your computer. It does not power
off the machine, pause for a key or require ANSI.SYS. Existing 40/80-column
text mode and active page are kept; the DOS prompt remains usable.

RECOVER remains plain for manual recovery and preflight. SELECT internal
recovery, absent journals, errors and redirected output remain plain.

The new SHELLSEL.EXE is required before activating the post-WIN batch block.
Follow BATCH08.TXT exactly, preserving all SET paths and every unrelated byte.
OLDWIN.TXT and NEWWIN.TXT are the exact replacement blocks. Require one old
block and no conflicting WINFAIL label. Nonzero WIN /R returns use RECOVER;
zero uses FINISH. ERRORLEVEL must be checked immediately after WIN /R.
The supplied TSTART.BAT remains only a first-install template. Never overwrite
a configured installed batch with it. The new helper works safely with an old
batch, which continues to use plain recovery until patched.

Build using BUILD.BAT with the owned MSC6 /AS /G0 and LINK4/SLIBCE toolchain.
Host checks: run TESTSEL.PY, then TESTNITE.PY with Python 3/GCC. BASESEL.C and
BASESTRT.BAT are historical fixtures used to prove the transaction source and
all configured SET paths remain unchanged. They are not installed. The test
runners generate temporary local outputs; do not publish those build outputs.
See ../TESTS08.MD for the retained DOS 6.22 emulator qualification.
