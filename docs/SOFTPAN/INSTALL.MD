# Native installation workflow

The installation checks use disposable Windows clones and the existing shared
emulator lease. Accepted packages and host installations are untouched.

Native DOS Setup is exercised by the existing `tools/XTLOGO/SKCTRL.ASM`
BIOS-keyboard controller, specialized by `src/softpan/NATSET.PY` for the
candidate source folder and OEM row. It reads mode-3 text, selects Display,
Other, the source path and the OEM entry, then accepts the selection and
returns to DOS. `KEYTRACE.BIN` records phases 1 through 6. The runner verifies
the selected driver bytes against the packet after Setup returns.

Windows maintenance Setup does not offer the DOS frontend's Other selection;
the documented installation route remains plain DOS Setup.

`UITEST` is a test-only Windows observer. `UIFLOW.PY` operates the real
Program Manager File/Run dialog and its edit/OK controls, then records the
display geometry, viewport, helper window, startup entry and memory. It does
not edit Windows configuration or install a driver itself. Its DOS buffer
flush makes completed records visible in the PC DOS 3.20 disk fixture.
`RUNUIJR.PY` owns bounded DOSBox-X PCjr sessions. `RUNUI86.PY` reuses the
existing 86Box debugger/headless API for the ColorPlus session: CPU resume,
read-only observations and framebuffer capture. It updates only a
preallocated fixture input file's data sectors while the guest is paused;
it does not write guest memory, registers, FAT entries or directory metadata
during Windows execution. Native Setup runs in the DOSBox DOS frontend;
ColorPlus Windows runs on the qualified PC DOS 3.20 Plantronics fixture.

## PCjr result

Other -> `C:\JRPAN` -> experimental 320x400 selection returned normally.
The installed driver matches the qualified candidate. `JRSTART` reached
320x400; native File/Run PANCFG enabled panning and preserved the observer
startup entry. The next guarded session loaded XTPAN automatically. OFF
removed it and preserved the observer entry. Native DOS Setup selected
Other -> `C:\PCJREXP` -> accepted 320x200 entry. `JRWIN` then reached
320x200 without the helper and exited normally. The restored TNDYJR.DRV is
byte-identical to the accepted packet.

PCjr memory in the observer's stable sampling point was 286,816 bytes before
helper startup, 278,720 with it running, and 286,816 after each of three OFF
cycles. The existing rendering fixture's 128-byte difference was already
present at FREE_CLEAN, before the helper was launched. It is a pre-helper
fixture/resource cost, not a measured residual from helper removal. The
exact owning GDI resource was not isolated. These measurements do not claim
that every allocation in an entire Windows session returns to its entry
value.

## ColorPlus fixture correction

The first installation clone contained accepted fixed-driver bytes under
CPPAN.DRV from the earlier baseline comparison. Native Setup selected the
candidate description but retained that already-present filename; Windows
correctly reported 320x200. That was a fixture defect, not a candidate pass.
The corrected fixture uses PCP3216.DRV for the accepted baseline and removes
the mislabeled copy. A new native Setup run copied the actual 58,864-byte
CPPAN.DRV and verified its exact candidate hash. The installed Windows then
reported 320x400 and File/Run PANCFG started the helper and panned to top 50.

The earlier 64-frame ColorPlus rendering evidence is unaffected. A direct
read of cp-panned-dos320-01/DISK.IMG confirms its selected
WINDOWS/SYSTEM/CPPAN.DRV is 58,864 bytes with SHA-256
af32878ca8cd62e765b140f9cbf604dd00b120ec9e21f89c0f8420626f98e54f.
Both saved HOSTRUN logs report HORZRES=320, VERTRES=400, START_TOP=0 and
COMPLETE=1, matching CP-RUN1/2.JSON's driver hashes and pixel verdicts.
The mislabeled file was in cp-fixed-dos320-01, the later Setup clone's
source, and does not contaminate that separate panned image or its logs.

PC DOS 3.20 does not support CALL or @ECHO. The disposable test wrapper was
corrected to chain the actual launcher directly. CPPAN-INSTALL.ZIP also
changes CPWIN.BAT's first line to ECHO OFF, avoiding a visible bad-command
warning. Its drivers, support files and helper bytes match CPPAN-REVIEW.ZIP.

The corrected candidate's first session enabled XTPAN through native
File/Run. Its next session automatically loaded the helper; File/Run PANCFG
OFF removed it and preserved the observer entry. Free memory was 303,136
bytes before the helper, 295,040 with it, and 303,136 after OFF. This is the
same complete 8,096-byte helper return measured on PCjr, at each adapter's
own stable sampling point.

The initial ColorPlus UI exit screenshots capture the mode-3 handoff and
are not, alone, proof of a returned command prompt. The earlier full
rendering suite already records two normal panned-driver DOS returns. The
final fixed-profile installation runner additionally waits for the actual
C> DOS prompt after Windows exits. The final capture shows C>; the owned
process was then stopped and its lease released. The matcher originally
expected a path in the prompt and was corrected to accept PC DOS's default
C>. No extra Windows session was needed. The bounded lease logs distinguish
the intermediate stopped/raced test runs from completed results.

Native ColorPlus rollback selected PCP3216.DRV, verified against the accepted
packet's SHA-256 67f8a3d77574f8f78d2751f68b9c303fc59fcacd93325b9aa4aaf10288c7c406,
and the resulting Windows session reported 320x200, no helper and the
preserved observer startup entry. PCjr's final restored TNDYJR.DRV hash is
a29cabbaa28b447893cd25d4cf9cf37435332697312fd4fcfcf6f4cddb8a23c4.

Final packets: JRPAN-REVIEW.ZIP and CPPAN-INSTALL.ZIP. Their complete hashes,
observations and emulator identities are in INSTALL/RESULT.JSON. The ZIPs
inside INSTALL/ contain logs and raw records, not installation media.
JR-INSTALLED.PNG and CP-INSTALLED.PNG are decoded VRAM; the CP-NATIVE and
CP-DOS-PROMPT captures are actual emulator framebuffer images.
