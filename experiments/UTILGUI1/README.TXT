UTILGUI1 - QUALIFIED SMALL GUI POLISH TRIAL
Windows 3.0 real mode / 8088, all five supported graphics profiles.
Isolated first-party trial based on c6ee4b0; qualified 6 October 2026.

CHANGES
EXJOY: Live / Paused / Demo headings and a partial-center axis count. A
paused demo keeps its Demo label. Sampling, presence uncertainty and I/O
are unchanged; normal and demo runs write no logs.
FileDrop: the last drop shows its path count and both fixture paths. A
later one-path drop clears the second line. /D opts into logs, /A retains
QA, and ordinary runs are silent. Dropped paths are never opened or copied.
CDTEST: the normal Dialogs window shows the selected path and result, with
Open / Save sample / Read sample / Try Cancel on the File menu. A Win3.0
listbox wraps long paths into bounded read-only rows. Save/read success
requires successful I/O and close. /A /B /C keep explicit diagnostics.
The COMMDLG.DLL implementation and CDSTART launcher are byte-identical to
the accepted historical versions. Launch the demo through CDSTART.

TRY
Read DOCS for each app. Use new trial folders and keep your working copies.
EXJOY can run from its own folder. FileDrop retains its documented fixed
C:\DROP.TXT and C:\SECOND.TXT fixture workflow with both EXEs at C:\.
Keep CDSTART.EXE, CDTEST.EXE and COMMDLG.DLL together; use a NEW scratch file
for Save sample. No installer, driver, Windows settings or stock OS patch
is included. Historical packages and their pinned payloads remain unchanged.

VERIFIED
Exact source snapshots and period C6 /G0 /Gw /AS builds are retained.
All five stock-font modes passed EXJOY /test, FileDrop /A, the full CDTEST
/C suite, its /B Save/read/Cancel round-trip and normal cross-task flows.
Normal flows cover pause/resume, two/one paths, private-DLL CDSTART lookup,
selected/long paths, Cancel, close/reopen, absent normal logs, real mode,
8088 CPU sentinels and unchanged original fixtures. EXJOY /porttest also
passed a bounded emulated no-device path. Every native run used 640 KB,
8086_prefetch, no EMS/XMS/UMB, Windows /R and the reservation helper.
Native records and raw-framebuffer-derived PNGs are under EVIDENCE/NATIVE.
A supplemental queued-paint run supplies the 3204 acceptance images; its
record and the earlier observer limitation are under EVIDENCE/PROBE3204.
160-pixel DISPLAY PNGs duplicate horizontal pixels for inspection; logical
PNGs retain 160x200 pixels. Other images are direct hardware-layout decoding.
Host EXJOY tests passed 90,060 synthetic checks and 128 exact capture-byte
cases. NE/import audits verified the Windows 3.0 import contracts. Direct
instruction review is scoped and supplements /G0 plus native execution.

QUALIFICATIONS
The normal-flow observer initially used a cross-task convenience text setter
that left a modal filename empty. It was corrected to explicit control
messages/readback, with completed-control and reentrancy guards. A clipped
narrow caption was shortened to Dialogs. Acceptance records refer only to
the final runtime hashes and the corrected observer; earlier trials are not
counted. A synchronous cross-task forced-paint observer produced incomplete
3204 RAM snapshots; the same run's video and a separate delayed/queued-paint
run show complete text with unchanged production binaries. The precise
low-level cause was not established; no driver defect is claimed. The probe
record preserves the misleading dumps, comparison and supporting frames.
Stock-font profiles were tested, not arbitrary custom fonts.
These are emulator functional/visual checks, not physical Tandy/joystick
acceptance or cycle-exact speed measurements. Existing device warnings remain.
Do not run automatic diagnostic switches in a working Windows session: they
can exit Windows. The ordinary apps close only themselves.

BUILD / CHECK
Use a licensed C6/MASM5/LINK4/Win3.0 SDK tree; none is bundled. Each SOURCE
app has BUILD.PY and BUILD.BAT; specify --repo TOOL_TREE --dosbox DOSBOX_X
--out NEW_OUTPUT. QA/BUILD.PY builds the normal-flow observer. All emulator
invocations must use your shared serialization lock. Read the app build docs.
SOURCE/CDLG and SOURCE/CDSTART retain unchanged dependency/launcher source.
The included runtimes are identified by MANIFEST.SHA; QA/TESTPUB.PY verifies
exact files, source/runtime evidence, native-case counts and the allowlist.
No full Windows/DOS installation, SDK library, toolchain or guest is shipped.
