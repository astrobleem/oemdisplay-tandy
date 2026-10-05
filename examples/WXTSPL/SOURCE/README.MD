# Building and testing WXTSPL 0.2

## DOS build

Use your own Microsoft C 6 installation with its `BIN` on `PATH`, and set
`INCLUDE` and `LIB` to its headers and libraries. From this directory run
`BUILD.BAT`. The build uses `/G0 /AS /W3 /Od`, an 8 KB stack, and `SLIBCE.LIB`.
It runs the built program's SHA-256 self-test. Copy the resulting `WXTSPL.EXE`
to the parent directory only after confirming the intended build.

The qualified runtime SHA-256 is
`772de655c5b949c5fb3a3d17f7e57dc2638cc3cbba1a98eb3782a5cf5d8d9bf7`.
Two builds with the qualified toolchain were byte-identical. A different
compiler or runtime may produce different bytes and needs new qualification.
No compiler, library input, Windows loader or complete `WIN.COM` is included.

## POSIX host safety tests

The host build is for tests, not installation. Compile from this directory:

```sh
cc -x c -DHOST_TEST -D_POSIX_C_SOURCE=200809L \
  -DS_IREAD=S_IRUSR -DS_IWRITE=S_IWUSR -std=c89 -O2 \
  -o wxtspl-host SPLASH.C
```

Run against your own recognized stock Windows 3.0 `WIN.COM` and the existing
first-party Tandy artwork in this repository:

```sh
python3 TEST.PY --exe ./wxtspl-host \
  --stock-win-com /path/to/your/WINDOWS/WIN.COM \
  --old-tandy-rle ../../../src/splash/assets/TNDYLOGO.RLE
```

`--old-tandy-rle` is an explicit path: adjust the example to your checkout's
layout. From `examples/WXTSPL/SOURCE`, the repository-relative path is
`../../../src/splash/assets/TNDYLOGO.RLE`.

The test refuses unrecognized inputs, reads them without changing them, and
operates only on temporary copies. It exercises 1,048 state, refusal,
idempotence and corruption cases, including symlinks and directories.
`--report /new/path/result.json` optionally writes a report; existing reports
are refused. POSIX rename semantics assume no concurrent external writer in
the temporary fixtures. The shipped DOS program uses DOS rename semantics.

`HOST_TEST` also enables named process-interruption checkpoints. These and
host syscall-fault injection were independently tested during qualification;
their evidence totals and limits are in `../QA/README.MD`. Host fault
injection is not proof of physical FAT/media behavior.

## Artwork

`../ART/tools/BUILD.PY` deterministically produces the approved monochrome
artwork and RLE using Python's standard library; Pillow optionally writes PNG
previews. Run `../ART/tools/TEST.PY` for exact pixel/PBM round trips and malformed
input checks. `../ART/assets/ASPECT.PNG` illustrates physical 4:3 aspect;
`../QA/BOOT.PNG` is an actual unedited emulator framebuffer capture.

Revised artwork needs a new explicit hash/output allowlist and qualification;
replacing the RLE alone is deliberately refused by this updater.
