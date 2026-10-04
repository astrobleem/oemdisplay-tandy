# Starfield verification

Current STARFLD.EXE is build10: 16,783 bytes, SHA256
`e06c9d80f977e1bda1db2d13be8af5f7d8b6f00285daa4f0e0159af00211b8d0`.
The SOURCE directory matches this executable's final source.

## Final build10 checks

- Six exact-runtime cursor ownership handoffs passed: activation, capture and
  focus change at both 160 and 640 mono. A prior build08-derived fixture
  overwrote another owner's IDC_CROSS; build10 preserved it in all six cases.
- Four actual SDL held-key/mouse cases passed at 160 and 640 mono, including
  held-input draining and no observed leak into the underlying test window.
- Two bounded animation benchmarks completed with stable warmed-up memory.
- Three final TSHELL integration reruns passed: primary shell at 160 and 640,
  plus secondary bar at 640. They cover Preview, wake/focus return, options
  staging/cancellation, saved presets, live idle selection, and disabling.

The ownership fix uses Windows 3.0 SetCursor's returned handle. It does not
import the Windows 3.1-only GetCursor API. Late WM_SETCURSOR is guarded and an
owned blank cursor is deselected before destruction.

## Earlier build08 coverage

Build08 was 16,239 bytes with SHA256
`c358104794d1241138321aa6d1f01470d19c95698837ae80197e651ad32fa36d`.
It passed five trial display modes, 16 lifecycle cases at both 160 and 640,
four actual held-input tests, saved options 1/64, Preview overrides 3/16 and
invalid-option fallback 2/32. Sampled GDI restoration had zero differences;
this is not exhaustive screen comparison. Its rendering and options code
were retained in build10, but this full historical suite is not claimed as a
fresh build10 rerun. The [final build10 screenshot](../../docs/SHOTS/STARS10.PNG) is an actual
emulator surface, not a generated image.

## Reproduction

```
SDL_AUDIODRIVER=dummy python3 SOURCE/BUILD.PY --repo /absolute/toolchain --dosbox /absolute/dosbox-x --out /absolute/new-output
```

Microsoft C 6 /G0 /Gw /AS /W3 /Od and LINK4 use owner-supplied Windows 3.0
headers/libraries. BUILD.BAT is the corresponding DOS procedure. No licensed
compiler, OS, ROM, guest installation or display-driver binaries are included.

Use an owned disposable 640 KB Windows 3.0 real-mode fixture, with the existing
reservation helper and its installed driver. `/A` runs lifecycle checks, `/I`
observes external held input, `/B` benchmarks animation, and `/O` runs the
three foreign-cursor handoffs. Diagnostics write STARFLD.LOG beside the
executable; normal `/S` does not create that log. `/S /V3 /N16` previews valid
unsaved speed/star-count overrides. Invalid whole tokens are ignored.

This renderer uses GDI on all drivers, with one star erase/draw per timer.
The timer interval is a request, not a frame-rate guarantee. Earlier build08
XT preset maxima were 385 ms at 160 and 220 ms at 640. Emulator presets are
uncalibrated; physical speed, long stress and low-memory faults are untested.
