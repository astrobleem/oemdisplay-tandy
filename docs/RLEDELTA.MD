# Compact journal and RLE delta follow-up

Baseline: main `15f2c2910feb0e3745ba23d3af25f5344f1c1519`.

Compact PREP previously restored all files but retained a ROLLED_BACK journal
that refused the next installation. PREP now validates completed journals and
exact restored bytes, exclusively creates a numbered history file, flushes it,
then starts the next transaction. Existing evidence is retained. Active,
incomplete, corrupt and inconsistent states refuse before payload mutation.
The offline suite passes 27 grouped checks with the optional pinned helper
(25 without), including repeated cycles and interruptions during archive flush and after archival.
Fonts, controls, focus-only helper and Calculator exclusion are unchanged.

RLE88 validated current X + dx but saved raw dx across a vertical delta.
It now saves that validated absolute X in the existing stack local. Same-row
delta behavior, bounds and ABI are unchanged.

## Actual assembly regression

The existing MODETEST/MODECHK infrastructure now has phase 64, cases 150-157:
RLE4/RLE8 x SetDIBitsToDevice/SetDIBits-memory x dy=1/3. Every case emits two
pixels, reaching X2, then delta dx2, followed by three pixels at X4..6. The
BI_RGB comparison is independently prepared. Complete VRAM and unused bank
bytes are checked, along with API returns, stage receipts and input integrity.

Both before/fixed drivers were assembled with the existing pinned external
toolchain and passed the emitted 8086 and RLE ABI audits. Under official
installed DOSBox-X 2025.10.07, tandy / 8086_prefetch, WIN /R, EMS/XMS/UMB off,
and accepted RESERVE protection:

| Candidate | Cases | Pixels | Result |
| --- | --- | --- | --- |
| Main RLE88 before fix | 8 | 512,000 | all 8 fail, exactly 4 misplaced pixels each |
| Fixed RLE88 | 8 | 512,000 | all pass; zero pixel/padding mismatch |

All API/immutability checks passed even before the fix. The reference-only
host suite therefore cannot substitute for this regression. Both owned
guest processes exited normally within 120-second bounds, released the
shared lease and restored all private Windows files byte-for-byte. Driver,
listing, probe, frame and source hashes are in [RLE-DELTA.JSON](RLE-DELTA.JSON).

[RLEDELTA.ZIP](RLEDELTA.ZIP) contains only generated solid-color test frames
and guest test logs, with no Windows, DOS, DDK, ROM, compiler or emulator
payload. To independently check the actual captured assembly output:

```
python -m zipfile -e docs/RLEDELTA.ZIP ../RLEFRAMES
python src/tandysw/MODECHK.PY ../RLEFRAMES/BEFORE --profile 320x200x16 --phases 64
python src/tandysw/MODECHK.PY ../RLEFRAMES/AFTER --profile 320x200x16 --phases 64
```

The first command-line check must exit 1 with eight four-pixel failures; the
second must exit 0. Rebuild MODETEST with MODEBLD.BAT in the documented
pinned external view; select phases=64 and width=320,height=200,colors=16,
bios=9,palette=0 in C:\MODETEST.INI. Use an isolated owned-media real-mode
guest and the existing guarded reservation/lease/watchdog procedure.

The follow-up tests the default 320x200x16 development profile. Historical
run41 remains evidence for its older HPXY binary; its X0 delta fixture did
not cover this defect. No other profile, physical machine or performance
qualification is claimed. Accepted release binaries and packages are unchanged.
