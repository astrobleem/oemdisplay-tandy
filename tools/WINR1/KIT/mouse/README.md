# Windows 3.0 real-mode serial mouse and wheel driver R1

`WHEEL.DRV` targets Windows 3.0 real mode on an 8086/8088, COM1 at
03F8h/IRQ4, 1200 baud, 7N1, with two buttons. Ordinary three-byte serial
mouse frames deliver movement and buttons immediately; an optional fourth
byte supplies signed wheel units. This is the specific tested serial
contract, not a universal PS/2 or USB mouse driver.

Build with the installed Open Watcom 1.9 tools at `C:\WATCOM\BINNT`:

```text
python build_driver.py
```

The resulting 1,820-byte driver has SHA-256
`84df334cfc34af2dc8785676e92cfe428e0288cb21e2c6e94dbc16baba6d12f0`.
It links only the newly authored `driver.asm`, `decoder.asm` and `timestamp.asm` objects;
there are no imports, DDK implementation/macros, SDK import libraries, or
runtime libraries linked into it. Build tools are not included. The source
license is MIT; see `LICENSE`. The integrating author inspected ABI and
prologue references, so this is explicitly not a clean-room claim; see
`PROVENANCE.md` for that distinction and the private combined-media boundary.

The ordinary mouse exports are ordinals 1-4 plus WEP at 5. Named wheel
exports, also at ordinals 10-13, are `WheelApiVersion` (0100h),
`WheelReadDelta` (destructive signed event queue), and `WheelLostPackets`
(saturating WORD). Windows export names are stored uppercase for loader
compatibility. The event queue has 31 usable entries and drops newest on
overflow. API calls preserve DS/BX/BP and lasting IF/DF.

The driver saves and restores COM1's BIOS data, IRQ4 vector, PIC mask bit,
UART LCR/IER/MCR and divisor across Enable/Disable. The native qualification
uses an unchanged Tandy HX emulator surrogate at 7,159,092 Hz and 640 KiB,
with actual UART register/IRQ processing and loopback-injected serial bytes.
The final evidence report states the exact passed scope. Physical serial
mouse hardware, protected mode, Windows 3.1, other ports and autodetection are
not qualified by these tests.

For an owned Windows installation, the driver is selected through the existing
`SYSTEM.INI` `[boot] mouse.drv=WHEEL.DRV` entry with `WHEEL.DRV` in its
SYSTEM directory. Wheel scrolling requires a compatible client such as the
separately supplied WXTWHL bridge; this driver does not itself scroll windows.
The combined own-media Setup route performs the tested installation and keeps
unrelated settings. Windows media, display/keyboard derivatives and the bridge
are not licensed by this driver's MIT notice.

## Decoder module

`decoder.asm` is a newly authored 8086 MASM-compatible decoder for the two-button Microsoft-compatible serial packet contract and its optional wheel byte. It was written from the interface and protocol facts recorded here. No existing Microsoft, DDK, or derived mouse-driver implementation was inspected or copied. The source is released under the MIT License; see the header in `decoder.asm`.

## Build

From this directory, assemble with the existing Open Watcom assembler:

```text
C:\WATCOM\BINNT\wasm.exe decoder.asm
```

The assembler writes `decoder.obj` beside the source. The module uses `.8086`, `.model small`, `_DATA`, and `_TEXT`; it has no imports, runtime-library dependencies, hardware accesses, or calls. Link `_DATA` into `DGROUP` so the caller's `DS` addresses the decoder state. `test_vectors.py` and `protocol_model.py` form a host-independent executable protocol model and vector suite; run them with `python -m unittest -v test_vectors` from this directory. This Python suite checks the written protocol contract, not the assembled machine code. The actual DOS machine-code harness already passed all 263,967 generated records; the retained result identifies its exact executable and vector hashes.

## Entry points and register contract

All procedures are near. The caller supplies `DS = DGROUP`. The decoder is single-context state and must be called serially; the driver owns UART access, IRQ handling, and any interrupt masking needed around queue reads.

