# HPXY startup performance experiment

Private opt-in experiment based on main `c40e380e13b6e7cc6201b1958c580fd287cf4374`.
Accepted driver binaries, package recipes, installer pins and consumer behavior
are unchanged. This directory does not qualify or publish a runtime.

## Candidate

`SOLID.PY` runs after the current XRBUILD overlay and changes only the inner
planar-to-Tandy eight-pixel converter in staged `EGA/TSOFT.ASM`.
Each plane byte must be 00h or FFh. The unsigned test after INC accepts exactly
those two values. Such a group contains eight identical pixels: convert one
RGBI nibble, duplicate it, and write the same four destination bytes with two
STOSWs. Every other group uses the original bit conversion body.

The checks modify only AL and flags before the mixed path, whose first
get_nibble resets AL. The existing outer save frame restores registers and
flags. Logical clipping, the 199/200 shadow-band boundary, cursor exclusion,
staging limits, group/bank wrapping and pan presentation remain unchanged.
There are no tables or new data allocations. Mixed groups pay for the tests;
representative native measurements are required before recommending adoption.

## Build

Use an explicit current-source view and the verified archived legacy inputs
from ../../tools/BUILDDEPS. All emulator use requires a coordinated slot and
the existing shared nonblocking byte lease. Supply a fresh output directory:

```
python experiments/SOLPERF/BUILD.PY --repo SOURCE-VIEW --out NEW-BUILD --dosbox DOSBOX-X --lease EXISTING-SHARED-LEASE
```

The wrapper uses the normal MASM 5.10/LINK4 and 8088 audits. RESULT.json labels
the output as a private candidate and records its overlay hash. Build success
is separate from native Windows correctness, timing and package acceptance.

## Initial host/build evidence

The complete source pipeline stages successfully. Removing the fast-path
insertion recreates the existing qualified HPXY staged source byte for byte
(SHA256 43e7e2c9a9404396fccd72cb9d04b4074fa260425425d675cc301696ac3673c3).
An exhaustive 256-value check of each plane's predicate admits only 00h/FFh;
all sixteen uniform plane combinations cover all sixteen RGBI colors.
This structural proof does not execute the candidate instructions.

The initial native build passes assembly/link and the existing 8088 audits.
HPXY.DRV is 61,936 bytes, SHA256
e3fa0eec6fdd176cf87f583d1c592ec9ad52908cd3e84603ef0402156ff55c08.
Gross NE allocation is 126,953 bytes, 70 above the released driver and 578
below the unchanged 127,531-byte project ceiling. The file grows by 80 bytes;
shadow and scratch allocations remain unchanged. These figures are not free
DOS RAM or physical-machine qualification.

## Matched native result

One fresh matched pair used the same patched 86Box 7.0 executable, Tandy 1000 HX,
8088 at 7,159,092 Hz, 640 KB (624 KB after RESERVE), Windows 3.0 real mode,
XT-IDE ramdisk timing, OS/app/probe bytes, resident helpers, logical 640x256
16-color desktop and normal Solitaire window rectangle 0,0,640,224.
The native marker launched both at GetTickCount 60033 and BIOS tick 1450.
Only HPXY.DRV differed among installed runtime/control inputs.

| Endpoint | Released | Candidate |
| --- | ---: | ---: |
| WinExec return | 37.788 s | 36.635 s |
| Visible/no-pending-invalidation observation | 37.898 s | 36.744 s |
| BIOS ticks to ready | 690 | 669 |

The ready reduction is 1.154 s, or 3.045%. Both complete 81,920-byte canonical
shadows are byte-identical, including all seven tableau columns. The top 200
rows (the card region) stayed unchanged for a further three guest seconds.
The physical viewport remains 320x200; the full logical capture is reconstructed
from the driver shadow. The ready observation is an upper bound, not a hook at
the last card-paint instruction. This is one controlled pair, not a confidence
interval or a physical-machine measurement. It must not be combined with the
older roughly40-second trials to calculate a speed ratio.

The pair uses private developer images and the normal RESERVE guard followed
by WIN/R. The released consumer file-identity CHECK intentionally rejects an
unqualified driver, so consumer installation/package acceptance is separate.
Normal helper programs and configuration were identical in both runs.

## Where startup time goes

The baseline has 217 random-interval stopped-PC samples during the native
startup interval. Loaded NE segments are identified by relocated-byte masks;
unresolved segment headers are checked against 24 instruction bytes at the
sampled offset. Counts estimate self-time, not call counts or inclusive costs.

| Location | Samples | Approximate share |
| --- | ---: | ---: |
| GDI | 66 | 30% |
| KERNEL | 38 | 18% |
| Driver DIB bitmap conversion | 33 | 15% |
| Driver presentation conversion | 27 | 12% |
| XT-IDE ROM (verified XUB signature) | 14 | 6% |
| Solitaire | 8 | 4% |
| Other driver raster code | 6 | 3% |
| Cursor | 2 | 1% |
| USER | 1 | below1% |
| Unresolved | 22 | 10% |

