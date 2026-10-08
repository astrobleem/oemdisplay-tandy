# Tandinator 0.3.8 experimental release

[Download TANDI11.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI11.ZIP) ·
[Public experimental release and checksums](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experiments-2026-10-07)

This is separate from the canonical v0.2 app and does not replace installed defaults.

TANDI11 contains the confirmed thinking-delay, cap-continuation and F3 sound fixes, the retained quiet demo/artwork, and the explicitly approved experimental notebook and Ask Two option. Learning use starts OFF every launch; Ask Two requires an explicit choice and never exceeds 40 questions.

The canonical engine, DB loader and standard DAT remain unchanged. AUDIT08 is a separate unpromoted option. Reports pin the exact DAT, require explicit identity/review/save, and cannot come from a game that used learning. Conflicts disable notes. Capacity is 256 cells and 128 saved-game IDs; Reset retains IDs, while explicit Fresh preserves archives.

Qualification passed 226 actual notebook/file-format checks, nine source-derived settings API mock checks, 30,720 deterministic full-roster games, and 19 final native Windows 3 real-mode runs across three Tandy modes. Cabinet/logo pixels, moving eyes, demo poses/placements and black frames match the original art. The native suite covers Q40 boundaries, continuation, recovery, cold relaunch, write failure, wake/input cleanup, saved-off sound and bad DAT.

Run `python TESTPUB.PY` beside the ZIP to verify every entry and the source/EXE/evidence pins. QA11.TXT explains study assumptions: borrowed reference answers are not independently audited facts; learning can hurt, and the ten-rejection host study limit is not a runtime limit. Logical file recovery is not a physical disk/power-loss guarantee. Physical hardware is untested.

The original local qualification changed no installed Windows/INI/default or
CF files. Its immutable packet was subsequently published as the separate
experimental download above. The packet excludes private Windows media, compilers, emulator, drivers and user reports. Use licensed private inputs to reproduce native checks.
