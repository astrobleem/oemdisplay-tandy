# Developer builds and package verification

Normal users download the ready-to-use `TANDY88.ZIP`, extract `DISK1`, and follow
`README.TXT` to run DOS `INSTALL` and Windows Setup's Other display option.
**Python and media staging are developer rebuild steps, not installation steps.**

## Accepted driver and reservation helper

This package targets Windows 3.0 real mode on the accepted 8086/8088 normal-640K
Tandy configuration. The old root `TNDY16.DRV` and `build_driver.bat` belong to
an earlier path and are not package inputs.

The builder uses only `src/tandysw/bin/TANDY88.DRV` and `RESERVE.COM`, with pins:

- TANDY88.DRV: `ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee`
- RESERVE.COM: `644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8`

To reproduce those binaries with the repository's MASM 5.10, LINK and resource
tools in DOSBox-X:

```sh
python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/driver-build
python3 src/tandysw/RESERVE.PY --dosbox /path/to/dosbox-x --out /new/reserve-build --cpu 8086_prefetch
```

See `src/tandysw/README.md`, `STATUS88.TXT` and `RESERVE.MD` for prerequisites,
provenance and acceptance limits. Packaging never silently rebuilds a missing
binary or substitutes another driver. Pin changes require separate acceptance.

## Rebuild the complete release ZIP

Python 3.8+ is needed on the development host; only its standard library is used.
On Windows, retain the normal `MAKEDISK.BAT` entry point:

```cmd
MAKEDISK.BAT --windows-files C:\WIN30SRC --out C:\RELEASE\TANDY88.ZIP
```

On Linux/macOS:

```sh
python3 MAKEDISK.PY --windows-files /your/windows30/source --out /new/TANDY88.ZIP
```

The media directory must contain these six accepted files. The builder accepts
the original SZDD mode-A compressed files under the requested filenames or the
expanded bytes; it checks SHA256 after expansion:

- EGASYS.FON: `8bd307d7886d0f2fdfc1de3da8253e294233d1c757fd9131a66405fca5825b09`
- EGAFIX.FON: `6df45a74e5756dd0746bcee593be9ac4df4a35458c26bf4570b748def2d394cb`
- EGAOEM.FON: `05bd6ef11802bbca20473b0e409116fd8919c5bbcbbbc26b7ee2ea1f33ad23be`
- CGA.GR2: `1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067`
- CGALOGO.LGO: `d9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807`
- CGALOGO.RLE: `f31392cac25d3433f22a4500e5f42aaa29fc1ac188a1e2525441b759bef21735`

Only those six Windows files are included. No full OS, installation disks,
emulator or compiler toolchain is added. There is no network fetching or input
directory globbing. Missing/wrong files fail before an output is created.
Calling the normal builder without `--windows-files` fails with a developer
rebuild explanation; users should obtain the complete download instead.

`--out` defaults to `TANDY88.ZIP` beside the scripts. Add `--local-out NEWDISK`
to write a ready-to-use extracted disk as well. Add `--windows-dir D:\WIN30`
(quote it on Unix shells) for a nondefault guest Windows path; the helper stays
at `C:\TANDY88`. Output paths must be new and their parent directories must
exist. Existing historical `disk1/`, root binaries, and archives are untouched.

The complete ZIP contains `DISK1/` and a root README. Its disk includes the
completion marker `LOCAL.TXT` and `MANIFEST.SHA`; Python is not bundled into
the normal download. File order, timestamps and attributes are fixed, with
ZIP_STORED for byte-for-byte reproducibility across zlib versions. The extracted
disk must fit standard 360 KB FAT12 media, including 1 KB allocation rounding,
112 root entries, both FATs, root directory and reserved-sector overhead.

## Verify the checked-in release without source media

```sh
python3 MAKEDISK.PY --verify TANDY88.ZIP
```

Verification checks exact members (including all six support files and the
completion marker), all eight binary pins, the full manifest, canonical ZIP
metadata, current source payload, and the 360 KB floppy allocation budget.
No external media directory is required. This is the tag-release CI path;
release automation can upload the same verified checked-in ZIP unchanged.

## Optional support-free developer toolkit

```sh
python3 MAKEDISK.PY --toolkit-only --out /new/T88TOOLS.ZIP
```

This deliberately separate toolkit is not install-ready and cannot be named
`TANDY88.ZIP`. It includes `STAGE.PY`, `TOOLKIT.TXT`, and the base disk payload.
After extraction, a developer can run:

```sh
python3 STAGE.PY --windows-files /your/windows30/source --out /new/disk
```

Normal users do not need this alternative.

## Tests

```sh
python3 oemdisk/TESTDISK.PY
python3 oemdisk/TESTDOS.PY --dosbox /path/to/dosbox-x --out /new/dos-helper-tests
```

Host unit tests use synthetic media with explicit test-only pins and exercise
complete-release and toolkit contracts, deterministic output, wrong/stale inputs,
manifest/source integrity, media decoding, output preservation and disk capacity.
DOS tests use disposable guests, the accepted reservation helper and executable
sentinels. Those tests establish control flow rather than a real Windows boot;
actual Setup and GUI results are documented in `docs/OEMDISK.MD`.

All edited source and generated DOS text uses CRLF. The native Windows wrapper
was statically reviewed; portable Python and DOS helper execution were tested.
Physical hardware and genuine MS-DOS variants remain separate acceptance checks.
