# Experimental HPAN R3 and HPXY R1 downloads

These experimental candidate packages are stored as repository files, not GitHub Release assets. Each ZIP contains the candidate source snapshot, driver/helper binaries, tests, and qualification evidence. Neither is an installer. Read the package README and qualification files before use, and follow the isolated Windows profile and rollback instructions inside the ZIP. No Windows installation media, ROMs, emulator, or compiler/SDK is included.

Canonical development repository: [astrobleem/oemdisplay-tandy](https://github.com/astrobleem/oemdisplay-tandy). The source commit pins below are recorded in the packages but do not resolve in the repository's public Git history; the ZIPs include the source snapshots.

## HPAN R3 — experimental, hardware not qualified

[Download HPAN R3 physical-acceptance candidate ZIP](./HPAN-R3-PHYSICAL-ACCEPTANCE.zip) · [SHA-256 list](./SHA256SUMS.txt)

- Size: 668,581 bytes
- SHA-256: `18e3d001ae57dce3a51a2835169b9df431d081edfc370584aa2c351478923a62`
- Package source pin: `00f232840f18b471c20aedaa1a2d07fb1813017d`
- Emulator record: 86Box emulating a Tandy 1000 HX, 8088 at 4.772728 MHz, 640 KiB; Windows 3 real mode. The display is 320×200×16 over a 640×200×16 logical desktop.
- Separate physical record: the archive marks the run `USER_ACCEPTED_PARTIAL` and explicitly sets `physical_hardware_qualified: false`. Its scope is a short 0→104→0 origin run; it has no full-range sweep, physical software baseline, visual frames, measured physical blank duration, or physical serial-mouse test.

![Actual HPAN R3 86Box capture from EVIDENCE/KEYS/FRAME314.PNG: emulated Tandy 1000 HX, Windows 3 real mode, 320×200×16 display.](./HPAN-R3-86Box-FRAME314.png)

*Original emulator frame from the candidate archive. This is not a physical-hardware screenshot.*

## HPXY R1 — experimental, emulator evidence only

[Download HPXY R1 experimental ZIP](./HPXY-R1-EXPERIMENTAL.zip) · [SHA-256 list](./SHA256SUMS.txt)

- Size: 481,867 bytes
- SHA-256: `78a3d39b9ef800b3b31e2bf506d7ac9483df7d3b99fc551d2b589dc781dbdac8`
- Package source pin: `f123135e2fbdf04479b184bccc9cc100cc0ee62f`
- Emulator record: 86Box emulating a Tandy 1000 HX with an 8088 and 640 KiB; Windows 3.0 real mode. The display is 320×200×16 over a 640×256×16 logical desktop.
- Source build dependency: this ZIP includes the nine first-party HPAN source files required by `XYPATCH.PY` through `../HPAN/HPATCH.PY`. This supplies the missing source dependency; the tested HPXY runtime driver and helper hashes are unchanged.
- Physical XY operation is untested; the package manifest sets `physical_XY_tested: false`. Follow the isolated-clone instructions in `README.TXT`; review `QUAL.TXT` and `PINS.JSN` before use.

![Actual HPXY R1 86Box capture from EVIDENCE/XYUN3/FRAME514.PNG: emulated Tandy 1000 HX, Windows 3.0 real mode, 320×200×16 display.](./HPXY-R1-86Box-FRAME514.png)

*Original emulator frame from the candidate archive. It is emulator evidence only, not physical-hardware qualification.*

## Verification notes

The archive ZIP structures and every member hash matched their embedded manifests. The two screenshots above are original `FRAME*.PNG` captures in those archives; they were visually reviewed for unrelated desktop content and were not generated. This publication task did not rerun emulator or hardware tests. The package test reports and scope are preserved inside each ZIP.
