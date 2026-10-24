# BI_RLE4 / BI_RLE8 integration and current-main build closure

This source overlay is now checked against canonical `main` commit
`4d9dc402c30fd398f10742b4eed3d78d420cea59` (tree
`523075e94d83a53b2c980c59a961e9949d4e23f4`). The original staging was based on
`fcfb748`; its 25-file patch remains preserved as historical evidence. The
complete current-main patch includes 26 paths, adding the missing first-party
`src/tandysw/COMPACT.PY` build helper.

## Candidate and accepted package

- Reproduced run41 candidate: 60,400 bytes, SHA-256
  `cb12b6b8ecb657b44b2b5122895dcaabca84fbc15c9b9f1a542e14d9f935629d`.
- Accepted package baseline: `tools/XR1PACK/PAYLOAD/HPXY.DRV`, 56,704 bytes,
  SHA-256 `9db7bbd8b1e9c30aa0cd766a89ff35abf42697aa3d342c7d7906b3d98f767275`.
  It remains unchanged. Package and companion manifests link it to source
  snapshot `3521f93a3647c5937e4f8a77c6c1d371473e06c5`, but no deterministic
  source-to-binary build receipt for that accepted payload is available.

## Build closure and exact reproduction

A clean isolated compiler build used canonical main `4d9dc402...` plus the
complete integration overlay and reproduced the run41 candidate byte-for-byte.
The first-party driver closure contains 31 inputs: 17 already match current
main, 3 differ and are supplied by the overlay (`BUILD88.PY`, `PORTDIB.PY`,
`SDIB88.ASM`), and 11 are absent from main and supplied as private
first-party build overlays. The 11 include the XY/RoundRect/HPAN build scripts
and sources, `RLE88.ASM`, and `COMPACT.PY`. All 31 applied-tree input contents
match the exact run41 build-root inputs after repository line-ending
normalization. The per-file comparison and build result are in
`RLE-CURRENT-MAIN-CLOSURE-4D9DC.json`.

The external Microsoft DDK, assembler/linker, resource tools, libraries, and
includes are recorded only as identities and SHA-256 hashes in
`RLE-EXTERNAL-DEPENDENCIES-4D9DC.json`; their binaries and SDK files are not
included in this source patch. The build linked 28 explicit objects, passed
the 8086 opcode audit with 16,563 emitted rows and zero unsupported opcodes,
and passed the RLE helper-return/stack audit. The output was byte-identical to
the run41 candidate. This is build reproduction; it is not a new Windows guest
run.

## Existing guest evidence and limits

The saved run41 Win3.0 real-mode run reports MODECHK 15/15 and compares 960,000
full-frame pixels for the documented 640x256 logical / 320x200 view profile.
It was reused, not rerun during this closure build. Case146's screenshot is
pre-call; the post-call `MD146.BIN` and full-frame oracle provide the pixel
evidence. The entry observer was unarmed, so callback-entry proof is
inconclusive. An older `386/814` crop count used pre-pan coordinates; with the
active pan `(8,4)`, the adjusted crop count is `766/814` with all 16 indices.
The full-frame comparison is authoritative.

This evidence does not qualify physical Tandy hardware, other display profiles,
or performance improvement. The RLE implementation uses bounded stream
input and one scan-row scratch buffer; no whole-image allocation is made.
The DIB entrypoint limit remains that compressed inputs require nonzero
`biSizeImage`; malformed and unsupported format combinations fail closed.
