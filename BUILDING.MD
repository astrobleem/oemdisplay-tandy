# Developer builds and package verification

Normal users download the ready-to-use `TANDY88.ZIP`, extract `DISK1`, and follow
`README.TXT` to run DOS `INSTALL` and Windows Setup's Other display option.
**Python and media staging are developer rebuild steps, not installation steps.**

## Five driver profiles and unchanged reservation helper

This package targets Windows 3.0 real mode on the accepted 8086/8088 normal-640K
Tandy configuration. The old root `TNDY16.DRV` and `build_driver.bat` belong to
an earlier path and are not package inputs.

The builder uses the five pinned drivers in `src/tandysw/bin/` and the shared
`RESERVE.COM`. The default and reservation identities remain unchanged:

- TANDY88.DRV: `ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee`
- RESERVE.COM: `644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8`

The four additional driver identities, sizes and their matching build evidence
are listed in [docs/MODES.MD](docs/MODES.MD#binary-identities).

To reproduce a driver with the repository's MASM 5.10, LINK and resource tools
in DOSBox-X, give each profile a fresh output directory:

```sh
python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/default-build
python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/6404-build --mode 640x200x4
python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/160-build --mode 160x200x16
python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/3204-build --mode 320x200x4
python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/6402-build --mode 640x200x2
python3 src/tandysw/RESERVE.PY --dosbox /path/to/dosbox-x --out /new/reserve-build --cpu 8086_prefetch
```

Omitting `--mode` means `320x200x16`; specifying that value is equivalent.
Each build stages its changes instead of modifying the source baseline. An
unsupported profile or existing output directory is rejected. Check `RESULT.json`,
the 27-object instruction/link audit and the output SHA256; building alone is
not runtime acceptance. All five fresh rebuilds matched the checked-in driver
bytes in [docs/modes/REBUILD.JSON](docs/modes/REBUILD.JSON).

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

The media directory must contain these eight accepted files. The builder accepts
the original SZDD mode-A compressed files under the requested filenames or the
expanded bytes; it checks SHA256 after expansion:

- CGASYS.FON: `baf8fa607806d949dfb6992113ce93494678abdef07783b22222b62e5de28ef4`
- CGAFIX.FON: `b0c043a65e2b551bce3c77d25921394dfd2533f50633bc129abd240c7aeb5f89`
- CGAOEM.FON: `1a86d9e42c73ccefcbc82c822abe8dbcd61cf0116454f213c3a95f4d7436cd0d`
- EGASYS.FON: `8bd307d7886d0f2fdfc1de3da8253e294233d1c757fd9131a66405fca5825b09`
- EGAFIX.FON: `6df45a74e5756dd0746bcee593be9ac4df4a35458c26bf4570b748def2d394cb`
- EGAOEM.FON: `05bd6ef11802bbca20473b0e409116fd8919c5bbcbbbc26b7ee2ea1f33ad23be`
- CGA.GR2: `1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067`
- CGALOGO.LGO: `d9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807`

Only those eight Windows files are included. The three CGA fonts are the only
new Windows dependencies; the original five support files remain unchanged.
The first-party startup image is read from `src/splash/assets/TNDYLOGO.RLE` and
pinned separately. No full OS, installation disks,
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

Verification checks exact members (including all five drivers, eight Windows
support files, the custom splash and completion marker), all 15 binary/support
pins, the full manifest, canonical ZIP metadata, current source payload, and the 360 KB floppy allocation budget.
No external media directory is required. This is the tag-release CI path;
release automation can upload the same verified checked-in ZIP unchanged.

The current pre-final-rebuild measurement is 22 disk files, 320,512 bytes of
1 KB-cluster file allocation plus 6,144 bytes FAT/root/reserved overhead:
**326,656 / 368,640 bytes used, 41,984 bytes free**. This is the measurement in
[docs/modes/PACKAGE.JSON](docs/modes/PACKAGE.JSON), not a promise for a later
archive. Rebuild and reverify after any packaged text change, including
`README.TXT` or `FILE_ID.DIZ`; allocation rounding can change the total.

## Reproduce the custom startup image

The ready disk uses `TNDYLOGO.RLE`, avoiding Setup's cached `CGALOGO.RLE` name.
The unchanged stock `CGALOGO.LGO` decodes the 640x200 two-color RLE4 stream.
The image is reproducible without external fonts or image-generation tools:

```sh
python3 src/splash/tools/BUILD.PY
python3 src/splash/tools/TEST.PY
python3 src/splash/tools/VERIFY.PY src/splash/assets/TNDYLOGO.RLE
```

See [the source guide](src/splash/README.MD) and [runtime evidence](docs/SPLASH.MD).
The normal disk already contains the image; users need none of these tools.

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
python3 src/tandysw/MODECHK.PY --selftest
python3 oemdisk/TESTDOS.PY --dosbox /path/to/dosbox-x --out /new/dos-helper-tests
```

Host unit tests use synthetic media with explicit test-only pins and exercise
complete-release and toolkit contracts, deterministic output, wrong/stale inputs,
manifest/source integrity, media decoding, output preservation and disk capacity.
DOS tests use disposable guests, the accepted reservation helper and executable
sentinels. Those tests establish control flow rather than a real Windows boot;
actual Setup and GUI results are documented in `docs/OEMDISK.MD`. The current
mode package passed 71 host checks and 26 DOS checks; repeated complete builds,
compressed/expanded source media and toolkit staging matched byte for byte.
The oracle self-test covers six profiles, counting the historical cyan/magenta
640x200x4 variant separately from the five current selectable drivers.

The four new runtime profiles passed 374 Windows GDI cases and 33,024,000
pixel comparisons. Follow [docs/MODES.MD](docs/MODES.MD#verification) for the
per-profile evidence, native applications, reproduction boundaries and limitations.

All five profiles have now been selected through native Windows Setup, with a
return from the default to 640x200 four-color. Independent Setup-produced clones
passed 466 cases / 38,912,000 pixels without SYSTEM.INI edits.

**Final emulator acceptance passed:** only-C-drive cold GUI start, installed
Paintbrush reopen and final rebuilt ZIP verification. See
[the cold/reopen record](docs/modes/oem/COLD.JSON) and package evidence.

All edited source and generated DOS text uses CRLF. The native Windows wrapper
was statically reviewed; portable Python and DOS helper execution were tested.
Physical hardware and genuine MS-DOS variants remain separate acceptance checks.
