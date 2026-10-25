# Unified panning settings: local native results

`NATIVE.JSN` binds the exact MSC6 XTPAN/PANCFG and Watcom XYCTL builds,
compiled source closure, native UI receipts and actual guest file identities.
`src/panui/VERIFY.PY` verifies it without starting an emulator.

All three UI cases passed in Windows 3.0 real mode with 640 KB:

| Case | Emulator and adapter | Geometry | Seconds |
|---|---|---|---:|
| PCJR | DOSBox-X PCjr, 8086_prefetch/fixed 200000 | 320x400 desktop / 320x200 view | 179.00 |
| COLORPLUS | 86Box IBM XT 1986/8088 4.772728 MHz, Plantronics | 320x400 / 320x200 | 337.03 |
| TANDYXY | 86Box Tandy 1000 HX/8088 7.159092 MHz | 640x256 / 320x200 | 727.86 |

PCjr covers the disabled notice, enable/OFF, stopped-enabled settings, repeated
invocation, edits, Tab/Enter/Escape, Apply/Cancel/persistence, invalid input,
Home, viewport tracking, repeated open/close and ordinary application use.
ColorPlus covers the actual Plantronics runtime, viewport placement, shared
owner, Apply/Cancel/persistence and OFF. XY covers its detected controls,
effective driver mode 1, persistence, unchanged mode after a second plain
launch, horizontal/vertical movement, Home, Calculator focus, owner removal,
and restart in software mode. These are emulator observations, not physical
hardware qualification. PCjr/ColorPlus remain software presentation.

XTPAN is 17,535 bytes (`3bece119...`), PANCFG 10,191 (`2c846db1...`) and XYCTL
21,160 (`35bc957c...`). Full hashes are in the JSON. All accepted driver,
font, grabber, logo, memory guard and ordinary Setup descriptor bytes remain
unchanged. The current core has exactly four changed archive members:
SETUP.EXE, README.TXT, WINXT/FIXXT.EXE and WINXT/XYCTL.EXE.

Measured warm helper allocations were 12,960 bytes for PCjr/ColorPlus and
30,048 for XY. ColorPlus returned its allocation exactly. The PCjr Calculator
case retained 704 bytes; further helper cycles did not reduce the final free
value. XY ended at 161,632 free bytes after Calculator and owner removal,
and repeated helper open/removal ended at that same value. No exact return
to initial global free memory is asserted for those application fixtures.

PCjr/ColorPlus returned normally to DOS. Tandy's bridge missed its final DOS
prompt format; actual text mode 03 and AUTOEXEC's RETURNUI.TXT after WIN /R
returned establish normal exit. The owned bridge was then stopped and its
lease released. This distinction is recorded in TANDYXY.ZIP/DOS-RETURN.JSN.
Failed earlier controller/bridge receipts remain in the private workspace.

HOSTUI passes 318 real strict-GCC checks through the managed wrapper, with
`-x c -std=c89 -pedantic -Wall -Werror`. Both unchanged-driver 64-frame saved
pixel oracles pass. Fifteen producer regression tests and four receipt-binding
tests pass. Independent source/package review found two missing receipt
bindings; both were fixed and reviewed clear.

## Qualified current review packets

JRPAN.ZIP and the flat native-install CPPAN.ZIP reproduce through
`tools/PANUI/PACKAGE.PY`. The main installer retains SETUP.EXE, README.TXT
and the expanded WINXT folder. Both native full installation and ordinary
Windows Setup use that one current source; consumers need no Python or
manual checksum preparation.

[PACKAGE.JSN](PACKAGE.JSN) and INSTALL.ZIP record the completed main update:
370 fresh outputs and 83 update outputs byte-matched, rebuilt C6 finisher
INSTALL/CHECK passed, and the normal CPSET stage passed. A cold boot from
those actual installed files used unchanged STARTXT -> WINXT.BAT readiness,
finisher and video-memory checks. The installed owner started automatically,
settings opened once, the owner stopped, and Windows returned normally to
DOS. The controller completed in 120.05 seconds; the owned native session
ended in 137.75 seconds with its child stopped, lease released and empty
process inventory.

The prior fixture's old custom Setup metadata was corrected privately to
already available exact supported stock metadata. Controller receipt-key
and owned-marker handling were corrected without rerunning completed cases.
Busy-lease preflights launched no emulator; other owners were not disturbed.
Earlier failed/cancelled controller records remain in the private workspace
and the startup raw evidence where applicable.

Main WINXT.ZIP is 660,289 bytes, SHA256
`c93d2310a8121785979a614df15c7a5d2f9bfbf335e9d85fe79bbdfd7fbdc614`.
The qualified runtime bytes are unchanged from the tested candidate.
No UI update has been published or merged by this local qualification work.
