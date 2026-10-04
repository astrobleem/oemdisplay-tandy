# Experimental 8088 drawing and color update

This development chain starts from ca795d46329cfdf1dd62be935078534ed4ac4129.
It preserves the existing resource, palette, reservation and Setup contracts.
The current source builds the final Output-row family recorded in BUILDS.JSN.
Existing src/tandysw/bin payloads, root runtime ZIPs and MAKEDISK/STAGE pins
remain unchanged. A newly built driver intentionally does not satisfy those
older accepted-package pins. Do not relax the pins or overwrite old binaries.

## Changes

- Read-only GDI queries retain real renderer calls and return values while
  avoiding unnecessary framebuffer copies.
- Cursor refresh retries are bounded; the latest position remains pending
  for the normal cursor maintenance path. There is no asynchronous GDI flush.
- Screen-destination BitBlt/SetPixel use proven row and byte-column bounds;
  eligible plain text uses conservative vertical bounds. Unknown cases retain
  full refresh. The canonical shadow remains authoritative.
- REP plus source-segment override copies are replaced with 8088-safe
  JCXZ / single-prefix MOVS / LOOP sequences. A build audit rejects unsafe
  multi-prefix REP instructions. Zero count, flags, direction and sequential
  overlap semantics are preserved. This fixes a reproduced 8088 restart
  failure during generated drawing-code construction.
- Cursor retention compares the actual flushed physical footprint, with the
  existing synchronous lock/hide semantics for overlap and uncertain cases.
- Output uses bounded full-width rows only for proven count-2 thin polylines
  and solid single scan intervals. Unknown inputs retain full refresh.
  Marker suppression, general polygon bounds and deferred conversion are absent.

Identity screen-to-screen SRCCOPY remains a full-screen resynchronization,
including the existing one-pixel identity call used by direct-render apps.
RESERVE.COM and its memory validation are unchanged. The lower 16 KB reserve
protects 98000h-9BFFFh while the normal BIOS memory limit already excludes
9C000h-9FFFFh; together these cover the 32 KB modes. No UMB bypass was added.

## Build and checks

Use the existing authorized DDK/compiler/linker inputs and DOSBox-X build
workflow documented by the repository. No new toolchain, OS, font or ROM
payload is included here. Run from a checkout containing this source delta:

    python3 src/tandysw/TSTCHAIN.PY
    python3 src/tandysw/TSTREP88.PY
    python3 src/tandysw/BUILD88.PY --dosbox <dosbox-x> --out <fresh-output> --mode <profile>

Profiles: 320x200x16, 640x200x4, 160x200x16, 320x200x4, 640x200x2.
Compare output driver bytes and SHA256 with BUILDS.JSN. Review RESULT.json
for the emitted ISA, link and multi-prefix-copy audits. TSTCHAIN stages all
five exact source pipelines and checks their assembly hashes; it does not
execute guest code. TSTREP88 without optional inputs checks fifteen static
listing-audit examples; it is not an interrupt stress test.

TSTCOL.PY and VERKEEP.PY preserve the earlier stage-specific checks. Their
--baseline inputs must be the matching earlier compiled stage, not the new
final outputs. They are not a standalone full regression command. Runtime
renderer and GUI results below are completed engineering observations;
the full owned-media test fixtures are not included in this source delta.
Do not describe the two short host commands as repeating those runtime tests.

BLDTR3.PY preserves the earlier TRIAL 3 build entry point for reproducible
monochrome rollback. To rebuild that exact parent, use a SEPARATE checkout
with this same source set, copy BLDTR3.PY over src/tandysw/BUILD88.PY there,
and build 640x200x2 normally. The unused OUTROWS.PY may remain present.
That pipeline omits the Output-row pass and must produce TR36402's hash
listed in experiments/TRIAL4/FILES.JSN. Do not execute BLDTR3.PY in place;
its relative imports are intended for src/tandysw/BUILD88.PY.

REPCOPY88.PY retains its original nine-character host filename so the tested
production source identity stays exact. All supplied DOS runtime names and
new test/document names are 8.3. Source and text files use CRLF.

## Evidence and limits

See VERIFY.TXT for measured scope and remaining gaps. BUILDS.JSN pins all
five final development binaries; only four new color drivers are supplied
as trial overlays. The new 6402 Output build is development-only. Its bytes
are not the physically tried TRIAL 3 monochrome fallback.

The physical reports cover TRIAL 3 640x200x2 use and a later 320x200x16
Paintbrush/TSHELL load check. They do not establish every app, every color
mode, a long soak or a post-install hash check for those two reports.
The 6404 emulation model explicitly remains uncertain.

The two-file overlays under experiments/TRIAL4 require fresh complete OEM
sources and owned support files. Read that folder's GUIDE.TXT. They do not
replace the normal package defaults, and are not complete installation disks.
