# Current native Windows XT packages

The full desktop producer is `tools/DOSINST/RCPUB.PY`; its portable host checks
run with `python -B tools/DOSINST/TESTPUB.PY`. The separate display producer is
`tools/XRSYNC/PUBLISH.PY`, checked by `python -B tools/XRSYNC/TESTPKG.PY`.
These developer tools package the exact qualified runtime binaries. Consumers
use the ready DOS installer or the driver disk linked from [README.md](README.md).
See [the installation guide](docs/DESKTOP.MD) for the full desktop.

The sections below retain font, startup and fixed-profile development records.
Their accepted payloads and historical qualification records remain unchanged.

# rc.5 original fonts and exact qualified package

The seven XT Pixels font resources are original MIT grid drawings. Build
them on a modern Python/Pillow host with tools/XTFONTS/BUILD.PY and TEST.PY;
see the [font source guide](tools/XTFONTS/README.MD). Windows font media is
not a generation input. Public CI packages the exact native-tested disk and
runtime, preserving the qualified zero-SHA/faster START base. No proprietary
compiler/OS/non-font support resources are fetched or shipped.

After the existing package tests and MAKEIMG build, run
python3 tools/XTFONTS/HOST.PY PUBLISH.PY --package <dist> --out <new-release-dir> --commit <sha>.
This verifies qualification/source/runtime pins and produces original-font,
source and preview downloads. The release workflow verifies the exact tag,
commit, qualification and complete asset checksums before making a new draft.
Existing assets/tags are never overwritten. Explicit publication authorization
promotes that verified draft to a prerelease; it is not a native rebuild.

The packaged BUILD.JSON/README are unchanged pre-publication snapshots so the
disk and toolkit remain byte-identical. Current QUALIFY.JSON and START-HERE
carry the final qualification and instructions. Native code/binary changes
still require a separately allocated emulator slot and new qualification.

# Retained fixed-profile build and splash default

The accepted independent startup default is the [slow flag wave](examples/WXTSPL/WAVE/README.MD).
The portable toolkit carries its exact qualified module/wrapper and own-media
preparation tool. The guarded DOS installer enables that short pre-load wave
in qualified Color mode; other profiles retain static startup.
[Installer qualification and exact pins](docs/QUAL/WAVEINS.JSON) cover normal
Color/static exits, native refusals and byte-verified rollback.

The retained fixed-profile package is built by `tools/FLASHDISK/MAKEIMG.PY`
and its Windows XT release workflow. Every current Setup display profile selects the
approved `WXTSPL01.RLE` (SHA-256
`eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c`).
The retired Tandy image is not a current installation choice.

```sh
python3 tools/FLASHDISK/TESTWAVE.PY
python3 tools/FLASHDISK/TESTFAT.PY
python3 tools/FLASHDISK/TESTPKG.PY
python3 tools/FLASHDISK/MAKEIMG.PY --out /new/winxt-public
python3 tools/FLASHDISK/TESTPKG.PY --verify /new/winxt-public
```

These public outputs contain no proprietary WIN.COM or Windows support bytes.
Use [the current installation guide](tools/FLASHDISK/README.MD) and the
[approved XT artwork source](examples/WXTSPL/ART/tools/BUILD.PY). The original
loader is supplied by owned Windows media. The DOS updater privately builds
the independent loader, changes only guarded starters, and retains exact
original starter backups. Normal Windows Setup owns display installation.
Public CI packages the qualified binaries without recompiling the legacy tools.

For original helper-source reproduction, use an existing owned Microsoft C 6
toolchain: CL /nologo /c /G0 /AS /W3, then LINK4 /NOE /NOD /ST:4096 for
TINST/PREPXT or /ST:8192 for WAVEXT, with SLIBCE.LIB. The checked-in helper
BUILD.BAT files use an existing T: toolchain. Changed executable bytes require
new native qualification and complete manifest/helper pin updates.

## Historical OEM producer

The retired TANDY88 producer, source metadata and regression tests live in
[oemdisk](oemdisk/HISTORY.MD). They are development references. Current consumer
downloads are linked from [README.md](README.md) and [the download page](docs/DOWNLOADS.MD).

## Bundled display support

Current package builders use `distributions/WINXT/CGA.GR2`, the expanded
2,104-byte qualified grabber. Each packet bundles it with its selected original
fonts and startup assets. Stock Windows itself remains an installation input;
consumers do not gather individual driver support files.
