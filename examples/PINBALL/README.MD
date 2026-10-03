# Tiny Tandy Pinball

A small native Windows 3.0 / 8086 proof of concept: one ball, two flippers,
three bumpers, three balls per game and a score. No sound or external assets.
The white-on-black table remains legible in two-, four- and sixteen-color modes.

## Play

Copy PINBALL.EXE somewhere on your Windows 3.0 drive, then run it from
Program Manager File / Run. Use the accepted Tandy RESERVE/launcher setup
before starting Windows; this example does not replace or configure drivers.

- Space launches a ball from the center gap. After three drains, Space starts
  a new game. There is no separate plunger lane in this tiny table.
- Hold Z or Left Arrow for the left flipper. Hold / or Right Arrow for the
  right flipper. Releasing the key lets that flipper return.
- P pauses/resumes. Switching focus away pauses automatically and releases
  both flippers; press P after returning.
- Each bumper contact earns 10 points, capped at 999990.
- Close with the native system menu or Alt+F4.

The game uses a fixed 144-pixel-wide playfield and a fixed-size native window.
The minimum verified usable display is 160x200. Movement is visibly stepped
and can flicker while redrawing; this is an early playable proof of concept.

It is intentionally spare: no multiball, music, saves, high-score file, tilting,
physics realism claim, or Space Cadet recreation.

## Build

Use the parent project's existing Microsoft C 6 and Windows 3.0 SDK/DDK
toolchain. This archive does not include Microsoft tools, libraries or media.
Run BUILD.PY with --repo pointing to the existing toolchain repository,
--dosbox to DOSBox-X, and --out to a new build directory. For example:

    python3 BUILD.PY --repo /path/to/repo --dosbox /path/to/dosbox-x --out /tmp/pinbuild

The flags are /G0 /Gw /AS /W3 /Od, with LINK4 and the small-model Win16 runtime.
All game source is ASCII/CRLF and filenames are DOS 8.3.

Host regression:

    python3 TEST.PY

TEST.C also builds as a native Windows test executable when HOSTMAIN is not
defined. Copy it as PINBALL.C in a separate build fixture and use the same
BUILD.BAT/DEF/RSP and PHYSICS.H. It writes C:\PINTEST.LOG and exits.

## Implementation and limits

PHYSICS.H is shared unchanged by game and tests. Positions are Q6 fixed point.
Each 55ms timer message advances exactly four bounded substeps, at most
1.75 logical pixels per axis per substep. Long intermediates protect projection and
reflection arithmetic on a 16-bit compiler. Three circle bumpers and four
line capsules use conservative separation. A tiny deterministic horizontal
nudge breaks perfectly vertical bumper/ceiling loops.

Delayed Windows timers slow the simulation rather than cause catch-up jumps.
The timer interval is a request, not a guarantee of 18 frames/sec. Ball updates
invalidate only its old/new small rectangles; flipper and score areas update
only when changed. Full repaint happens for launch, drain, pause or exposure.
A compatible-bitmap cache holds the static table (about 14.5 KB at the tested
154x181 client size with four logical planes). Repaints copy just the dirty
rectangle and redraw intersecting dynamic parts; a square ball avoids repeated
ellipse scan conversion. If allocation fails, direct GDI drawing is retained
as a slower fallback. No expensive filled polygons are used.

See TESTS.MD for the actual verification record and remaining limits.
