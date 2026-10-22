# RLE run41 qualification record

This is a source-only summary of the private run41 evidence. The original run
files remain in the task workspace; the integration contains no `DISK.IMG`,
guest/system binaries, or full guest artifact set.

- Candidate `HPXY.DRV`: 60,400 bytes, SHA-256
  `cb12b6b8ecb657b44b2b5122895dcaabca84fbc15c9b9f1a542e14d9f935629d`.
- Accepted preboot driver: 56,704 bytes, SHA-256
  `9db7bbd8b1e9c30aa0cd766a89ff35abf42697aa3d342c7d7906b3d98f767275`.
- Run41 MODECHK exit 0, 15/15 cases, 960,000 full-frame pixels and 491,520
  physical bytes compared. Duration 180.05 seconds.
- Case146: compressed and raw `SetDIBits` returned 11 scans; inputs, metadata,
  fixtures and guards remained unchanged; all 64,000 frame pixels matched the
  expected oracle. The post-call `MD146.BIN` plus full-frame checker are the
  pixel evidence. The screenshot is pre-call and the entry observer was
  unarmed, so callback-entry evidence is inconclusive.
- The old `386/814` crop number used unadjusted coordinates. Under active pan
  `(8,4)`, the adjusted crop is 766/814 changed with all 16 indices; the
  complete-frame comparison remains authoritative.

Run41 used the emulator's original 8088 core, Tandy 1000 HX surrogate, Windows
3.0 real mode, 640 KB, logical 640x256x16, and a 320x200 visible view. This is
not physical-hardware or other-profile qualification and establishes no
performance improvement. The current-main build closure separately reproduced
the exact run41 candidate; that compiler run did not launch a Windows guest.
