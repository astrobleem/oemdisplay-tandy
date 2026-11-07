# Drawing and copy candidate

Cube drawing/copy optimization - native validation, 2026-10-30

Selected candidate: bounded clear/copy plus a monochrome GDI canvas for Dither and Wire. Flat keeps its compatible color bitmap and original gray shades. Both candidates preserve GDI ownership of all display pixels and the existing viewport, input, cursor, settings and cleanup paths. No raw VRAM writes, driver changes, phase cache or additional pixel buffer was introduced.

The original accepted baseline (832daf29599c5a0a392a3f8135fa40206ae550af, runtime 9ce367edd179291f324b011f8175afa90d298d1c60a644ef53d63ae56b43aa0e) and math-only candidate (717f7de954f76ad9d8c1839a6f09153f43a1d7cc, runtime 8844b44814563a28ed66226b4953511ef1001c7894c5c1a8efb6541ca69dddbb) remain intact in separate worktrees/build folders. New comparisons use the math-only drawing path as a control, with identical deterministic developer-QA phase/capture support in control and optimized builds. The control changes QA only, not ordinary rendering.

Why this target: a separate instrumented native build accumulated setup/math, bitmap clearing, GDI drawing, and copy/presentation time. Presentation includes GetDC, viewport query, BitBlt, QA readbacks/logging and ReleaseDC; it is not an isolated BitBlt CPU measurement. All stage clocks are Windows GetTickCount (~55ms).
320 Flat profile shares: setup/math 0.7%, clear 2.4%, draw 53.3%, copy/present 43.6%.
320 Dither profile shares: setup/math 0.4%, clear 3.2%, draw 53.9%, copy/present 42.6%.
320 Wire profile shares: setup/math 1.2%, clear 5.4%, draw 19.9%, copy/present 73.5%.
Historical TNDY160 160 Flat profile shares: setup/math 0.7%, clear 0.4%, draw 32.3%, copy/present 66.6%.
Historical TNDY160 160 Dither profile shares: setup/math 0.5%, clear 2.0%, draw 30.9%, copy/present 66.6%.
Historical TNDY160 160 Wire profile shares: setup/math 1.2%, clear 1.8%, draw 8.4%, copy/present 88.6%.

Candidate A computes a conservative one-pixel-padded vertex bounding rectangle and clears/copies its union with the previous rectangle. The canvas dimensions, geometry center and Bayer brush origin stay fixed, so shading and dithering do not shift. The entire transferred rectangle is cleared before drawing; old pixels are covered even after arbitrary phase jumps. Bounds reset on each drawing initialization; the original old-screen-position clear remains for viewport relocation.

Candidate B adds a 1-plane, 1-bit CreateBitmap canvas only for the two strictly black/white styles. Destination text/background colors are explicitly set to black/white for the monochrome-to-display BitBlt and restored afterward. Flat shading remains on the original color bitmap. This changes an application-owned GDI memory bitmap, not the display driver's logical planes or reported colors.

Conditions: separate private 86Box recorder instance, Tandy 1000 HX 8088 at 7159092 Hz, dynarec disabled, normal 640 KB, Windows 3.0 WIN /R, successful RESERVE 32, no EMS/XMS/UMB workaround. 320x200x16 uses pinned TR53216.DRV and XTE fonts; 160x200x16 uses pinned TNDY160.DRV and XTC fonts. Driver/font hashes and launch config bytes are in each PREPARE.JSON. MSC6/LINK4 native builds use /G0 /Gw /AS /W3 /Oat and NE target 3.0; toolchain/source/runtime pins are retained.

The controlled QA renderer draws the same 13 phases (39,47,...,135), speed=2, size=2, in each case. Native captures explicitly record phase 55 after two timer frames and phase 119 after ten timer frames. These are two late-enough poses to compare both geometry and stale-pixel erasure. Each style has two restart/input cases (26 complete rendered frames); timings below divide accumulated production render draw_ms by those 26 frames. They include geometry, clearing, drawing, copy and QA edge-pixel checks but exclude deliberate capture holds. Artificial QA elapsed duration is not treated as FPS. The samples do not benchmark every pose in a full 512-phase rotation.

