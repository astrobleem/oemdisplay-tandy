# PR155 on current XR1: opt-in batching candidate

Historical candidate `ff5d5e38`; its abandoned-BEGIN gap is superseded by the
local synchronous follow-up in [RRSYNC.MD](RRSYNC.MD). The measurements below
remain the exact earlier experiment, not the current implementation.

Base: main `5ada3e8092b761aab9099c6d96a7b893ed3a6902`. Original PR155 head:
`364662202d625d07ef0e8c02934ed887d84a33ea`. No release package, accepted
binary, source pin or default is replaced. Physical hardware is untested.

## Remaining delta and integration

PR151 was merged as `fc7b09bd`. Main's `experiments/XYRRECT/XRPATCH.PY`
still calls its local `rr.patch_candidate`; that patch skips copies for
markers and bounds polylines, but presents each fill row immediately.
Neither main's `src/rrect/RRPATCH.PY` nor the XR copy had `patch_batch`.
Thus PR155's batching remains useful and is not already enabled by XR1.

The original experiment, per-call checker and three failure mutants are
retained with their original historical evidence in [RRBATCH.MD](RRBATCH.MD).
The current integration adds `XRBUILD.PY --batch`. It applies only batching
after XR1's existing PR151 and dual-band alias checks. The default XR build
is unchanged. Current main's RLE decoder and compact resources are retained.

`XRBATCH.PY` adapts the staged source rather than rebasing binary patches:

- XR1 aliases `FlushRetainRows` to `FlushRows`; use that actual procedure end.
- Close pending rows before pan/Control, Disable and DIBScreenBlt, in addition
  to the original drawing entries. Control/Disable use a far trampoline
  because they live outside the near drawing-code segment.
- Settle memory Output and scanlines rejected by the conservative gate before
  rendering. Recognized screen markers bypass that fallback: BEGIN deliberately
  cleared `dirty`, which must not immediately close the newly opened batch.
- Nested BEGIN first presents the previous range. END without BEGIN is empty.
  Rows outside a batch retain immediate presentation. Cursor interrupt code is
  unchanged; foreground presentation uses XR1's existing cursor-aware flush.

An abandoned BEGIN with no later foreground driver call still leaves its rows
pending. The next drawing call, Control or Disable settles them. This is the
original marker-protocol limitation, not a claim of timer-driven recovery;
batching remains an explicit opt-in. No interrupt-time shadow copying is added.

## Fresh assembled-driver results

Baseline: 60,400 bytes, SHA-256
`c418dff91b27940437d03d0143b99d4d0b9185890bb7f6ff76a89d0fae837d30`.
Batch: 60,624 bytes, SHA-256
`fcce3ea7c374ea911bbaabdae6fb314b3dfa83bbed07bf7b43cd4b009aeec475`.
Measured cost: **+197 allocated code bytes, +6 data bytes, +224 file bytes**.
Both link 28 objects, pass the 8086 opcode and REP audits, and pass the RLE
helper-return/stack audit. Shadows remain exactly 64,000 + 17,920 bytes.

The matching Windows 3.0 `WIN /R` runs use DOSBox-X 2025.10.07, Tandy,
8086_prefetch, fixed 3,000 cycles, 640K conventional memory with RESERVE,
and XMS/EMS/UMB disabled. Each run has a 180-second watchdog and the shared
nonblocking emulator lease. Only owned children are stopped. These timings
are emulator measurements, not a calibrated physical 7.16MHz 8088 claim.

| Viewport / presentation | 20 keys under arrow, baseline | Batch | Difference |
| --- | ---: | ---: | ---: |
| (0,0), software | 4,064 ms | 1,538 ms | -2,526 ms (-62.2%) |
| (8,56), existing hardware-pan mode | 4,064 ms | 1,538 ms | -2,526 ms (-62.2%) |
| (320,56), software | 4,010 ms | 1,538 ms | -2,472 ms (-61.6%) |

Without cursor overlap, the 20-key RoundRect stage is 1,154 ms in both
drivers in all three comparisons. Calculator's three repaint samples stay
within 2,087-2,143 ms. Reversi stays within 1,098-1,154 ms and Paintbrush
within 2,307-2,362 ms. Differences of one roughly 55ms timer tick do not
establish a general application speedup. The older 86Box hourglass/37% claims
belong to the historical report and are not substituted for these results.

All **111 frame pairs** match byte-for-byte over all 32,768 VRAM bytes:
45 final-stage frames, 42 single-shape frames and 24 marker-settlement frames.
The eight direct ordinal-8 cases cover normal END, nested BEGIN, interleaved
Pixel write, memory Output, another Output style, Control/pan, rejected bounded
fill and Pixel read. At Y=56 their rows 200/201 enter the second shadow band.
Raw VRAM reads prove all eight baseline cases present before settlement and
all eight batch cases remain held. An initially disabled integration would
pass pixel equality but fails this assertion; the tested candidate passes it.
An independent full-viewport oracle checks 3,072,000 marker-case pixels,
including hardware bank rotation, the extra Pixel and rejected-fill row.

Fresh RLE regression runs at 25,000 cycles pass 9/9 cases and 576,000 full-frame
oracle pixels **per driver** at pan (8,4), including RLE4/8 screen and memory
imports, truncated input, cross-segment input, invalid format pairs and early
EOB. The retained RLE probe's C body is identical to current main; only its
leading documentation comment differs. Host checks pass: RRTEST 28 tests,
XR1 TESTPREP 24 and TESTPUB 9. The historical three broken batches are still
rejected by the retained per-call evidence tests.

Receipts, raw log hashes, all frame hashes, comparisons, independent oracle
results and exact build audits are in [current/CURRENT.JSN](rrbatch/current/CURRENT.JSN).
Private guest files, raw dumps, driver binaries and toolchains remain outside
the repository. Every completed runtime child stopped and released its lease.

## Reproduction

Use a fresh pinned external build view containing current `src/tandysw` and
`experiments` sources plus the verified BUILDDEPS inputs. Do not reuse an old
TR5 source view. Supply owned Windows files; no install or CF operation is used.

```text
python experiments/XYRRECT/XRBUILD.PY --repo <view> --out <fresh-base> --dosbox <dosbox-x> --lease <shared-lock>
python experiments/XYRRECT/XRBUILD.PY --repo <view> --out <fresh-batch> --dosbox <dosbox-x> --lease <shared-lock> --batch
python src/rrect/RRAPP.PY --repo <view> --out <fresh-probe> --dosbox <dosbox-x> --lease <shared-lock>
python src/rrect/RRXRUN.PY --windows <owned-Windows-directory> --reserve <RESERVE.COM> --driver <base/HPXY.DRV> --probe <probe/RRBENCH.EXE> --out <fresh-run-base> --dosbox <dosbox-x> --lease <shared-lock> --pan x
python src/rrect/RRXRUN.PY --windows <owned-Windows-directory> --reserve <RESERVE.COM> --driver <batch/HPXY.DRV> --probe <probe/RRBENCH.EXE> --out <fresh-run-batch> --dosbox <dosbox-x> --lease <shared-lock> --pan x --expect-held
python src/rrect/RRCMP.PY <fresh-run-base> <fresh-run-batch> --json <comparison.json>
```

Repeat with `--pan y --hardware` on both runs, then `--pan z` without hardware.
RRXRUN is Windows-host-only. RRAPP retains POSIX locking support; that path was
not rerun in this Windows qualification. Accepted releases remain unchanged.
