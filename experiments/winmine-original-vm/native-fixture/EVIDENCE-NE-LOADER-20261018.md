# Native minimal NE loader evidence

Source commit: `28a0ffa38fa0d28016b68ccc382fb0e8ef3ec260`.

The first-party `W16APIN.EXE` was built with Microsoft C 6.0, LINK4 5.01.17,
and MASM 5.10 (`BUILD=PASS`; private executable SHA-256
`1e64328a1f5fd52e938cfa36944c2ea989ccbd6accaed2497526a14a0a5c4c97`). The
host generator emitted a 378-byte first-party `W16TEST.NE` input (SHA-256
`decec10f17d38158fa4eac75e9b8e4a75f2c5d2ae7375a0de1b9cfe5b7488726`). Neither
binary is included in the repository.

The bounded 86Box v7.0 development run used a Tandy 1000 HX profile, emulated
8088 at 7.159092 MHz, 640 KB, and Windows 3.0 real mode. It completed in 62.2
seconds under a 90-second watchdog. The fresh log records the loaded NE image,
named `KERNEL!GetVersion` and `USER!EnumWindows` imports, three callbacks
executed from the loaded callback segment, restored `RETF` frames, malformed
NE and unsupported-opcode rejection, `RESULT=PASS`, and clean `WINRET=0` /
`HPDONE=DONE` return. The owned emulator stopped and the shared lease was
released.

Raw sanitized evidence:

- [`W16API.LOG`](evidence/ne-loader-20261018/W16API.LOG) — 1,937 bytes,
  SHA-256 `f1a96d73395fd361fda20cbbe2ea2f779a4fe4cc1814dc96d683236ab471e7a0`.
- [`WINRET.TXT`](evidence/ne-loader-20261018/WINRET.TXT) — 11 bytes,
  SHA-256 `130182ef952a8e56ff9fd062f83560a0fe855afd1d649d4c16ff66577b8071a6`.
- [`MANIFEST.json`](evidence/ne-loader-20261018/MANIFEST.json) records the
  exact source/build hashes, emulator profile, fixture hash, lease/exit state,
  and original-input hashes before and after use.
- [`MNSN1-host-probe.json`](evidence/ne-loader-20261018/MNSN1-host-probe.json)
  and [`MNSN2-host-probe.json`](evidence/ne-loader-20261018/MNSN2-host-probe.json)
  record separate host-only entry-slice probes against the pinned original
  executables using probe source commit
  `190016d9ff9cc34eceb10c4ef080a710abd7c964`. Each reports the pinned input
  hash and unchanged input bytes.

The private original disk image hash remained
`ec32fab0f73818ff30d90ed0f6a0384627e33ea211fd926e3803382c5600549a`. MNSN1
and MNSN2 `WINMINE.EXE` hashes also matched before and after the host probes.
The original application was not run in the emulator. This evidence is an
emulator-only compatibility result for a first-party test fixture; it does
not qualify the display driver, Minesweeper, or physical hardware.

CI exercises the repository's Python NE parser and bytecode oracle, generated
fixture relocations, fail-closed cases, and raw evidence hashes. It does not
execute the production C interpreter. The C implementation's behavior is
therefore supported by the exact MSC6 build hash and native guest log above.
