# Cube qualification

Eight representative native-emulator rendering fixtures passed.
Qualification is limited to the table below. No physical adapter,
composite output, Windows 3.1 or every-driver qualification is claimed.

The exact CUBE.EXE is 15,647 bytes, SHA-256
`9ce367edd179291f324b011f8175afa90d298d1c60a644ef53d63ae56b43aa0e`.
The paired shell is 74,131 bytes, input DLL 6,301 bytes and native DOS
installer 16,306 bytes. ACCEPT.JSN pins all four, their source and evidence.
No accepted display/font/mouse/keyboard/sound or core packet was replaced.

## Native rendering scope

<!-- NATIVE TABLE -->
| Fixture | Logical screen | Colors | Visible viewport | Driver | Result |
| --- | --- | --- | --- | --- | --- |
| CGA low color | 160x100 | 16 | 0,0 160x100 | CGA100.DRV | PASS |
| CGA monochrome | 640x200 | 2 | 0,0 640x200 | CGA640.DRV | PASS |
| Tandy 16 color | 320x200 | 16 | 0,0 320x200 | TR53216.DRV | PASS |
| Tandy extended | 640x256 | 16 | 160,28 320x200 | HPXY.DRV | PASS |
| CGA large desktop | 320x200 | 16 | 160,28 160x100 | CGAPAN.DRV | PASS |
| Tandy 4 color | 640x200 | 4 | 0,0 640x200 | TNDY6404.DRV | PASS |
| CGA 4 color | 320x200 | 4 | 0,0 320x200 | CGA320.DRV | PASS |
| Tandy low width | 160x200 | 16 | 0,0 160x200 | TNDY160.DRV | PASS |
<!-- END NATIVE TABLE -->

CGA runs use an emulated IBM XT 8088 at 4.77 MHz; Tandy runs use a Tandy
1000 HX 8088 at 7.16 MHz. Both have normal 640 KB and Windows 3.0 real mode.
The Tandy fixture uses the required RESERVE 32 guard. Selected fonts and
driver sizes/hashes are retained in each PREPARE.json. These are emulator
observations, not physical-adapter or composite-output qualification.

The eight rows completed 624 QA frames and 48 matching white readbacks.
Both panning rows used the nonzero viewport position (160,28); Cube logged
the returned physical view and centered its drawing there.

Every passing rendering row exercised Flat, Dither and Wire. Six cases each
drew 13 complete frames: keyboard wake, held mouse button/release, movement,
activation loss, Close and stolen capture. Six white edge-pixel reads matched
between the GDI memory bitmap and target screen. No leaked input, timer,
capture, bitmap, DC or pen remained. Developer QA supplies native Windows
input messages and ownership API calls; it does not establish physical mouse
hardware coverage. Actual captures were inspected separately from assertions.

The renderer uses reported dimensions and the validated XY viewport query.
Driver and palette combinations absent from the table remain unqualified.
Generic dimension support does not certify every adapter/mode.

## Settings and actual idle launch

The exact current four-file kit passed native UI acceptance at 160x100x16.
Settings saved Style=1, Speed=3, Size=3; Preview launched and returned cleanly.
The shell saved Cube, enabled=1 and a ten-second idle delay. A real emulated
keyboard F2 established a fresh idle baseline, Cube launched on idle, and a
real Escape make/break gesture dismissed it. Installed file SHA-256 values
and actual INI values were checked. Both compact panels, including all bottom
buttons, fit in decoded 160x100 CGA video memory. See UI04 in EVIDENCE.
Preview ownership transfer also left the other task active and focused
without reactivation or focus repair by the controller.

## Installation and recovery

Native DOS installed the paired shell/input DLL, retained exact original
backups, restored both with /UNDO, reinstalled, and returned to DOS. The mono
case also deliberately supplied an unknown shell: the integrated installer
refused it, /APPONLY succeeded, and the unknown bytes remained identical.
Final app/shell/DLL and both backup SHA-256 values matched kit/baseline pins.
The original shell and DLL are not replaced in the accepted core packets.

