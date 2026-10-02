# Acceptance - 2026-10-02

TABOUT.EXE: 6,479 bytes; SHA256
b13fb3cf53cabe28692c1902417768e4cf87de3fa34d6d05212a00d8d9c171ed.
A fresh documented rebuild matched this EXE byte-for-byte.
Production source SHA256:
b7a8cc7834afaa6bc4067ffd8ab3f41ecc4c428f0eaa94a8bfa9e7d7ff587298.

## Native tests

690 / 690 assertions passed: 138 in each accepted actual-driver Windows guest.
160x200x16, 320x200x4, 320x200x16, 640x200x2 and 640x200x4 all passed.
The exact source snapshot is included by ABOUTUT.C and executed natively
inside Windows 3.0 real mode with 640 KB, 8086_prefetch semantics, FPU off and
EMS/XMS/UMB off. There are no host-mocked Windows API results.

Checks cover actual resolution and physical color count, four logical planes,
one bit/plane, WinFlags=64 real mode and 8086/8088, Windows version and free
memory, native control creation/geometry, measured page/footer text bounds,
all page selection routes, arrows, repeated refresh, Tab/Shift-Tab traversal
and wrapping, Escape and ordinary WM_CLOSE. CPU-family formatting is also
checked with synthetic flag combinations. Source/hash, build, configuration,
per-guest logs and result JSON are under EVIDENCE/UNIT. Guest paths in records
identify fixtures from this run; Windows media is not bundled.

## Visual and input acceptance

Every page was visually inspected on all five real driver profiles. Text,
buttons, focus marks and keyboard footer fit; the 160-pixel screenshot is the
minimum-resolution check. S/D/M navigation, Refresh and Tab/Space were exercised
through real emulator input. The native System button was also clicked with
the captured serial mouse at160x200; it changed the page and focus correctly.
The final Tab correction was retested by native harness and narrow GUI.

This is emulator evidence, not physical-hardware verification. Accelerated
cycles were used for practical QA; no calibrated timing/performance claims.

The only app-side correction found was first Tab from parent focus originally
selecting Display. It now starts at System; Shift-Tab starts at Refresh.

No display driver, Cookie demo, OEM package or installation was changed.
