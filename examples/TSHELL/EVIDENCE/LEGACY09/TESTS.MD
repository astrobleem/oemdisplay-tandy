# TSHELL verification record

Production build09: 7,423 bytes; SHA256
7027211a07888a903ff736a3f2c37579a5b4855d82d9408ca8ecf71716b8cbdf.
Two clean /G0 /Gw /AS builds match byte for byte. BUILD.PY marks the NE
expected Windows version as 3.0 after LINK4, equivalent to resource-compiler
/30 marking for this resource-free program. Protected-mode-only is clear.

## Native automated evidence

Five isolated Windows 3.0 real-mode cold boots use shell=tshell.exe:
160x200x16, 320x200x4, 640x200x4, 640x200x2, baseline 320x200x16.
The instrumented production-source probe checks the real-mode flags,
shell selection, native bar/control geometry, available and missing apps,
WM_QUERYENDSESSION acceptance, and an actual DOS clock minute transition.
The clock is neither set nor simulated. All five passed. Dialog probes
open the compact confirmation three times per mode: two cancels and one
acceptance without actual exit; geometry, default Cancel and survival pass.

Separate 160/640x200x4 menu probes send a synthetic native menu mnemonic and
verify WM_COMMAND reaches the real launch routine and creates Notepad.
This is not a physical mouse test. A native Program Manager test confirms
an existing minimized instance is restored, visible and active. A loader
starts the unmodified final EXE at 160 and closes only the bar; Program
Manager remains alive. Exact logs, test source and build inputs are included.
CHECKS.JSON contains the aggregate assertions over those final logs.

Guests: DOSBox-X, machine=tandy, 8086_prefetch, 640 KB conventional memory,
no EMS/XMS/UMB; accepted RESERVE runs before Windows. Cycle settings are
emulator conveniences, not physical Tandy performance measurements.

## Interactive verification and captures

Final production build09 cold-booted as the real shell at 160. The clock,
Start popup and compact exit confirmation fit. Keyboard menu navigation,
Program Manager launch/restore and task return were observed. Confirmed
Exit Windows completed normally and returned to DOS (EXIT.OK). Restoring
only the saved SYSTEM.INI cold-boots stock Program Manager without the bar;
its original binary and the restored INI hashes match the originals.

Production build08, used as a regular app at 640x200x4, launched Notepad
through F10 and its mnemonic. A disposable unsaved document triggered the
stock save warning during Exit Windows. Cancel preserved the text and
returned to the shell with Exit canceled. SAVE08/VETO08 captures identify
that earlier binary explicitly; build09 only adds Program Manager restore
handling, but the dirty-document interaction was not repeated on final09.

Live serial-mouse activation could not be verified through this emulator's
remote input path: the guest pointer did not follow injected host movement.
Mouse support uses the native Windows button/menu, but a real mouse check
on the target setup remains required. Do not call this complete mouse QA.
GUI screenshots cover final160 and earlier640x200x4; the other three modes
have native automated checks rather than manual full app sessions.

## Memory measured on the final production binary

In every mode, the ordinary-app loader observes an 11,168-byte decrease in
GetFreeSpace(0). Runtime GlobalSize reports a 5,232-byte code block (resident,
not discarded at measurement) and an 8,976-byte instance data block: 14,208
bytes together. Those block sizes and the availability decrease overlap;
do not add them. The latter is not a complete resident-memory census.

The NE code is 5,200 bytes before loader rounding; minimum data is 1,792
bytes, heap 2,048 and stack 4,096. Budget roughly 20 KiB for the bar plus
transient menu/dialog allocations and memory for launched applications.
That is a planning estimate, not a measured maximum including all shared
Windows resources. Fragmentation and loaded fonts/modules affect capacity.
The shell creates no full-screen bitmap; popups are allocated on demand.

## Limits and reproduction

Stock Program Manager/app windows can clip at 160; the shell does not
rewrite their layout. Other apps may cover the bar; use Windows task
switching. This is a launcher/clock, not a task-list manager. No physical
hardware, complete application compatibility, launch-failure injection,
or Windows host-wrapper claims are made.

Build via BUILD.PY in the repository. EVIDENCE/{PROBE,DIALOG,MENU,MEMORY,
PMRESTOR,CLOSEBAR} contains exact instrumented/helper sources and build
inputs; pass --repo explicitly when building those copies. CONFIG.TXT
records the test emulator profile; provide a fresh isolated installation
from your own media and accepted driver/RESERVE arrangement. No Windows
media, stock applications, guest disks or compiler binaries are included.

Do not put /S in SYSTEM.INI: that early experiment stalled startup. The
supported and verified setting is plain shell=tshell.exe. No earlier
incomplete experiment is counted as a pass.
