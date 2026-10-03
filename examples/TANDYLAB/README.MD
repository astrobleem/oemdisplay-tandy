# TANDYLAB CompactFlash hardware-test pack

[Download TANDYLAB.ZIP](TANDYLAB.ZIP), extract it on the modern PC, then copy
its single `TANDYLAB` folder onto the confirmed and backed-up CompactFlash
card. The documented PC reader letter is `D:`; its DOS drive letter on the
Tandy may differ. The user supplies and installs their own DOS/Windows 3.0.

This is a first physical-hardware test pack. Emulated acceptance does not
establish real-Tandy speed, mouse behavior or compatibility. Nothing here
automatically installs, edits boot/configuration files, replaces the shell,
or copies a private DLL into Windows.

## Copy and test

Start with the [copy/run guide](README.TXT), [application catalog](CATALOG.TXT)
and [first-hardware checklist](CHECK.TXT). Preserve an existing folder before
copying, keep a known-good Windows/boot backup and safely eject the card.
Start Windows with its normal accepted procedure. A custom display driver
still requires its guarded TANDY88 launcher and successful reservation.

The final Fly Swat game is in `FLYSWAT/SWAT.EXE`: fullscreen fast rendering
on the five supported profiles, slow windowed `/G` fallback, silent normal
play and no normal-play file writes. Its approximate XT emulator timings
are not calibrated physical measurements. See [game instructions](FLYSWAT/README.TXT).

App-local files remain paired. In particular, keep `BEATS/MIDIMAP.DRV` with
Beats. Launch the experimental dialog demo through `EXPER/CDLG/CDSTART.EXE`,
with its unchanged `CDTEST.EXE` and `COMMDLG.DLL` beside it.

## CDSTART source and focused evidence

[CDSTART](CDSTART/README.TXT) fixes Windows 3.0's private static-import lookup
by temporarily entering the demo directory. It checks for the pair and
refuses if COMMDLG is already loaded, then restores active/per-drive
directories immediately after WinExec returns. It is not resident.

The child's later file dialogs can change an inactive drive's remembered
directory after the helper exits. The [native test notes](CDSTART/TESTS.TXT)
and preserved earlier failing expectation explicitly record that limit.
Use full paths for later file work and new scratch filenames for Save/Read.
Helper source, build tools, accepted logs and [focused harness source](CDSTART/QA)
are included. Fresh publication builds reproduced helper and harness bytes.

## Optional display toolkit

`DRIVERS/T88TOOLS.ZIP` contains only the first-party display toolkit. It is
not an install-ready OEM disk: its unchanged STAGE.PY requires eight exact
Windows support files from the user's own media. Read [the staging guide](DRIVERS/README.TXT).
Stock-CGA Windows first, then the documented Windows Setup route; do not
manually edit SYSTEM.INI. The hardware text-mode experiment is excluded.

## Provenance and verification

This directory's runtime files and `TANDYLAB.ZIP` are byte-for-byte from the
final sealed pack. [MANIFEST.SHA](MANIFEST.SHA) covers original pack members;
it excludes itself and publication-only README/source/evidence/ZIP files.
[SOURCES.TXT](SOURCES.TXT) links the app projects and standalone source packages.
No Windows, Microsoft SDK/DDK/compiler binaries, fonts or OS image are added.

Run `python3 VERIFY.PY` on a modern host for read-only archive/hash checks.
It verifies the pack and nested helper/toolkit manifests; it does not execute
apps, install drivers or make a hardware-test claim. [Publication checks](EVIDENCE/PUBCHECK.JSON)
are separate from native evidence and GitHub CI. The only existing workflow
is tag-triggered release packaging, so no PR CI is configured.

- TANDYLAB.ZIP: 355,159 bytes, SHA256 `ac825b9e38d6fc636cbf33960e2e55eb00693dc92de49d8d04adf093bcb13881`
- SWAT.EXE: 16,989 bytes, SHA256 `6f65c56dd17a5667e16b583638d8e02a0a8b937234357b09457ca60ee965a60b`
- CDSTART.EXE: 4,867 bytes, SHA256 `c2cf986d1cd5d44ed02a31a4c327601b4b7b4b6a4dceb94fa41f8909d8136eac`

This isolated draft adds only `examples/TANDYLAB`; no existing source,
driver, default build or workflow is changed. No merge, tag or release.
