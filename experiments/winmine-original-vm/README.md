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
required SHA-256. It runs the bounded entry prefix through the first imported
call, binds only `KERNEL` ordinal 91 (`InitTask`), and executes the guest's
`OR AX,AX` / `JE` continuation after the host service returns. The service
models a narrow register-return contract with an explicit synthetic launch
context. It does not allocate or initialize a Windows task, PSP, local heap,
stack, instance data, or DLLs. The input is read-only and no executable is
modified or emitted.

The ordinal mapping and register contract are based on Wine's Win16
[ordinal table](https://github.com/wine-mirror/wine/blob/master/dlls/krnl386.exe16/krnl386.exe16.spec)
and [task initialization code](https://github.com/wine-mirror/wine/blob/master/dlls/krnl386.exe16/task.c),
not an independently verified Windows 3.0 export table. This is a
bridge-dispatch milestone, not proof that the original application has
completed Windows startup.

`win16_host.py` rejects every other import. Its callback dispatcher makes a
bounded far call into guest code and requires a matching `RETF` to the saved
host frame. The callback unit test uses only a four-byte first-party fixture;
it is not a callback from WinMine or Windows code.

From the repository root, run a pinned local image like this:

```console
python experiments/winmine-original-vm/probe_original.py <read-only-ne-image> --sha256 <expected-sha256>
```

This probe does not launch Windows or DOS, load a ROM, or use an emulator. It
is not an app converter or Windows compatibility layer, and establishes no
full-app, release, or hardware qualification.

## CPU subset

The model has 16-bit general and segment registers, IP and arithmetic,
direction, interrupt, and trap flags, plus flat byte-addressed memory. The
implemented 8086 subset is immediate/register and register/memory word MOV,
register PUSH/POP, ADD/SUB/XOR/OR/CMP, INC/DEC, NOP, short JE/JMP, near
CALL/RET, far CALL/RETF, and supported 81h word-immediate groups /0, /5, and
/7. 16-bit ModRM effective addresses are supported for those word operations.

The only 80186 instruction forms implemented are:

* `PUSH imm16` (`68 iw`)
* `PUSH imm8` (`6A ib`), sign extended to 16 bits
* `IMUL r16, r/m16, imm8` (`6B /r ib`), with signed multiply and CF/OF

`INT FF` is a synthetic host trap used by tests. Import dispatch binds only
`KERNEL` ordinal 91. The callback test covers a parameterless far procedure
and `RETF`; it does not implement the full Win16 callback ABI. Unknown
imports, instructions, and unsupported group extensions fail closed.

## Checks

Run the deterministic synthetic checks with:

```console
python -m unittest -v
```

The tests compare registers, stack words, selected flags, NE fixups, and the
bounded entry trace against explicit expected values. They contain no external
guest code.

