> For current installation, use [current downloads](../../docs/DOWNLOADS.MD).
> This directory preserves the historical R1 component publisher.

# Qualified R1 redistributable release

This publisher binds the two previously reviewed, unchanged R1 ZIPs to their
visible component source and notices, the Oct19 emulator qualification and
an exact publication commit. No native session is started by these tools.

- `KIT` is the complete first-party wheel/font source and runtime snapshot.
- `downloads/R1` holds the original reviewed ZIP bytes, not a private installer.
- `PUBLISH.PY --out NEW --commit SHA` builds the six public assets.
- `PUBLISH.PY --verify NEW --commit SHA` checks exact source, content and scope.
- `TESTPUB.PY --release NEW` exercises corruption/extra-owned-file/scope guards.

The overlay supplies nine copies of four unique MIT binaries. All 370 other
inputs must be supplied locally. Windows media alone does not supply HPXY,
TNDYK3, TSHELL, XYCTL, WXTWHL, paired TP and other qualified project helpers.
Their inclusion in a private build is not a redistribution grant. The local
assembly utility refuses missing/mismatched inputs and existing output.

Build source reproduction in a fresh copy of KIT. Driver: run
`python build_driver.py` in mouse with existing Open Watcom 1.9 BINNT tools
(or WATCOM_BIN), then compare WHEEL.DRV SHA256 with the qualification record.
Fonts: from KIT run `python fonts/generator/HOST.PY BUILD.PY --out NEW-FONTS`
and `python fonts/generator/HOST.PY TEST.PY --out NEW-FONTS`. Python 3.8+,
Pillow and separately supplied build tools are external dependencies; none
is bundled. These host builds do not repeat guest/hardware qualification.

The guarded R1 workflow builds/readbacks assets on the exact event commit,
then a separate fresh runner checks hashes/scope and creates a new draft
only for v0.1.0-rc.7. It never replaces an existing tag/release/asset.
The old rc.6 publisher remains frozen for rc.6. Publication follows review
and successful required CI on the exact integrated commit.