Actual complete drawing cost, milliseconds/frame:
320 Flat: control 597.81; bounded-copy 519.62; selected mono/bounded 521.77; selected reduction 12.72%.
320 Dither: control 591.50; bounded-copy 519.65; selected mono/bounded 418.27; selected reduction 29.29%.
320 Wire: control 348.58; bounded-copy 276.77; selected mono/bounded 228.15; selected reduction 34.55%.
Historical TNDY160 160 Flat: control 929.46; bounded-copy 918.96; selected mono/bounded 921.15; selected reduction 0.89%.
Historical TNDY160 160 Dither: control 933.81; bounded-copy 918.88; selected mono/bounded 832.31; selected reduction 10.87%.
Historical TNDY160 160 Wire: control 699.15; bounded-copy 673.92; selected mono/bounded 648.58; selected reduction 7.23%.

Interpretation: the selected candidate improves actual drawing in these controlled Windows sequences, rather than only the geometry microbenchmark. The strong 320-mode differences are larger than clock quantization. The small 160 Flat change is not a reliable practical speedup. The historical TNDY160 copy/presentation stage was about 0.62s per call. That observation does not describe current TR51616; see the current-driver correction below. No universal physical-machine FPS or full-rotation improvement is promised.

Native correctness: both candidates in both modes passed all six 13-frame cases: keyboard wake, held button/release, movement, activation loss, Close, and stolen capture. QA supplies Windows messages and ownership API calls; it is not physical keyboard/mouse coverage. Every endpoint reported errors=0, leaks=0, capture=0 and resources=0 and returned cleanly to DOS. The selected/control pair completed 312 frames and 24 matching white bitmap/screen readbacks. All 24 paired early/late full-screen scanout captures are pixel-identical; both candidate experiments together have 48 passing paired captures. All captures were retained and representative early/late styles inspected.

Host/source checks: geometry equality remains exact for 136192 scale/phase plus 65536 unsigned-phase cases. The new bounds property group covers 136192 cases including vertices, clipping, old/new coverage and arbitrary jumps. A separate exhaustive per-cell rectangle-coverage check also passed. Configuration (163 checks), idle, Hold and actual teardown-policy lifecycle groups pass. Native scoped direct-control-flow audits report no post-8088 suspects (not exhaustive imported-code/indirect-branch ISA qualification). Q8 16-bit int/32-bit long math is unchanged.

Build closure: CUBERECT.H is added to the native build input copy/pin list and strict native source inventory, and TESTRECT.C is part of RUNHOST.PY. Existing acceptance/runtime/package pins are not relaxed or repinned to these partial native tests. Release packaging is intentionally still gated until the remaining native qualification and exact receipt closure are completed.

Selected code snapshot before these documentation notes: 1cb6f963fa6828a788397812854196e23c86fb46. Qualified selected runtime: b8d5fe0a6594800a9b51fa2a7fe7dc888f2e39dae64e81b03696beb83a6a50b6 (16703 bytes). Color/monochrome bitmap selection and bounding code now live in experiments/CUBEOPT/SOURCE/CUBE.C and CUBERECT.H. The accepted examples/CUBE/SOURCE tree is restored byte-for-byte. The paired baseline/control and both candidate binaries/recipes remain in their native-* folders.

BOR/Mesen: independent x86 work was explicitly authorized alongside Mesen. The x86 guard continues to require the shared byte lease, no other x86 emulator, unused control ports, private image/config, owned child job/watchdog and verified stop/release. Mesen inventory is observational and never blocks or controls that separate emulator family. No BOR/Mesen files, process, emulator state or ports were touched. These native experiments preceded publication authorization. Chad subsequently authorized publishing the tested source changes on a branch and opening a draft PR; approval and merge remain separately gated.

Retained non-acceptance attempt: native-render-profile stopped before launch because Python did not infer a loader for the uppercase .PY guard path. It was corrected with an explicit source loader, then compiled in fresh native-render-profile-02. No failed or timed-out emulator run is counted as acceptance.

