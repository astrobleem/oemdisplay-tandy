# Runtime acceptance - 2026-10-02

Final COOKIE.EXE: 8,543 bytes; SHA256
9edbfc5c23a245c555af690391d6a7f6efccd6db552de5473e613e9c2bae2a14.
A fresh documented BUILD.PY rebuild matched it byte-for-byte.

## Native Windows checks

All five accepted Setup-produced installations passed 82 native tests each:
160x200x16, 320x200x4, 320x200x16, 640x200x2, 640x200x4.
**410 / 410 passed; zero failures.** This is emulator evidence, not hardware.
Each ran Windows 3.0 real mode, normal 640 KB, 8086_prefetch instruction semantics,
FPU off, EMS/XMS/UMB off. Accelerated emulator cycles were used for practical QA;
these results make no physical 8088 speed or calibrated CPS timing claim.

The harness compiles the exact final COOKIE.C snapshot as SUBJECT.C and directly
executes its real WndProc and save/load functions in Windows. It verifies native
window/button creation, actual SetTimer delivery, inside/outside cookie hits,
keyboard increments, upgrade cost and limits, saturation, exact save bytes,
round trip, every one-byte corruption, all truncated lengths, extra bytes,
invalid signatures/versions/ranges, missing/unwritable paths, preserved live
state on failed loads, and native About creation, measured layout and OK closure.
EVIDENCE/UNIT contains its source, build inputs, logs and JSON records. Captured
fixture paths in JSON/configs describe this actual run, not bundled Windows media.
To reproduce independently, compile COOKIEUT.C with BUILD.BAT using the full
project toolchain and launch COOKIEUT.EXE in a disposable accepted guest. Do not
run it beside a real save: the harness deliberately writes malformed test saves.

## Visual and input pass

All five final builds were cold-launched, inspected in raw native emulator
captures, and exercised through Game/Help menus, unaffordable Upgrade feedback,
About/OK, Load and passive generation. At 160x200 the cookie was also clicked
with the actual mouse, followed by nine Space presses to reach exactly ten, then
the native Buy button was exercised with the captured serial mouse (CPS became
1 and the status confirmed Upgrade bought). Save/New/Load and About/Escape
were additionally exercised in the narrow-mode development and final passes.

The minimum verified usable screen is 160x200. Count/CPS, cookie/chips, buy,
status and keyboard hint fit. Native Game/Help menu labels and dropdown commands
fit, as do the complete About text and native OK. The compact caption is Cookie;
the complete benchmark name appears in About and this guide. No horizontal
scroll, toolbar, common file dialog, or large standard message box is used.

Resolved app-side findings:
- Whole-client timer invalidation erased the button during repaint. Repaint is
  now limited to count/status regions and the parent uses WS_CLIPCHILDREN.
- Disabled native button text mapped to white in the 2/4-color modes. The final
  native button stays enabled/readable and reports affordability in the status.
- Default EGA vs CGA dialog units produced different About scaling. Final About
  explicitly sizes its client and native OK in pixels after dialog creation.

Remaining honest limits:
- In 320x200x4 and monochrome, the cookie fill maps to white. Its black outline
  and chips remain clear. 640x200x4 maps its fill to red; 16-color modes to yellow.
- Native Windows non-square pixels alter apparent proportions. Raw captures
  are 320x200 for logical160x200 (column doubled), 320x200 for both320 modes,
  and 640x400 for logical640x200 (row doubled). They are unretouched.
- Windows timers may coalesce under slow repaint or other programs; there is
  no offline catch-up. This is a usability exercise, not a timing benchmark.
- A window manually reduced below the intended compact size may clip. Maximize
  it again; smaller screens and physical Tandy hardware are not verified.
- Save overwrites in place, checks write/close, and reports failure, but is not
  crash-atomic. Load rejects a damaged save and preserves current state.

Driver scope remained untouched. The source worktree adds only examples/COOKIE.
