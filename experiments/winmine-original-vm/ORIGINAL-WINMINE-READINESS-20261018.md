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
`KERNEL` ordinal 102 at `F001:0018`, with `AX=3500h`. The ordinal mapping is
supported by the period reverse-engineering list in
[*Undocumented Windows* (1992)](https://ftpmirror.your.org/pub/misc/bitsavers/pdf/microsoft/windows_3.1/Schulman_-_Undocumented_Windows_1992.pdf),
which lists `DOS3CALL (KERNEL.102)`, and is corroborated by Wine's current
[`krnl386.exe16.spec`](https://github.com/wine-mirror/wine/blob/master/dlls/krnl386.exe16/krnl386.exe16.spec).
This is not a direct export-table dump from the target Windows 3.0
`KERNEL.EXE`; the mapping is triangulated rather than binary-verified against
that exact system image.

Microsoft's Windows SDK 3.0/3.1 knowledge-base articles describe `DOS3Call`
as a register-based DOS interface with no stack parameters and a FAR PASCAL
call shape ([Q80783](https://jeffpar.github.io/kbarchive/kb/080/Q80783/),
[Q93343](https://jeffpar.github.io/kbarchive/kb/093/Q93343/)). The
[MS-DOS Version 4.0 Programmer's Reference](https://www.pcjs.org/documents/books/mspl13/msdos/dosref40/)
documents the DOS register contracts for
[get/set interrupt vector](https://www.pcjs.org/documents/books/mspl13/msdos/dosref40/)
and [get DOS version](https://www.pcjs.org/documents/books/mspl13/msdos/dosref40/).
Based on those sources, the host probe implements only these bounded forms:

- `AX=3500h` gets INT 00h and returns its synthetic handler in `ES:BX`.
- `AX=2500h` sets INT 00h from `DS:DX`; no result registers are changed.
- `AX=3000h` returns an explicitly supplied synthetic DOS version in
  `AX`, `BX`, and `CX`.

All three calls FAR-return without stack arguments. Other DOS functions,
interrupt numbers, or missing synthetic inputs fail closed. Tests exercise
the documented register inputs/results, stack return, vector state, and
fail-closed cases.

For the original-image trace, the synthetic INT 00h vector started at
`F000:0040`, was read using `AX=3500h`, and was changed to `1000:2A18` using
`AX=2500h`. A separately supplied synthetic DOS 3.30 value produced
`AX=1E03h`, `BX=0000h`, and `CX=0000h`. The guest then executed 64 more
instructions and stopped before `REPNE SCASB` at `1000:27FB` (`F2 AE`), with
`ES:DI=0000:0000` and `CX=8000h`. This is the recorded stop from the earlier
host-probe version, not an application failure result. That version had no
explicit PSP/environment block and its vector map was host-side state rather
than a real-mode IVT in guest memory.

The task context, INT 00h vector, and DOS version used here are all synthetic.
The prior trace did not launch Windows or establish a real Windows task, PSP,
heap, stack, instance data, DLL environment, or DOS process. Resource loading
and resolution of the original image's 99 ordinal imports also remain separate
requirements for original-image startup. The expanded trace is not full-app,
release, or hardware qualification.

## Follow-up synthetic launch slice

The host-only probe now accepts the explicit fixture
[`fixtures/winmine-synthetic-dos-context.json`](fixtures/winmine-synthetic-dos-context.json).
It declares PSP `3000h`, environment segment `3100h`, an empty environment,
program path `C:\FIXTURE\WINMINE.EXE`, an empty command tail, and INT 00h
`F000:0040`. These are synthetic values, not recovered DOS state. The context
installs only the PSP environment pointer and command-tail bytes, the declared
environment block, and declared IVT vectors. Reads of uninitialized bytes in
protected PSP, IVT, environment, or low DOS memory ranges fail closed. DOS3Call
vector get/set reads and updates the guest IVT bytes and checks them against
the declared fixture state. The instruction subset includes `REPNE SCASB`/
`SCASB` with tested byte flags, `CX`, match termination, and direction-flag
behavior.

The pinned original executable was not present in the current workspace or the
known supplied-media directory checked for this follow-up. The new context and
instruction behavior were validated with synthetic unit tests, but the pinned
original was not rerun; the earlier `1000:27FB` stop remains the latest
actual-original trace evidence. The partial fixture does not add a DOS process,
Windows task, heap, file handles, termination vectors, release, or hardware
qualification.

## Scope

This report is a host-only identity, NE inventory, and bounded instruction
trace through three explicitly modeled `DOS3Call` forms. It makes no claim
that the original application starts, displays a window, or supports gameplay.
No Windows media, ROM, executable, or private candidate is included; no
emulator or physical hardware was used for this audit.