| Entry | Input | Output |
| --- | --- | --- |
| `dec_reset` | none | Resets parser and button baseline; empties the 32-slot ring (31 usable entries) and clears the lost count. |
| `dec_feed` | `AL` byte, `AH` UART LSR | At each completed three-byte frame, `AX` is a Windows mouse flag word, `BX` signed `dx`, `CX` signed `dy`; `CF=1` iff `AX` is nonzero. Other bytes return `CF=0`. |
| `dec_read` | none | `AX` is the next sign-extended wheel delta (`-8..7`), or zero when empty. |
| `dec_lost` | none | `AX` is the saturating count of dropped wheel events. |

The procedures may clobber `AX`, `BX`, `CX`, `DX`, `SI`, `DI`, and flags. They preserve `BP`, `DS`, and `ES`. No procedure changes the lasting direction or interrupt-enable state. `dec_feed` returns the specified carry flag. Queue operations are intended to run with interrupts disabled when called from the IRQ path; the caller protects any read/write lifetime that could race.

## DOS machine-code harness

`dostest.asm` links directly against `decoder.asm`. It reads `VECTORS.BIN` in 504-byte blocks (42 records per read), invokes each operation, checks all documented return values, and sets `BP`, `DS`, and `ES` sentinels around every decoder call. A mismatch prints its zero-based record index and a small error code, then exits with status 1; success prints the record count and exits with status 0. The executable expects `VECTORS.BIN` in its current DOS working directory.

Build both the stream and DOS MZ executable with:

```text
python build_decoder_test.py
```

The build script uses the existing `C:\WATCOM\BINNT\wasm.exe` and `wlink.exe`; it does not launch the DOS executable. Run the generated `DTEST.EXE` from DOS with `VECTORS.BIN` in the same directory. Its 8.3 filename is intentional. `make_vectors.py` can be run alone with `--output VECTORS.BIN`. Each 12-byte record is `<op, data, lsr, expected_cf, expected_ax, expected_bx, expected_cx, check_coordinates>` using little-endian words. Operations are reset `0`, feed `1`, read `2`, and lost-count `3`. `check_coordinates` is set only for completed three-byte frames, since `BX/CX` are unspecified for other feed calls. For read/lost records, `expected_ax` contains the return value. The generator models exhaustive signed coordinate encodings and wheel nibbles, button edges, malformed/resynchronized packets, UART errors and DR-clear input, queue overflow, and the full 16-bit loss-counter saturation path.

## Wire and event rules

* LSR error bits `0x1e` abort the partial packet and discard the byte. A clear data-ready bit (`0x01`) discards the call without advancing parser state.
* A byte with bit 7 set aborts the partial packet. Any byte with bit 6 set starts/restarts a three-byte frame. In the header, bit 5 is left, bit 4 is right, bits 0–1 are the high two X bits, and bits 2–3 are the high two Y bits. The following bytes contribute their low six bits. Coordinates are signed 8-bit values.
* At byte three, movement flag `1` is set when either coordinate is nonzero. Button transition flags are left-down `2`, left-up `4`, right-down `8`, and right-up `16`. Button state is retained across malformed bytes and UART errors; `dec_reset` clears it.
* A possible fourth byte is accepted only when bits 7, 6, and 5 are clear. Bit 4 is ignored and the low nibble is a signed wheel delta. Zero deltas are ignored. A subsequent header also cleanly abandons the optional-byte opportunity.
* The wheel queue has 32 physical slots and a 31-event capacity. On overflow, the newest event is discarded and the lost counter increments to `0xffff` at most.


## Timestamped API extension

`WheelReadDeltaAge` (ordinal 13) returns the same shared-ring signed delta in AX and BIOS-tick age in DX; `FFFFh` means empty or unknown timing. API version and ordinals 10-12 retain their v1 behavior. See `API13.md` for exact age, register and midnight limits. Only an accepted IRQ enqueue stamps a slot; overflow leaves existing timestamps intact.

The standalone NE build also requires Python Capstone. `WATCOM_BIN` can override the installed tool directory. It generates its own map and checks linked DS operands, export prologues and both timestamp-word CS negative controls; it needs no DOS harness artifacts. The unchanged decoder harness remains separate. Actual timestamp API DOS and native evidence is recorded in `TIMED-QUALIFICATION.json`; the final combined qualification is separate.
