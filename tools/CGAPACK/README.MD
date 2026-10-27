# Qualified CGA download

`downloads/experimental/CGA/CGA.ZIP` is the single current CGA packet. Its root
contains native DOS `SETUP.EXE`, `README.TXT` and the expanded `CGA` folder.
It supports fixed 160x100x16 RGBI, a 160x100 viewport over a 320x200x16 desktop, 320x200x4 bright palette 1 and 640x200 monochrome
on Windows 3.0 real mode with normal 640 KB. See [installation](../../docs/CGA.MD).

`ACCEPT.JSN` pins the complete expanded packet and its native/build evidence.
The earlier accepted packet and pins remain in `docs/QUAL/CGAPAN/BASE.*`;
its original native evidence stays under `docs/QUAL/CGA`. The three earlier
display drivers and CGACTL are byte-identical. CGAPAN adds its driver, owner,
key DLL, Setup choice and compact shared settings without consumer copy chores. No compiler or emulator
is run by this producer. Physical CGA, clones and composite remain unqualified.

Run `python -B tools/CGAPACK/VERIFY.PY`; current catalog CHECK and CI
also invoke this gate. Source rebuilds use `src/cga/README.MD`; rebuilding
does not replace accepted binaries or relax the acceptance record.
