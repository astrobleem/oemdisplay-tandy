# Pinned original WINMINE readiness audit

## Input identity and method

The private original input is 27,776 bytes with SHA-256
`633c1328922b4092351e0019b1ba1c6d56c0f0fea83824cc8b7e2e731b15e80b`. Its path
was recovered from the retained private input pin; the local candidate
manifest corroborates the size and hash. The path and executable are not
included here. The on-disk size and hash matched before and after this audit.

The read-only identity pass reported byte-passthrough equality and wrote no
output. The bounded host probe then loaded the NE segments, modeled the first
`KERNEL` ordinal 91 (`InitTask`) call with an explicit synthetic register and
stack context, and executed the two-instruction `OR AX,AX` / `JE` continuation.
It did not run Windows, allocate a real Windows task, or execute the
application. The MNSN1 and MNSN2 host-probe records elsewhere in this tree are
for converted demo images, not this pinned original.

## Original NE inventory

- Target OS: Windows; NE expected-version field: 3.10.
- Entry: segment 1 offset `2563h`; initial stack: segment 2 offset `0000h`.
- Automatic data segment: 2; heap: 4,096 bytes; stack: 8,192 bytes.
- Two file-backed segments: segment 1 is 11,216 bytes at file offset `0620h`
  with 107 relocation records and 204 chained sites; segment 2 is 2,364 bytes
  at file offset `3560h` with no relocations.
- Sixteen resources and five imported modules: `KERNEL`, `GDI`, `USER`,
  `SOUND`, and `SHELL`.
- Ninety-nine imported ordinal records: 25 `KERNEL`, 15 `GDI`, 52 `USER`, six
  `SOUND`, and one `SHELL` (`SHELL` ordinal 22). The import-name table has no
  imported API names.

The native C fixture is intentionally much narrower: it accepts its own
two-segment, two-module `W16TEST.NE`, resolves named `KERNEL!GetVersion` and
`USER!EnumWindows`, and applies two imported far-pointer fixups plus one
internal callback-segment fixup. It does not load this original image, its
resources, or its ordinal imports. The fixture’s successful API calls do not
demonstrate original-application startup.

## Bounded entry trace and next API dependency

The original host probe reached runtime selector:offset `1000:2563`. Its first
far call is at segment 1 offset `2566h` (file offset `2B86h`), with source
bytes `9A FF FF 00 00` relocated to `KERNEL` ordinal 91. The probe supplied a
synthetic `InitTask` result, then decoded `0B C0` (`OR AX,AX`) and `74 5B`
(`JE`), taking the success fall-through to `1000:256F`. The synthetic return is
not a Windows task initialization result. At `1000:256F` (segment 1 offset
`256Fh`, file offset `2B8Fh`), the next bytes are:

```text
8C 06 22 01    MOV WORD PTR [0122h], ES
```

The bounded host CPU now supports this `MOV r/m16,Sreg` family, including the
memory store used here. Its memory-store path checks the 20-bit physical
address against the allocated host memory, writes low byte then high byte,
preserves flags, and fails closed for unsupported segment fields or out-of-
bounds destinations. Focused tests cover direct and BP-based operands,
register destinations, 20-bit wrap, and bounds rejection.

After the synthetic `InitTask` return, the continuation reaches `1000:2573`
(`ADD CX,0100h`), then `1000:2577` (`JB +51h`), which is not taken under the
synthetic register values. It stores the synthetic startup registers, loads
`AX=3500h`, tests a word through a CS override at `1000:2615`, and falls through
the following `JZ`. At `1000:261E`, the guest makes a far call relocated to
`KERNEL` ordinal 102 at `F001:0018`. The bounded trace stops at this next import
without invoking it. `AX=3500h` at the boundary is recorded as machine state,
not as evidence that a DOS service ran.

Wine's current [`krnl386.exe16.spec`](https://github.com/wine-mirror/wine/blob/master/dlls/krnl386.exe16/krnl386.exe16.spec)
labels `KERNEL` ordinal 102 `DOS3Call`; that implementation table is a
cross-reference, not an independently verified export table for the target
system. No ordinal 102 service was bound or executed. The next blocker is to
verify that ordinal's target export and register contract before deciding
whether a narrow host model is appropriate. The trace remains host-only: the
`InitTask` return values and task context are synthetic. Real task/PSP, stack,
heap and instance setup, resource loading, and resolution of the 99 ordinal
imports remain separate requirements for original-image startup.

The bounded continuation executed 15 guest instructions after the synthetic
entry slice. Its stop record preserves the call site, relocated import target,
registers, and the 256-instruction ceiling. It does not continue through the
import stub or perform any DOS operation.

## Scope

This report is a host-only identity, NE inventory, and bounded instruction
trace to the next imported API. It makes no claim that the original application
starts, displays a window, or supports gameplay. No Windows media, ROM,
executable, or private candidate is included; no emulator or physical hardware
was used for this audit.
