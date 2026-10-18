# Native Win16 far-call fixture - 2026-10-18

## Build and source

- Tested source commit: `2e4753f812211686a9e219527236a7782e13ca0e`
- `W16APIN.C` SHA-256: `fa497bdc07b000fc53903ee286fe0ad16263c7ca6a38d9c6a67022bd8875cff7`
- Private Win16 executable SHA-256: `030169729b316024cee9028a59e98f97e88ca0e265b91c8afa03eabca2bbbe8e`
- Build: MASM 5.10, Microsoft C 6.0, LINK4 5.01.17; `BUILD=PASS`
- MASM emitted a 48-byte callback stream matching `g_far_callback_bytecode` byte for byte. The assembler product itself remains private.
- The exact separate host commands passed 24 root tests, 6 bytecode VM tests,
  and 4 raw-evidence integrity tests.

## Guest run

- Emulator: 86Box v7.0 development build
- Profile: Tandy 1000 HX, emulated 8088 at 7.159092 MHz and 640 KB
- Guest: Windows 3.0 real mode
- Watchdog: 90 seconds; result completed in 43.2 seconds
- `W16API.LOG` was absent before launch and created by this run
- Shared nonblocking emulator lease acquired and released; owned 86Box process stopped
- Result: `RESULT=PASS`, `WINRET=0`, `HPDONE=DONE`

The guest log recorded a real Win16 `GetVersion` result of `0x06160003` in the
native `DX:AX` pair through the bounded far-import token, with `RETF 0`
returning to `1000:0005`. It also recorded three all-pass Windows
`EnumWindows` callbacks and one stop-on-first callback. Each callback's
first-party assembled 8088 program returned through decoded `RETF 6`, restored
the virtual stack, and returned its AX result to the native C callback.
Unknown far imports were rejected. The earlier `INT FF` / HLT smoke remains a
separate baseline in [`EVIDENCE-20261018.md`](EVIDENCE-20261018.md).

The sanitized raw files are in
[`evidence/farcall-retf6-20261018`](evidence/farcall-retf6-20261018/); their
exact byte lengths and SHA-256 hashes are in its `MANIFEST.json`:

- `W16API.LOG`: 1,296 bytes, SHA-256
  `2d641f38cfd54e0cd652b30cf943542f6046f1d3f64d352dd3175571222a5c0d`
- `WINRET.TXT`: 11 bytes, SHA-256
  `130182ef952a8e56ff9fd062f83560a0fe855afd1d649d4c16ff66577b8071a6`

The source and manifest do not include the Windows guest image, Windows media,
private executable, assembler executable, or unrelated files. This is
emulator-only fixture evidence. It does not establish physical-hardware or
display-driver qualification, a generic NE import bridge, or Minesweeper
runtime support.
