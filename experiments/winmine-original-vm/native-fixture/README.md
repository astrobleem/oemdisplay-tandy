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

The fixed interpreter accepts `PUSH BP`, `POP r16`, `MOV r16, imm16`,
`MOV BP,SP`, register and BP+disp8 `CMP /7` (`81h`/`83h`), short `JZ`/`JNZ`,
immediate `CALL FAR`, `RETF`/`RETF imm16`, the legacy `INT FF` smoke trap, and
`HLT`. It uses an eight-word virtual stack and a 64-instruction limit; unknown
opcodes, imports, branches, and invalid stack operations fail closed.

The newer bounded path resolves only far import token `F001:0001` to the real
Win16 `GetVersion` API. The callback is first-party 8088 assembly in
[`W16CALL.ASM`](W16CALL.ASM); MASM 5.10 output was compared byte for byte with
the VM array. It performs a decoded far call, reads HWND and the two LPARAM
words from its virtual Pascal frame, checks the cookie, then returns with
decoded `RETF 6`. Windows itself supplies the real `EnumWindows` callback
arguments to the native C `EnumProc`; that routine creates the VM frame and
returns the VM's AX result to Windows. This proves the fixture's bounded
far-call and callback semantics, not a general NE import bridge or execution
of the original Minesweeper executable.

The host oracle tests the checked-in byte arrays with a fixed version value.
It does not model Python `Win16Host` or stand in for the native API result.
The guest test below calls the real Win16 `GetVersion` under Windows 3.0.

## Native emulator results

### Historical smoke baseline

The earlier `INT FF` / HLT run remains recorded separately in
[`EVIDENCE-20261018.md`](EVIDENCE-20261018.md) and
[`evidence/smoke-20261018`](evidence/smoke-20261018/). It tested source commit
`3a05a121d8816f8067439c5b1e995b9545c3f44d`; it is not the new far-call result.

### `CALL FAR` / `RETF 6` integration

Source commit `2e4753f812211686a9e219527236a7782e13ca0e` was built with MASM
5.10, Microsoft C 6.0, and LINK4 5.01.17 (`BUILD=PASS`), then run in 86Box
v7.0 development on a Tandy 1000 HX profile (emulated 8088, 7.159092 MHz,
640 KB) under Windows 3.0 real mode. The fresh log records the real
`GetVersion` value `0x06160003` in the `DX:AX` result, a far-import `RETF 0`
back to `1000:0005`, three all-pass `EnumWindows` callbacks returning TRUE,
and a stop-on-first callback returning FALSE through decoded `RETF 6` with
the stack restored. Unknown far imports fail closed. The fixture ended with
`RESULT=PASS`, `WINRET=0`, and `HPDONE=DONE` after 43.2 seconds.

The private fixture executable SHA-256 was
`030169729b316024cee9028a59e98f97e88ca0e265b91c8afa03eabca2bbbe8e`; it is
not distributed. [`EVIDENCE-FARCALL-20261018.md`](EVIDENCE-FARCALL-20261018.md)
links the sanitized raw log and DOS return record and gives their hashes. The
emulator display was garbled, so no screenshot is used as evidence. This
result qualifies only this API/bytecode fixture in the stated emulator
profile. It does not qualify a display driver, Minesweeper runtime, or physical
hardware. No Windows media, guest image, or executable is included.
