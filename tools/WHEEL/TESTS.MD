# WHEEL 0.1 validation

## Scope

A DOS/8088 diagnostic, not a Windows scrolling driver. The serial decoder is
an IntelliMouse-format candidate decoder. Two physical Genius NetScroll direct-serial captures are recorded below. A missing DOS API does not diagnose hardware.

## Reproduce

- DOS, with legally obtained Microsoft C6 and LINK4 configured through PATH,
  INCLUDE and LIB: change to `tools/WHEEL/SOURCE`, then run `BUILD.BAT`.
- Run the built executable with `/TEST` for synthetic packet fixtures.
- Host, with Python 3 and GCC: `python3 tools/WHEEL/TESTS/MOCKTEST.PY`.
- For standalone host parser checks:
  `gcc -x c -std=c89 -pedantic -Wall -Wextra -Werror -DHOST_TEST -fsanitize=address,undefined -g tools/WHEEL/SOURCE/WHEEL.C -o wheeltest`
  then `ASAN_OPTIONS=detect_leaks=0 ./wheeltest`.

The mock tests replace hardware calls and do not access real serial ports.
Leak checking is disabled because the validation runner does not support it;
these tests allocate no dynamic heap memory.

## Completed checks

- Microsoft C6 `/G0 /AS /W3 /Od` compile and LINK4 link: no warnings.
- Exact included executable: DOSBox-X Tandy, normal core, 8086_prefetch,
  self-test passed. At 3000 fixed cycles, the supported API timed run ends,
  and unsupported API and resident-handler raw-refusal branches behave as
  documented. This does not emulate the actual mouse's electrical behavior.
- Synthetic fixtures cover all 16 signed wheel values, ordinary three-byte
  packets, middle-only fourth byte, invalid fourth-byte bit 5, line errors,
  synchronization gaps and 10,000 malformed-byte steps. Host ASan/UBSan passed.
- Nine mock cases passed: resident handler, missing port, active UART IRQ,
  cancellation, changed UART state during consent, transmitting UART, DLAB
  selected, Esc and normal timeout. Refusals made zero mocked port writes;
  both capture exits restored divisor/LCR/MCR/IER.
- Independent source review completed after correcting API baseline handling,
  fourth-byte validation and UART preflight checks.

## Limits

The physical result is bounded to the two raw captures below. No Windows
scrolling support or system-wide wheel API is established.
A clean DOS boot and correct physical port remain essential. DTR/RTS changes
may reset the mouse. Register restoration cannot restore consumed bytes or the
mouse's internal state. BIOS midnight reset may shorten a capture.

No proprietary compiler, SDK, driver, operating-system media or third-party
binary is included. WHEEL.EXE is accompanied by its original source.

## Bounded physical raw-capture result

Two Genius NetScroll direct-serial runs on a physical Tandy EX produced valid
four-byte packets. After settling, opposite wheel directions yielded fourth
bytes 0F and 01. The first run recorded 27 three-byte packet cores, 27 fourth
bytes, 13 nonzero wheel samples and net wheel +9. The second recorded 27
packet cores, 27 fourth bytes, 20 nonzero wheel samples and net wheel +2.
Both reported zero UART error bytes and zero decoder errors.

This demonstrates raw directional wheel packets for this mouse/setup in
these two short captures. It does not establish every serial-mouse model,
long-duration behavior, a Windows wheel driver, or an INT 33h wheel API.
No photographs, private machine/user identifiers or chat records are included.
