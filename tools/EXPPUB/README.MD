# Separate experimental driver downloads

`PACKAGE.PY` reproduces and verifies the 2026-10-18 TEXT80 and PCjr ZIPs.
These are separate from Windows XT rc.6 and the historical DISPLAY3 release.
Existing package bytes, tags, release assets and qualification pins stay fixed.

The runtime source is commit `997e7b910eb4623226b676c1c229aa0dd4e81661`.
`PINS.JSN` is the explicit payload allowlist; `QUALIFY.JSN` records exact
source/build/test identities and the limits of each inherited Windows session.
The packaging script performs no native build, emulator launch or download.

Use the pinned external dependency view described in
[BUILDDEPS](../BUILDDEPS/README.MD). Reproduce the native outputs in a fresh
build root using these output subdirectories (each under an explicit,
bounded `src/xtpan/EMULOCK.PY` slot):

| Build command | Output folder under the build root |
| --- | --- |
| `src/text80/BUILDT80.PY --variant t80` | `t80-2024` |
| `src/text80/BUILDT80.PY --variant t80c` | `t80c-2024` |
| `src/text80/BUILDT80.PY --variant t80pan` | `t80pan-2024` |
| `src/text80/BUILDT80.PY --variant t80vga` | `t80vga-2024` |
| `src/text80/BUILDAPP.PY --app XTPAN --dos-app T80SET` | `textapps` |
| `src/text80/T80FONT.PY` | `textfonts` |
| `src/pcjr/BUILDJR.PY` | `pcjr` |
| `src/pcjr/BUILDCOM.PY --src src/pcjr/JRGUARD.ASM --src experiments/DISPLAY3/JRWIN.ASM` | `jrcom` |
| `src/pcjr/INSTALL/BUILDGR.PY` | `jrgrab` |

Supply each command's documented `--repo`/`--deps`, external `--dosbox`,
and fresh `--out` arguments. These are builder options, not DOS installation
commands. No build input is distributed with the runtime downloads.

```sh
python3 tools/EXPPUB/PACKAGE.PY --builds /scratch/build-root --out /scratch/new-packets
python3 tools/EXPPUB/PACKAGE.PY --verify /scratch/new-packets
python3 tools/EXPPUB/PACKAGE.PY --verify downloads/experimental
```

The PCjr packet passes through the merged `JRPACK.PY`, retaining its original
runtime pins and Setup contract. TEXT80 uses five original XT Pixels font
resources, not Microsoft/ROM glyphs. Drivers and the patched PCjr grabber
retain their DDK derivative notices. Each ZIP includes DOS installation and
recovery instructions, component notices, build evidence and a full manifest.
All runtime member names are uppercase DOS 8.3 names; edited text uses CRLF.
ZIP_STORED, fixed order/timestamps/attributes and explicit members make the
archives byte-for-byte reproducible without zlib-version dependence.

Verification checks exact membership, runtime pins, CRCs, both manifests,
canonical ZIP metadata and current guide/evidence bytes. Changed native bytes
need new evidence and a separately named download; never relax an old pin or
replace an existing released ZIP merely to accept a rebuild.