All selected final receipts confirm their owned process stopped, the shared
byte lease was released and emulator inventory was zero. The closed CGA
fixture's two FAT copies matched after the mono test; later runners also
check FAT agreement at their quiescent acceptance endpoint. No unrelated
process was stopped. Private OS images/media, ROMs and native tools are excluded.

## Performance and source checks

CGA160x100 median second-frame draws were 0.77 seconds for
filled styles and 0.41 for Wire; CGA640 mono was 0.66 and 0.33 seconds.
These Windows tick observations include GDI and cooperative scheduling and
are not calibrated physical-machine benchmarks. Small size or Wire reduces
work. Every frame returns to the Windows message loop.

MSC6/LINK4 used /G0 /Gw /AS /W3 /Oat, NE target 3.0. The shell retains its
existing /Od build; Open Watcom builds the DOS installer with -0 -ms -os.
Host checks pass all 512 geometry phases, winding, lighting and tight bounds,
163 shell configuration/rollback checks, and idle/Hold checks including Cube
module/window wake exclusions. The scoped NE control-flow audit found no
post-8088 suspects in 3,218 instructions. Indirect continuations/tables and
imported Windows code are excluded; this is not exhaustive ISA qualification.

## Capture interpretation and retained failures

Original headless PNGs are retained. Headless scaling/offset varies by adapter;
*-VRAM.PNG decodes DEh cell attributes into RGBI logical pixels and uses
nearest-neighbor enlargement. This checks logical layout without claiming
a calibrated physical pixel aspect ratio. Evidence and harnesses are in the
separate source packet. CUBECTL is developer-only and must not be installed
or run in a Windows session containing user work. Autosaved 86Box configs
normalize paths; where INPUT.CNF is present, it preserves exact launch bytes.

Historical UI01/UI02 controller attempts failed to verify the edited delay.
The preceding UI03's cross-task WM_GETTEXT read confirmed ten before Apply
and passed
persistence/idle/wake. The failed attempts are retained, not counted as
acceptance. Historical prototype receipts are labeled separately. One FAT
file-growth preparation incorrectly launched an incomplete fixture; its owned
process stopped. Preparation now replaces entries and requires completed
receipts/config before launch. A stale-payload attempt stopped before
acceptance. A later missing old Tandy clone stopped before launch; the
completed fixture was copied into this task privately. Blank transitional
captures were replaced with a developer QA frame hold and pixel readback.

The final source ZIP is replayed after packaging: its complete member set,
all member hashes/sizes, 163 declared source files, committed CRLF bytes and
all five host groups are checked. Earlier source replay found omitted nested
DOS sources; the closed inventory now includes them.

## Independent review corrections

Independent source review found preview teardown could reactivate its settings
window after another task took ownership. Destruction no longer requests
activation. The actual production stop/WM_DESTROY code is compiled with API
spies: frozen pre-fix source fails with two activation requests; the corrected
source passes five paths, including normal wake and preserving foreign capture.
This is a deterministic source-policy regression, not native message-order
reproduction. The earlier native settling control passed the old code and is
explicitly retained as nondiscriminating. Corrected UI04 additionally records
a native ownership-transfer smoke with zero activation/focus loss events.

Independent packet review found source repinning could reuse stale native
evidence, and source replay omitted hashes for helpers outside ACCEPT.source.
The gates now bind every native source, recipe and runtime to build receipts,
require all ten advertised roles, and check every source-archive member before
extraction. Semantic source drift with only acceptance repinning, omitted roles,
modified helpers, missing/extra members and runtime/receipt tampering are rejected.
Independent re-review cleared both corrections; reports are in
EVIDENCE/INDEPENDENT. The earlier 0346d47 package remains withheld history.

Current native roles point only to UI04, LOW02, MONO02, TANDY03, PAN02,
CGAPAN02, T6404-02, CGA32002 and T160-02. Other native folders are historical
evidence for earlier runtime bytes; none qualifies the corrected binary.

Forced installer copy/rename failure paths were source-reviewed but not
native-fault-injected. Normal install, paired undo/reinstall and unknown-file
refusal/standalone preservation are the observed installation scope.
