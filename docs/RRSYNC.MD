# PR155: synchronous XR1 Output

This follow-up supersedes `ff5d5e38`'s deferred rows. Every screen
Output presents before returning. BEGIN/END are still no-op drawing markers;
no row range is retained, no later call is needed, and no timer is involved.
Accepted release packages, installations and the previous candidate are preserved.

## Implementation

`experiments/XYRRECT/XRBATCH.PY` now adds X bounds to the existing validated
scanline/polyline gate and synchronously calls `FlushRetainColumns`, rounded
outwards to eight-pixel groups. Dual-band alias checks and conservative full
refresh fallbacks stay intact. Rendering arguments, order and ROPs are unchanged.

XR1 had replaced `cursor_begin_retain` with an unused stub. The follow-up
restores the existing `CURKEEP.cursor_helpers(160)` implementation and passes
the actual clipped viewport rows and physical byte columns. Its foreground
lease retains a disjoint cursor; overlap uses the original hide/copy/show path.
Existing interrupt-time motion defers while that short-lived lease is held.
No interrupt-time GDI call, shadow copy, new ISR or cooperative timer is added.
Hardware pan staging still skips presentation/cursor ownership, as before.

The first trial exposed stale saved-background pixels because the XY stub
did not hide before end_retain refreshed. Restoring the existing helper fixed
those per-call failures. Only the corrected bytes below are the candidate.

## Exact candidate and measurements

| Driver | File bytes | SHA-256 |
| --- | ---: | --- |
| Current-main baseline | 60,400 | `c418dff91b27940437d03d0143b99d4d0b9185890bb7f6ff76a89d0fae837d30` |
| Previous deferred candidate | 60,624 | `fcce3ea7c374ea911bbaabdae6fb314b3dfa83bbed07bf7b43cd4b009aeec475` |
| Synchronous candidate | 60,800 | `ae2d06f69ff68e64f099c3e0af79028e40e7dca89bd442de23eb18d36be4dca1` |

Cost over baseline: **+382 allocated code bytes, zero data bytes, +400 file
bytes**. Shadows remain 64,000 + 17,920 bytes. All 28 linked objects pass the
8086 opcode, REP-prefix, closed-link and RLE helper-return/stack audits.

Matched Windows 3.0 WIN /R runs use the existing DOSBox-X Tandy fixture,
8086_prefetch, fixed 3,000 cycles, normal conventional memory and RESERVE,
with XMS/EMS/UMB disabled. Every run takes the shared nonblocking emulator
lease and has an owned-child watchdog. These are emulator workload timings.

| Viewport / presentation | Cursor keys: baseline / previous / new | Keys without overlap: baseline / new |
| --- | ---: | ---: |
| (0,0), software | 4,064 / 1,538 / **549 ms** | 1,154 / **385 ms** |
| (8,56), hardware | 4,064 / 1,538 / **604 ms** | 1,154 / **330 ms** |
| (320,56), software | 4,010 / 1,538 / **549 ms** | 1,153 / **384 ms** |

Calculator repaint median is **1,099 ms** in all three new runs, against
2,142 ms baseline and 2,087-2,142 ms in the previous candidate. Each run has
three samples; the new samples are 1,099 / 1,043 / 1,099 ms. Timer resolution
is about 55ms. Cursor-overlap improvement is 85.1-86.5% versus baseline and
60.7-64.3% versus the previous candidate; Calculator improves about 48.7%.

## Visibility and regression evidence

Probe v6 sends BEGIN and two fill rows, omits END, and reads real B800 VRAM
immediately after Output returns. It then busy-waits nine BIOS IRQ clock ticks
and reads again. There is no draw, Control, Disable, GDI/DOS call or message
dispatch between those two reads. Baseline and new driver read visible=1
both times at all three viewports. The old candidate reads 0 both times.
The ninth marker capture and the marker-stage final frame catch that old gap;
all its other captures match. The new implementation's synchronous write before
return removes the dependency on any future call, not just on a finite wait.

All **114 main frame pairs** match byte-for-byte, including 14 single shapes
and nine marker/interleaving cases per viewport. The independent marker oracle
checks 3,456,000 pixels across both sides. The Y=56 cases write rows 200/201
in the second shadow allocation. Probe v7 additionally performs one supported
8-pixel/4-row diagonal pan and return with the cursor visible, exercising the
existing hardware stage and bank wrap. All 16 per-call captures and the final
frame match at each viewport: **51 additional frame pairs**, for 165 total.
The previous candidate also matches all 51 pan frames.

Fresh RLE phases 32 and 64 pass for all three drivers: **17 cases and
1,088,000 independent oracle pixels per driver**, including the merged
nonzero-X vertical-delta fixes at both depths/import paths. Phase 32 uses
pan (8,4); phase 64 uses the same existing oracle with a 640x256 home-view
profile. Existing first-party probe/oracle code is reused. RRTEST passes
32 host tests, including malformed idle receipts and missing pan captures.

Receipts, exact hashes, timings, negative controls and build audits are in
[rrsync/RESULT.JSN](rrsync/RESULT.JSN). Raw captures and owned guests remain
in the local task's native directory. PROBE6.C/PROBE7.C preserve the exact
compiled harness snapshots; neither is a new diagnostic project.

## Local candidate and reproduction

Build with a fresh current-source BUILDDEPS view:

```text
python experiments/XYRRECT/XRBUILD.PY --repo <view> --out <fresh> --dosbox <dosbox-x> --lease <shared-lock> --sync-output
```

`--batch` remains an alias for that current XR1 option. The separate TR5
RRBUILD deferred variants remain historical negative controls only.

The earlier OEM packet remains the recorded graphics reference. The current
public kit below includes the supplied CGA grabber and completes native
preparation, Windows Setup and a guarded cold start on the DOS computer.

## Public installable kit

For installation use the [current DOS guide](RELEASES/XRSYNC.MD). The packet
includes the driver, supplied CGA grabber, original fonts/artwork, RESERVE,
XYCTL and native XSETUP. Run `XRSYNC C:\WINDOWS` on the DOS computer; it
prepares `C:\XR155`, reserves video memory and starts Windows Setup. No
separate support-file collection or host preparation is required.

Developer `tools/XRSYNC/PUBLISH.PY --out <new-release> --commit <full-source-sha>`
creates and re-verifies deterministic XRSYNC.EXE, XRSYNC.ZIP, README.TXT,
RELEASE.JSON and SHA256SUMS. It checks source/runtime identities and the exact
native-qualified packet before creating a release directory. No rendering
executable is changed by the native installer correction.

[Native installation and cold-start receipt](QUAL/DOSINST/XRSYNC.JSN) binds
packet hashes, actual Setup selections, installed identities and the existing
17-frame probe. [Recovery qualification](QUAL/DOSINST/XSPACE.JSN) records
nearly-full-disk refusal, interrupted helper cleanup and retry. The earlier
[SETUP.JSN](rrsync/SETUP.JSN) remains the historical reference for the original
host-prepared installation. No physical hardware or CF was used.
