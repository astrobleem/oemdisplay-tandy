# Native Win16 API fixture

This first-party MSC6 fixture checks the real Win16 `GetVersion` and
`EnumWindows` APIs. Its exported `BOOL FAR PASCAL` callback is passed through
`MakeProcInstance`, then invoked by Windows during enumeration. The log records
the version value, callback HWND/LPARAM pairs, full-enumeration return, and the
early-stop return after a callback returns `FALSE`. After closing the log, the
one-shot fixture requests Windows exit so the guest can return to DOS.

`BUILD.BAT` builds the private `W16APIN.EXE` with Microsoft C 6.0 and LINK4,
with the toolchain mounted as `C:` and this directory mounted as `S:`. A
machine-specific `BUILD.CNF` can supply those mounts in DOSBox-X; it is not
included because its host paths are local. The runtime fixture writes
`C:\W16API.LOG` on the guest. Do not commit or publish the executable or guest
image.

The Windows 3.0/8088 guest run is a compatibility check for this API path; it
does not qualify an OEM display driver or Minesweeper runtime. Record emulator,
machine profile, guest version, tested source commit, and log when reporting a
run. Emulator results must not be described as physical-hardware qualification.

## Bounded 8088 bytecode path

The fixture includes a small first-party 8088 interpreter for one fixed
bytecode program and the `EnumWindows` callback program. It implements the
8086/8088 `POP r16` and `MOV r16, imm16` forms, register `CMP /7`, short
`JZ`/`JNZ`, `INT FF` for the single `GetVersion` import, and `HLT`. It uses an
eight-word virtual stack and a 64-instruction limit; unknown opcodes, imports,
branches, and invalid stack operations fail closed. The `INT FF` bridge calls
the real imported Win16 `GetVersion`. `EnumProc` pushes HWND, both LPARAM
words, and callback mode onto the virtual stack, then returns the bytecode
result in AX to Windows.

The host differential oracle exercises the checked-in bytecode for the
GetVersion import, valid and invalid callback cookies, stop mode, null HWND,
and unsupported opcode/import rejection. It complements the native fixture;
it does not replace execution inside Windows.

## Current native result

MSC6 and LINK4 produced a Windows NE executable (`BUILD=PASS`). Source commit
`3a05a121d8816f8067439c5b1e995b9545c3f44d` was run in 86Box v7.0 on a Tandy
1000 HX profile with an 8088 at 7.159092 MHz and 640 KB, under Windows 3.0
real mode. The fresh guest log reports one bridged `GetVersion` call returning
`0x06160003`, three all-pass callbacks returning TRUE, one stop callback
returning FALSE, restored virtual stacks, wrong-cookie rejection, and
unsupported-opcode rejection. The fixture ended with `RESULT=PASS` and
`WINRET=0` after 43.19 seconds. The private executable SHA256 was
`404dc0bd992742f979d087123184530886cf80b7d41b9b57099f72e1b31639b9`.

See [the sanitized run record](EVIDENCE-20261018.md). The emulator display was
garbled during the desktop/dialog stage, so no screenshot is used as evidence.
This result qualifies only this API/bytecode fixture in the stated emulator
profile. It does not qualify a display driver, Minesweeper runtime, or physical
hardware. The executable and guest image remain private and are not included.
