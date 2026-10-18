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
models its register-return values and pushed zero word with an explicit
synthetic launch context. It does not allocate or initialize a Windows task,
PSP, local heap, task stack, instance data, or DLLs. The input is read-only
and no executable is modified or emitted.

The ordinal mapping and register contract are based on Wine's Win16
[ordinal table](https://github.com/wine-mirror/wine/blob/master/dlls/krnl386.exe16/krnl386.exe16.spec)
and [task initialization code](https://github.com/wine-mirror/wine/blob/master/dlls/krnl386.exe16/task.c),
not an independently verified Windows 3.0 export table. This is a
bridge-dispatch milestone, not proof that the original application has
completed Windows startup.

`win16_host.py` binds `KERNEL` ordinal 91 plus the name imports `KERNEL!GetVersion`,
`KERNEL!MakeProcInstance`, and `USER!EnumWindows`. Every other import fails
closed. `api_fixture.py` is first-party 8086 guest code loaded through a
synthetic NE structure with name-import relocations. It calls these APIs,
checks the returned Windows 3.0 version word, and passes an `EnumWindows`
callback through a host-resolved procedure-instance token. The callback body
executes in the guest CPU model, reads the Pascal stack arguments, writes
through its bound instance `DS`, and returns with `RETF 6`. The HWND list comes
from the fixture host, not a Windows desktop. `MakeProcInstance` is modeled by
a token-to-callback mapping that applies the documented instance-segment
binding; it does not generate Windows thunk bytes or verify the SDK-required
module-definition `EXPORTS` entry for the callback.

The API signatures and Pascal callback contract follow Microsoft's original
[Windows 3.0 SDK Programmer's Reference, Volume 1](https://www.pcjs.org/documents/books/mspl13/win/w3sdkr1/)
(`GetVersion`, `MakeProcInstance`, `EnumWindows`, and the Windows calling
convention). The `FARPROC` result in `DX:AX` and segment-before-offset far
pointer argument layout follow Microsoft's period
[C 6.0 ABI reference](https://www.pcjs.org/documents/books/mspl13/c/cadvprg/).
These sources document the API and calling shapes; the fixture uses symbolic
`KERNEL`/`USER` import names but does not validate those names against original
Windows 3.0 export-table bytes. Its bridge behavior is not a Windows runtime.

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
register PUSH/POP, ADD/SUB/XOR/OR/CMP, INC/DEC r16, NOP, short JE/JMP, near
CALL/RET, far CALL/RETF, and supported 81h word-immediate groups /0, /5, and
/7. 16-bit ModRM effective addresses are supported for those word operations.

The only 80186 instruction forms implemented are:

* `PUSH imm16` (`68 iw`)
* `PUSH imm8` (`6A ib`), sign extended to 16 bits
* `IMUL r16, r/m16, imm8` (`6B /r ib`), with signed multiply and CF/OF

`INT FF` is a synthetic host trap used by tests. Import dispatch binds
`KERNEL` ordinal 91 and the three name imports documented above. The
first-party callback fixture covers the `EnumWindows` far Pascal callback
shape and instance `DS` binding; it does not implement general Win16 thunks or
the complete Win16 callback ABI. Unknown imports, instructions, and
unsupported group extensions fail closed.

## Checks

Run the deterministic synthetic checks from the repository root with:

```console
python -m unittest discover -s experiments/winmine-original-vm -p "test_*.py" -v
```

The tests compare registers, stack words, selected flags, NE fixups, and the
bounded entry trace against explicit expected values. The API and callback
fixture is first-party 8086 machine code; the suite contains no external guest
executable. Run the standalone API/callback fixture with:

```console
python experiments/winmine-original-vm/api_fixture.py
```
