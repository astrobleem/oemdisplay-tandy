# Historical Tandy Start 06 verification

## Exact production candidate

- TSHELL.EXE: 29,555 bytes; SHA-256
  34d441cf8c9a544eaf08d2e89503ac032f00949f2c29b99173d79a72f1d0f2e0
- TSINPUT.DLL: 3,082 bytes; SHA-256
  cbb4a851a7f4489945e42c758bb2519415f85270dabe105781acfb056d0521f8
- ../MATRIX/MATRIX.EXE: 14,157 bytes; SHA-256
  0987936c3b80eb9fc5718f3022996514f6885adbdf83cd05128d01bc19de17c8

Independent native rebuilds reproduced the final shell, DLL and Matrix bytes.
The shell uses Microsoft C 6.0 /G0 /Gw /AS /W3 /Od. DLL code and single shared
data are fixed/preloaded, with no local heap; exports and USER/KERNEL imports
were checked directly in the final NE file. Matrix uses /G0 /Gw /AS /W3 /Ox.

## Portable source checks

Run Python 3 and GCC through TESTS/RUNHOST.PY. It covers the unchanged 210
selector assertions, all seven completed SELECT and seven RECOVER mutation
checkpoints, 26 nested recovery interruptions, later unrelated edits,
collision/corruption refusal and short writes. Twelve group-parser categories
include 1,000 mutated files and command/slot/string/checksum bounds. Twenty-three
startup/exit cases cover ordering, duplicates, busy helpers, veto and failures.

Version 06 adds SVCORE deadline boundaries, once-per-interval behavior, activity
and blocked resets, and 32-bit timer/generation wrap. The idle observer tests
ownership, duplicate hook refusal, chaining, held input, modal/capture guards,
non-consuming normal polls, polling gaps, suspended Windows time, midnight and
backward DOS-clock changes, removal failure and WEP cleanup. The host stub uses
a pointer-sized DWORD for callback pointers; native NE/ABI checks cover the
actual 16-bit target separately. The runner also verifies the shipped DLL's
fixed-segment/export/import contract. Tests leave no generated source files.

## Final native integration

The final integration recorded 89 passing checks across 32 native fixtures
and a host policy check, including 45 legacy checks rerun on this exact shell.
Tests used DOSBox-X 8086_prefetch, 640 KiB conventional memory with 16 KiB video
reservation, no XMS/EMS/UMB, no FPU, and 160x200 16-color plus 640x200 monochrome
Windows 3.0 real-mode displays. Accelerated functional emulation is not an
original-clock or physical-machine timing measurement.

A separate foreground Windows app received real SDL keyboard and captured
relative mouse input. More than 15 guest seconds of other-app activity
prevented a 10-second idle launch. Quiet input launched one Matrix instance;
another complete idle interval did not create a duplicate. Actual keys and
mouse motion dismissed it and restored the app/desktop on both displays.
Held-key/button, capture, popup/dialog and known audio-class guards passed,
as did shutdown veto/resume. Three saver/unload cycles on each display returned
GetFreeSpace to the same observed baseline: 325,344 bytes at 160 and 277,952 at
640. This is a three-cycle measurement, not a universal memory-growth claim.

A real DOS COM/PIF interval paused Windows GetTickCount for 12 BIOS seconds.
The owner-side DOS clock comparison blocked stale immediate launch, required
a fresh release, then allowed a new full idle interval. Tests observed no
saver for 11 guest seconds after return before providing a new input gesture.
A clearly labeled 20-second test chime verified startup serialization; real
chimes ran separately in legacy cases, without an audible-quality claim.
A secondary nonprimary TSHELL bar loaded neither the hook nor the saver.

Real About This Tandy opened through Start/System at both widths. Compact
menus/notices were visually checked. SDL button pairs showed that only the
clock area opens Clock on double-click; Start and empty-bar double-clicks did
not. Calendar opened when Clock was absent. The clock tests used a control
app to position the cursor, then real button events; no direct double-click
window message was posted. Genuine mouse movement was tested separately.
Disabled saver, missing Matrix, invalid interval, missing DLL and malformed
DLL continued safely. Missing/bad-DLL notices fit the 160-pixel display.

The 45 legacy checks cover group paging/bounds/read-only handling, saved
arguments and working directories, real keyboard Run/Browse, missing/corrupt
groups, local common-dialog and CD-start support, 20 stable menu cycles,
startup choice/order, busy/missing helpers, exit veto/retry and silent fallback,
shutdown while a notice is open, and the direct-DOS TSTART/Windows/restore
lifecycle. The accepted selector, DOS batches and sound helpers are unchanged.

## Limits and historical evidence

Ten-second idle intervals exercise the same parser/policy as the shipped
300-second setting. An independent observer's IdleReady is not a readiness
verdict because only the installing shell task owns that query. Assertions
used genuine input, actual launches/windows, activity generation and guest
clock measurements. Disabled/rejected paths need not execute copied helper
fixtures; the actual final runtime trio was used for live acceptance cases.

Physical tests of these new controls, global hook and Matrix /S behavior are
pending. Earlier acceptance of Tandy Start 05 and on-demand Matrix does not
qualify the new features. Original-clock performance, acoustic quality,
forced allocation exhaustion, arbitrary third-party sound engines, unknown
PSG writers and non-yielding apps are not certified. No emulator test proves
all possible torn disk writes or arbitrary corruption recoverable.

This document summarizes bounded native evidence; raw environment reports,
private paths, OS media, toolchains and test-control binaries are excluded.
Existing MILESTONE.ZIP and pre-06 EVIDENCE files are historical. They are not
reruns of this candidate. The current portable checks can be run from source;
native reproduction needs the tester's own licensed Windows/DOS and tools.

