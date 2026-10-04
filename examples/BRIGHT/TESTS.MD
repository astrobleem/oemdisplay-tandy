BRIGHT01 first playable slice verification, 2026-10-04

Fresh publication checks
- Warning-free period C6/LINK4 build, /G0 /Gw /AS /W3 /Od; byte-identical to the tested 8271-byte executable. SHA256 f00c8b3efc31fc6d3073543cccea71cc3c48b1a662bff1193d632a07314fbdef.
- Independent strict-C89 engine oracle: 136884 assertions; all 108 nominal routes (23 success, 85 failure, including suffixes skipped after early endings), 6656 choice boundary cases and 2560 continuation boundary cases.
- Engine and UI copy audits pass the 18-column/four-line bounds. The host compiler retains one pre-existing misleading-indentation warning in ENGINE.C; it does not fail the oracle.
- Scoped ISA audit: 1850 reachable instructions, no post-8088 suspects. Imported Windows code and unresolved indirect/unreachable paths are excluded.

Retained native evidence
Windows 3.0 /R GUI testing at 160x200x16 and 640x200x2 covered all five notices, receipts, metrics, stacked choices, both endings, Restart/Exit, keyboard controls, mouse selection, cold relaunch and Alt+F4/DOS return. Success 1,2,1,1,2 reaches 58/72/93. Failure 2,3,2 ends after event 3 at 96/10/92. The fixtures used 640 KB with XMS/EMS/UMB disabled, required RESERVE protection, and accelerated uncalibrated 8086_prefetch emulation. This does not establish physical speed or unexpanded 256 KB compatibility.

Only this five-event first slice is included; it is not the eventual full game. Physical hardware speed, other video modes and broader manual input compatibility remain unqualified. No driver, OS/media/font/toolchain files, screenshots, private receipts or guest images are added. TESTS/README.MD documents the portable oracle and copy checks; BUILD.PY/AUDIT.PY reproduce the native build/scoped audit.
