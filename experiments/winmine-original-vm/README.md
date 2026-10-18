# Original-image VM probe

This directory contains a deliberately small, pure-host Python instruction
interpreter and a bounded NE loading probe. The committed tests use synthetic
structures only. No Microsoft source or executable is included here.

`ne_loader.py` reuses the repository's public `tools/W31CHECK/w31check.py`
parser. It maps each NE segment into a private 64 KiB selector window and
resolves the internal, ordinal-import, and name-import fixups covered by this
probe to synthetic segment selectors. Unsupported source or target fixups fail
closed. The model does not reproduce Windows NE allocation, shared libraries,
callbacks, or segmented-pointer lifetime rules.

`probe_original.py` can read a caller-supplied NE executable after verifying a
required SHA-256. It executes at most the first three instructions at the NE
entrypoint, intercepts the first relocated far import, returns a caller-chosen
AX value, and compares resulting CPU, stack, and defined-flags state with a
separately hand-calculated trace. The intercepted call has no Windows API
semantics. The command reads the input, emits a JSON report, and creates no
modified executable.

From the repository root, run a pinned local image like this:

```console
python experiments/winmine-original-vm/probe_original.py <read-only-ne-image> --sha256 <expected-sha256>
```

This probe does not run the application, Windows, DOS, a ROM, or an emulator.
It is not an app converter, Windows compatibility layer, or Minesweeper
runtime, and establishes no full-app, release, or hardware qualification.

## CPU subset

The model has 16-bit general and segment registers, IP and arithmetic,
direction, interrupt, and trap flags, plus flat byte-addressed memory. The
implemented 8086 subset is immediate/register and register/memory word MOV,
register PUSH/POP, ADD/SUB/XOR/CMP, INC/DEC, NOP, short/near JMP, near
CALL/RET, far CALL, and supported 81h word-immediate groups /0, /5, and /7.
16-bit ModRM effective addresses are supported for those word operations.

The only 80186 instruction forms implemented are:

* `PUSH imm16` (`68 iw`)
* `PUSH imm8` (`6A ib`), sign extended to 16 bits
* `IMUL r16, r/m16, imm8` (`6B /r ib`), with signed multiply and CF/OF

`INT FF` is a synthetic host trap used by tests. The far-import interception
point is generic; it is not a Windows import table, callback ABI, or complete
interrupt support. Unknown instructions and unsupported group extensions raise
`UnsupportedOpcode`.

## Checks

Run the deterministic synthetic checks with:

```console
python -m unittest -v
```

The tests compare registers, stack words, selected flags, NE fixups, and the
bounded entry trace against explicit expected values. They contain no external
guest code.