Limits: these two Tandy modes and medium size/speed only; physical hardware/composite output, other five display fixtures, native interactive settings/resize extremes, full-period native raster comparison, long-duration memory profiling and installer/package acceptance remain unqualified. Host bounds checks cover the documented full scale range and native QA covers repeated starts/cleanup. No blocker remains to the requested drawing/copy experiments.

Evidence: RENDER-VALIDATION.JSON contains every native case, stage total, capture hash/pixel comparison, build/source/runtime pin, and cleanup receipt. Reproduction helpers are prepare_render_profile.py, prepare_render_candidates.py, prepare_mono_candidate.py, build_render.py, run_render.py and the queue scripts. Private guest images, licensed tools and ROMs are excluded from the compact evidence archive.

## Current TR51616 correction and separate BitBlt probe

Current TR5 160x200 cube validation, 2026-10-30

Driver TR51616.DRV c03925071ea1dd5943654a7c180c9b7efc59340c4bee5ae086773d4228b9ce3d (54880 bytes, Git blob 60f9c07f93be544c686d9eda661e73134de63e1e).

This supersedes performance conclusions drawn from historical TNDY160.DRV. Historical records remain intact.

Private 86Box Tandy 1000 HX, 8088 7159092 Hz, dynarec disabled, 640 KB, RESERVE 32, Windows 3.0 WIN /R, XTC fonts. Identical control/selected EXEs and 13 phases39..135 step8; 26 frames/style. QA holds excluded; QA pixel readbacks included.

Flat control 475.35 -> selected 426.85 ms/frame (10.20% reduction)

Dither control 462.62 -> selected 331.58 ms/frame (28.33% reduction)

Wire control 219.73 -> selected 147.77 ms/frame (32.75% reduction)

Both runs passed 78 frames, six source/screen readbacks and cleanup; all 12 paired full-screen captures are pixel-identical. No driver bytes changed.

Separate BitBlt probe: color memory full/dirty medians 22.3125/19.7422 ms per call; color display full/dirty116.75/96.125. Mono memory21.8828/18.8828; mono display116.625/89.25. Full49x95, dirty41x85, 3 batches each (128 memory or8 display calls).

Identity display full/1-pixel copies median549.25/528.625 ms/call are a documented full-resynchronization proxy. They do not represent ordinary cube bitmap-to-display calls. Memory/display differences include dispatch and conversion as well as flushing; internal flush-only cycles were not isolated. No driver change is proposed.

Probe completed30 error-free samples and native cleanup. Original host result FAIL retained: CRLF regex counted0 samples. Corrected parser plus independent closed-log/driver/FAT verification passed without rerunning or replacing measurements.

All owned children stopped and leases released; matched driver bytes verified after runtime. BOR/Mesen untouched. Physical hardware, full-period raster equality, other sizes/modes and full release-package qualification remain outside scope.

The machine-readable current-driver results, raw logs, exact driver/build identities and 12 paired captures are in EVIDENCE/RNDTR5. Source/runtime code is unchanged from the selected native-tested snapshot 2c50ab5d1759f84927640a3e06e755534e5f08d3. The following evidence additions change documentation only.

## Accepted gate correction

PR #215 initially replaced the accepted source tree with the unreleased candidate. The existing acceptance gate correctly rejected BUILD.PY against ACCEPT.JSN; the new builder copies CUBERECT.H, while the accepted native binary and original receipt predate that header. Updating that one source pin would not establish a new source/runtime binding.

The candidate now lives in experiments/CUBEOPT/SOURCE. All ten native compiler inputs are byte-identical to the tested snapshot; only the host lifecycle report path was adjusted. CANDIDAT.JSN explicitly labels its separate source/evidence pins PARTIAL_NATIVE_NOT_RELEASE. Candidate host and integrity/tamper tests run in an additional CI job. The original examples/CUBE/SOURCE files, accepted binaries, ACCEPT.JSN, all original receipts and the existing release gate steps retain their accepted bytes. The original workflow still assembles and replays the accepted packet; its success does not qualify the candidate for release.
