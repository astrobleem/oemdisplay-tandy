# Qualified CGA download

`downloads/experimental/CGA/CGA.ZIP` is the single current CGA packet. Its root
contains native DOS `SETUP.EXE`, `README.TXT` and the expanded `CGA` folder.
It supports 160x100x16 RGBI, 320x200x4 bright palette 1 and 640x200 monochrome
on Windows 3.0 real mode with normal 640 KB. See [installation](../../docs/CGA.MD).

`ACCEPT.JSN` pins all 25 members, the original independently reviewed packet,
the public documentation-only derivation and the exact native/review evidence.
All 24 members other than root README are unchanged. The original reviewed
packet is retained inside `docs/QUAL/CGA/REVIEW.ZIP`. No compiler or emulator
is run by this producer. Physical CGA, clones and composite remain unqualified.

Run `python -B tools/CGAPACK/VERIFY.PY`; current catalog CHECK and CI
also invoke this gate. Source rebuilds use `src/cga/README.MD`; rebuilding
does not replace accepted binaries or relax the acceptance record.
