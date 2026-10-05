# TANDINATOR v0.2: native-art experimental test build

A full-screen, offline Windows 3.0 character-guessing game for an 8088 Tandy.
The selected v0.2 build preserves the two owner-supplied 16-color sprite
sheets and uses exact pixel crops, cached native bitmaps and bounded eyes.
It includes an original curated 128-character, 128-question starter set.

**Experimental draft, not physical Tandy qualification.** This publication
adds an optional app only. No stable display/sound package, source builder,
Windows configuration, launcher or desktop default is replaced.

![Actual v0.2 320x200x16 emulator frame, displayed at doubled size](SHOTS/320x200x16.PNG)

## Try it on a working installation

1. Download [TANDI02.ZIP](TANDI02.ZIP), then read [the runtime guide](RUN/README.TXT).
2. Back up any older TANDINATOR files. Copy `TANDI02/RUN/TANDI.EXE` and
   `TANDI02/RUN/TANDY.DAT` together into a folder such as `C:\TANDINAT`.
   The optional installer refuses an existing EXE or DAT; replacing an
   earlier version is a deliberate user action after backup.
3. Start Windows through your **existing guarded WindowsXT launcher**,
   normally `C:\WINXT\WINXT`. Do not bypass reservation or recovery errors.
4. In Program Manager, File > Run: `C:\TANDINAT\TANDI.EXE`.

Use 1-5 or the answer buttons, Tab/Shift-Tab and Enter/Space. F1 shows help,
F2 shows scores, and Escape or the visible EXIT button closes the app. The
ordinary game saves no answers or learning history and makes no network
requests. Explicit `/T` test mode writes diagnostic logs/framebuffer dumps;
it is not normal play.

The two-file runtime needs Windows 3.0 real mode and the already working
Tandy environment. Python, Pillow, a compiler and network access are modern
host development tools, never Tandy runtime requirements. No Microsoft
Windows files, fonts, display drivers, compiler/DDK or guest image is in
this test kit.

## What is qualified

- Fresh strict 640 KB real-mode emulator games in 320x200x16, 640x200x2 and
  640x200x4, including mixed mouse/keyboard answers, rejected guesses,
  replay, help/scores, dirty redraws, same-task focus/expose restoration
  and three exit routes.
- Eight art/UI tests: immutable input hashes, exact native crops and packed
  atlas, text fit, nine bounded eye positions and actual framebuffer color
  indices in all three modes. 320x200 uses native sprite pixels; 640x200
  doubles horizontal pixels into a cached bitmap.
- 53 database/compiler tests; shared-C engine invariants for 128 and
  synthetic 2,000-record databases; scale and corrupt-DAT emulator runs.
- Emitted-code audit of 5,878 decoded instructions, with no unsupported or
  FPU findings. This is not a proof of every possible control-flow path.

Publication independently reran all 53 compiler tests, the eight art tests
against frozen native captures, ASan/UBSan engine checks at both sizes and
the emitted-code audit. The full retained QA is in the ZIP and
[QA.TXT](SOURCE/QA.TXT). The immutable engine/data match corrected v0.1.

## Honest limits

This is 128 authored characters, not 2,000 authored characters. The larger
database is a synthetic stress test. Simulated truthful answers give
128/128 first guesses at a mean 8.09 questions. With one or two deliberately
wrong answers, first-guess success falls to 71/128 and 39/128; all starter
cases eventually recover after rejecting wrong guesses. Synthetic two-error
stress has four failures within the ten-rejection cap. These are authored
database consistency checks, not a study of real human answers or verified
facts across every portrayal. See [curation sources](SOURCE/data/SOURCES.TXT).

Physical 8088 drawing, disk/CF latency and memory-pressure performance are
unmeasured. Fixed-cycle DOSBox-X timings are uncalibrated. Actual cross-task
Alt-Tab/Alt-F4 keypress behavior is not covered by the same-task expose test.
160x200 is unsupported. The 640x200 four-color mode remains subject to the
display driver's original EX/HX hardware caveat; its qualified emulated
palette is black/red/green/white, never sixteen colors.

## Source, checks and provenance

[SOURCE](SOURCE) is browsable matching code, original curated data, art,
host tools and tests. [BUILDING.TXT](SOURCE/BUILDING.TXT) describes rebuilding
with separately supplied authorized vintage tools. Some emulator helper
paths record the original development workspace and must be adapted on a
different host. The ZIP includes the complete matching source, original
source history and final evidence, with a full SHA-256 inventory.

`python3 examples/TANDINAT/TESTPUB.PY` verifies the immutable archive,
internal manifest, runtime identities, original art hashes, matching
browsable source and absence of excluded platform files.

The exact private-delivery archive is preserved as TANDI02.ZIP, SHA-256
`4b7da3fc7c9141c66dd43e8c84a4b177bc2cdf2b93cbad4d24f2cf83c6fbdb4c`.
Its original private-preparation wording is historical; this directory is
the public experimental publication record. Original source commit:
`3d514bc` (following corrected v0.1 `39688b1`).

Both original sprite sheets were supplied by the project owner for this
app upgrade. No visible third-party watermark or license restriction is
present. Their immutable hashes and exact crops are recorded in
[art/MANIFEST.JSON](SOURCE/art/MANIFEST.JSON). Authorship/upstream licensing
was not independently verified, and this publication invents no new asset
license. See [NOTICE.TXT](SOURCE/NOTICE.TXT); character names and trademarks
remain their owners' property. No proprietary Akinator data or copied
character portrait is included.
