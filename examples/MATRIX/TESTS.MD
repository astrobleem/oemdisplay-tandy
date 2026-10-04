# Matrix /S verification

Current MATRIX.EXE is 14,157 bytes, SHA-256
0987936c3b80eb9fc5718f3022996514f6885adbdf83cd05128d01bc19de17c8.
A warning-free Microsoft C 6.0 /G0 /Gw /AS /W3 /Ox build was independently
rebuilt byte-for-byte. The renderer and exact five-name direct-drawing
whitelist are unchanged. Unknown/trial aliases use clipped GDI rendering.

## Component evidence

The final binary passed 15 native /A restoration/control cases in each of
five 200-line display modes: 160x16, 320x16, 320x4, 640x4 and 640x2 (75 cases).
All restored activation and released owned capture. Canonical TNDY6402 used
an exact visible-byte comparison. Four trial aliases used a GDI sample grid
at every eighth pixel, which is not full-pixel proof.

Cases covered key/character/system-key release, one-pixel mouse motion,
unchanged synthetic motion, held buttons and second clicks, Close,
deactivation, cancellation, both shutdown outcomes, repaint and overlap.
Live capture theft passed all five modes: Matrix left the other window's
capture intact. An already running ordinary Matrix rejected a new /S launch.
Five ordinary 60-update /T runs and two held-button checks per mode passed.
Those component cases used native Windows messages, not physical input.

An earlier candidate's real desktop keyboard test held a letter over an EDIT
control for two seconds; the edit text was unchanged and focus/activation
returned. Final changes added capture-loss and Ctrl-Break release guards;
the letter drain/focus logic was unchanged. This observation is not claimed
as a final-candidate physical or manual-mouse test.

Portable SOURCE/RUNHOST.PY covers 30,000 rain ticks, shade/glyph/dirty-cell
invariants, 262,144 packed pixels and visible row bounds with address/undefined
behavior sanitizers. LeakSanitizer is disabled for sandbox compatibility;
the tested renderer uses static arrays and no dynamic allocations.
A scoped final 8088 disassembly audit examined 4,066 reachable instructions
without later-CPU suspects. Imports and unresolved indirect continuations
are excluded; this is not exhaustive ISA proof.

## Integrated final-candidate evidence

The exact final Matrix, TSHELL and TSINPUT trio was exercised at 160x200x16
and 640x200 monochrome. Real SDL keyboard and captured relative mouse input
in another Windows app suppressed idle launch; quiet input launched exactly
one saver. Genuine wake keys/motion restored the preceding app and desktop.
Three saver/unload cycles per display showed stable observed GetFreeSpace.
See ../TSHELL/TESTS.MD for the 89 combined checks, guards, DOS suspension,
clock/About controls, startup behavior, and evidence boundaries.

## Reproduction and limits

SOURCE/BUILD.PY needs owned Microsoft C 6 and Windows SDK tools. RUNLAB.PY
clones an owned installed guest for /A or /T tests; it requires a fresh output
directory. TESTSRC builds the optional MXGUARD observation app. That binary,
OS executables, donor disks, SDK libraries and compiler tools are excluded.
SOURCE/DECODE.PY requires Pillow; SOURCE/AUDIT.PY requires objdump and the
matching build map. The older SOURCE/VERIFY.PY, if present in the repository,
checks historical ordinary /C and /Q run layouts, not the new /S acceptance.

The cooperative saver can consume a wake gesture while it owns focus/capture.
Forced deactivation, shutdown or capture loss cannot guarantee swallowing the
remainder. Non-yielding tasks, arbitrary video writers, original-clock speed,
physical hardware and forced allocation failure remain outside certification.
Earlier on-demand hardware acceptance does not qualify the new /S behavior.

Existing MILESTONE.ZIP, MANIFEST.JSN and earlier EVIDENCE files are historical.
Current results are summarized here; raw private environment reports and
binary test payloads are not added to the public tree.
