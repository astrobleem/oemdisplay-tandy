# RLE integration build and test record

All source tests use the staged `src/tandysw` files. The current-main compiler
build was run in the isolated build root; no Windows guest was launched during
this closure step.

- `python -B src/tandysw/RLETEST.PY`: PASS, 13 tests, including RLE4 nibble
  ordering and odd absolute padding, RLE8 encoded/absolute/padding/delta and
  early EOB, clipping, scan bands, malformed/truncated bounds, cross-64K reads,
  buffer immutability, palette translation, and compression/depth rejection.
- `python -B -m unittest discover -s src/tandysw -p test_rle_abi.py -v`: PASS,
  6 ABI/opcode regressions covering near-call/RETN stack balance, far cleanup,
  and byte-sized delta skip handling.
- `python -B src/tandysw/MODECHK.PY --selftest`: PASS.
- `python -B RLEABITEST.PY <run41 RLE88.LST> --source RLE88.ASM`: PASS. The
  listing has four near calls, C3/RETN on both helper outcomes, RLEInit and
  RLENextRow Pascal cleanup of 24/8 bytes, and the byte compare at ES:DI+27.
- Saved run41 guest output recheck: PASS, 15/15 cases and 960,000 pixels. This
  reused existing artifacts; it is not a new emulator qualification.
- Current-main isolated native build: PASS, `HPXY.DRV` 60,400 bytes with SHA-256
  `cb12b6b8ecb657b44b2b5122895dcaabca84fbc15c9b9f1a542e14d9f935629d`, exact
  byte match to run41, link PASS, 16,563 8086 instruction rows audited and
  zero unsupported opcodes. Runtime was not run by this build.

## Nonzero-X delta correction

The historical candidate above predates the nonzero-X vertical-delta fix.
See [follow-up evidence](RLEDELTA.MD) for the new source, actual assembly before/after tests,
and distinct default-profile scope. The old candidate hash is historical.