Nineteen of 27 presentation samples have an attributable BitBlt caller. Several
full-flush callers remain unresolved. No panning hotspot appeared; Pixel,
Output and text calls were not counted individually. ROM execution is not a
measurement of total disk wait. The 4-bit import/export loops in BMC_ETI and
BMC_ITE are useful next general driver targets. GDI and KERNEL costs require
further attribution before proposing a change to driver capabilities.

## Correctness and cost

Both actual-Windows regression boots returned normally to DOS. Each passed 41
frame comparisons (1,312,000 packed visible bytes), four controlled GDI interior
checks, and 144 additional brush/pixel assertions. The scenes cover requested
sixteen-color brushes, mixed first/last planes, fills, lines, text, the 199/200
shadow boundary, visible custom cursors, drawing beneath saved-under pixels,
small/reverse/high-origin pans, full fallback and forced recovery. All five
captured canonical shadows are also identical across the two builds.

The initial extra oracle incorrectly expected flat colors for two RGB brush
samples. The unchanged baseline uses EGA brush dithering there; the failed
receipt is preserved and expectations were corrected before candidate assessment.
The independent shadow-to-VRAM comparisons passed throughout. Transient live
FAT-copy warnings disappeared: both stopped images have matching FAT copies.
Both original source-image hashes are unchanged.

Five full logical 640x256 PatBlt calls per batch, with the 320x200 view presented:

| Workload | Released | Candidate | Change |
| --- | ---: | ---: | ---: |
| Requested green RGB brush (actually dithered) | 6.481 s | 6.317 s | -2.5% |
| Black/white checkerboard, first plane mixed | 6.481 s | 6.646 s | +2.5% |
| Black/dark-gray checkerboard, last plane mixed | 6.426 s | 7.196 s | +12.0% |

These are individual five-call batches at roughly 55 ms clock resolution. The
first workload is not a pure uniform-fill benchmark. The source checks explain
the late mixed-plane penalty: all four predicates execute before fallback.
Warm free Windows heap was 153,728 bytes for baseline and 153,664 for candidate;
each remained unchanged after its pan sequence. Largest free blocks were 149,152
and 149,120 bytes respectively. These are observed heap metrics, not a new
allocation contract or an exhausted-memory claim.

Keep this candidate experimental: the small Solitaire benefit comes with a
material worst-case mixed-pattern cost. Accepted runtime binaries and package
pins remain unchanged. Further work should reduce predicate/fallback cost or
accelerate the general DIB conversion paths before promotion.

## Reproduction and remaining scope

RESULT.JSN binds the exact build, probe sources, controls, timing fields, profile
counts, native oracle outcomes and source-image identities. MARK.C is the native
memory-marker probe; SCENE.C is the expanded Windows raster/cursor/pan probe.
Build them with the external Open Watcom 16-bit Windows compiler using -zW -0
-ms -od -we, its H and H/WIN headers, and WLINK system windows. No consumer
preparation depends on Python. Private OS/ROM images and native binaries are
not included here. ORACLE.PY checks an extracted SCENE output directory:

```
python experiments/SOLPERF/ORACLE.PY PRIVATE-SCENE-OUTPUT
```

The local workspace retains the private preparation/runners, raw traces, native
logs, final logical PNGs and lifecycle receipts outside the repository. See the
evidence_root in RESULT.JSN. Separate reviewer signoff, repeated-trial confidence,
consumer installer/package qualification and physical EX/HX/CF testing remain
open. No push, merge, publication or physical-media writes were performed.


## DIB-only follow-on (host preparation)

DIBBLD.PY applies DIB.PY after the normal HPXY overlay and does not apply the
older solid-group predicate. It unrolls the fixed four-source-byte import and
four-destination-byte export groups. Palette translation, every pixel operation,
partial-byte routines, segment-crossing dispatch, stack frames, presentation,
cursor and panning code remain unchanged. No data table or allocation is added.
The original AH and temp_bit_count postconditions are explicitly retained.

DIBHOST.JSN records the source-stream proof: the repeated bodies are identical
to the originals, and all text outside the two full-group routines is identical.
This establishes source structure only; assembly and native results are pending.
DIBSCN.C combines the prior scene with DIBTEST.C checks for palette permutations,
widths1/7/8/9/15/16/17/37, a high-offset64KB crossing, RLE4, guard bytes and
64-call GetDIBits/SetDIBits timing batches. It compiles with the same Open Watcom
8086 Windows flags. DIBORCL.PY adds11 DIB-case and native-assertion requirements
to the independent scene oracle.
