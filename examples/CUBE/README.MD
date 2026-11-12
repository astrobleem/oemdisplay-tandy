# Rotating cube

A Windows 3.0 real-mode / 8088 screen saver with flat illumination,
ordered dithering and a twelve-edge wireframe. This is a local review
candidate; publication is separate.

The renderer uses a 130-byte quarter-wave table, four Q8 rotation products
per frame and eight orthographic vertices. Windows GDI draws into a small
compatible bitmap and copies only its projected bounds. It requires no FPU,
EMS/XMS, raw video layout, driver replacement or full-screen shadow bitmap.
The largest sizing envelope is 224 by 128 pixels; the actual copy is smaller.
Input returns to the message loop between complete frames.

The compact settings panel fits 160 by 100. A candidate Tandy Start adds Cube
to its existing idle policy, preview, busy/ownership checks and shutdown.
Its saver selector also has a compact layout for the 100-line display.
The native DOS installer preserves the original shell/input pair, checks exact kit and
baseline identities, supports undo, and retains existing configuration.
The current accepted shell/runtime packets are preserved separately.

The working source includes an unqualified symmetry optimization; see
[candidate changes, host evidence and pending native checks](OPTIMIZE.MD).
The accepted runtime and its existing qualification remain pinned separately.

See [installation and controls](README.TXT) and [qualification](TESTS.MD).
Source, build commands and developer-only native controllers are in SOURCE.
The source ZIP layout and rebuild prerequisites are in [BUILDSRC.TXT](BUILDSRC.TXT).
No Windows media, installed guest tree, licensed SDK/toolchain or emulator
belongs in either runtime or source packet.

Native builds need an explicit coordinated slot, existing shared emulator
lease, external MSC6/DDK tools and DOSBox-X:

```text
python SOURCE/BUILD.PY --toolchain EXTERNAL-INPUTS --dosbox DOSBOX-X --lease SHARED-LEASE --out FRESH-BUILD
python ../TSHELL/BUILD.PY --toolchain EXTERNAL-INPUTS --dosbox DOSBOX-X --lease SHARED-LEASE --out FRESH-SHELL
python SOURCE/BUILDIN.PY --toolchain EXTERNAL-INPUTS --dosbox DOSBOX-X --lease SHARED-LEASE --out FRESH-INPUT
python SOURCE/BUILDSET.PY --watcom WATCOM --cube FRESH-BUILD/CUBE.EXE --shell FRESH-SHELL/TSHELL.EXE --idle FRESH-INPUT/TSINPUT.DLL --old-shell ACCEPTED-TSHELL.EXE --old-idle ACCEPTED-TSINPUT.DLL --out FRESH-INSTALLER
python SOURCE/RUNHOST.PY --out FRESH-HOST-CHECKS
```

The native controller CUBECTL is developer-only. Its default task exercises
settings, preview, the shell selector and real idle launch. Its `/Q` route
runs Cube's native render/input suite and then exits the private Windows
fixture so DOS can test undo/reinstall. Never install that controller or run
it in a Windows session with user work.

The installer baseline inputs are the first-party `TSHELL.EXE` and `TSINPUT.DLL`
from `distributions/WINXT` at commit
`54ede71df5b569c70fb18a3825caf75f88d0406f`. Their exact sizes, SHA-256 and
CRC-32 values are in `EVIDENCE/BUILD/INSTALL.JSN`. They are already public
project files; consumers use the complete Cube kit. Licensed MSC6/DDK inputs
remain external and are never included in either packet.

CI runs the host math/policy and tamper checks and requires the strict native
receipt gate before assembling review artifacts. It does not run Windows,
replace a native receipt, or publish a release.

## Drawing/copy experiment

See [RENDER.MD](RENDER.MD) for the current unreleased drawing/copy candidate,
controlled native Tandy comparisons and remaining qualification limits.
The earlier geometry-only OPTIMIZE.MD record is historical.
The tested unreleased source now lives in
[experiments/CUBEOPT](../../experiments/CUBEOPT/README.MD); this directory
retains the complete accepted source/runtime/receipt closure.
