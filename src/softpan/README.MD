# Software panning candidates

The opt-in PCjr candidate presents a 320x400, 16-color logical desktop through
a 320x200 viewport. It composes the current staged BUILD88 renderer, PCjr
physical video-page mapping and XTPAN software clipping. Every pan converts
the viewport from the shadow. The video start-address registers are not used.
The viewport resets on every actual Enable and Disable.

The four-plane shadow is 64,000 bytes, 32,000 more than the fixed driver.
The hardware video page remains 32 KB. Original profiles, installers and
accepted driver bytes are untouched. The compact journal and RLE corrections
from main remain in the source build.

## Build and run

Use the existing pinned dependency view described in tools/BUILDDEPS. All
outputs must be fresh. WINRUN.PY uses the existing shared Windows emulator
lease, checks process inventory, bounds each child and stops only its own
children. It never creates or replaces the shared lease file.

```
python src/softpan/BUILDSP.PY --repo VIEW --dosbox DOSBOX --out JBUILD
python src/softpan/BUILDAPP.PY --repo VIEW --dosbox DOSBOX --out APPS
python src/softpan/RUNTEST.PY --windows PRIVATE_WINDOWS --build APPS --driver JBUILD/JRPAN.DRV --dosbox DOSBOX --out JRUN
python src/softpan/SPCHK.PY JRUN/CROOT/RUN1 --driver JBUILD/JRPAN.DRV
python src/softpan/SPCHK.PY JRUN/CROOT/RUN2 --driver JBUILD/JRPAN.DRV
python src/softpan/PACKSP.PY --driver JBUILD/JRPAN.DRV --apps APPS --out JRPACKET
```

RUNTEST clones an owned Windows installation into a private test folder and
selects the test shell there. That test setup does not qualify native Setup.
The packet supplies a normal OEMSETUP selection, fonts, the PCjr grabber,
static startup logo, memory guard, guarded launcher and XTPAN helper. Its
INSTALL.TXT provides installation and return-to-fixed-driver instructions.
PANCFG enables/removes the helper without manual WIN.INI editing and keeps
other startup entries. It finds XTPAN.EXE beside its own executable.

## Evidence scope

SPTEST exercises exact and clamped viewport positions, drawing while the
target lies outside the viewport, DDB and DIB transfers, text, clipping,
screen copies, ScrollDC, cursors at both viewport edges, drawing under the
cursor, repeated pans, helper start/follow/stop and two Windows exits.
SPCHK compares every visible pixel and unused video-bank byte. Text shape
uses a separately rendered memory bitmap; all other geometry and cursor
composition have independent expectations. PNGs are decoded raw VRAM
captures, not host window screenshots. Timing at fixed emulator cycles is
functional evidence only.

The ColorPlus compositor is selected explicitly with `--adapter colorplus`.
It keeps the adapter's two planes, even/odd rows and per-plane cursor
retention footprint. It passes the same two-session Windows pixel suite on
the existing 86Box 640 KB XT/ColorPlus machine with PC DOS 3.20. RAMTEST also
executes its staged FlushRows and conversion macros against guarded RAM.

RUN86 reads the partition offset and CHS geometry from the supplied raw boot
image. Use the existing PC DOS 3.20 fixture used by the earlier fixed-driver
qualification. The previous boot image failed before the shell with both
accepted and panned drivers; changing to the compatible DOS boot fixture
resolved that failure without a driver change. Windows support files stay
the same. REPLAY86 performs this one-driver comparison on a copied guest.
Both runners capture closed session logs and raw frames from the host while
the CPU is paused. They do not rely on DOS COPY directory syntax.

PACKCP makes the separate local ColorPlus packet. Supply the unchanged
accepted PCP3216.DRV as --fixed, alongside --driver, --apps and --out.
The grabber defaults to the supplied root CGA.GR2, expanded on the host.
Its native Setup choices
include the panned driver and the accepted fixed rollback driver. It uses
CPWIN, with no shared-memory reservation helper. The local packet is not a
public release and includes no complete operating-system media.

Neither candidate is physical hardware qualification or hardware panning.
No accepted package is replaced by these builders.

The developer-only RUNUI86.PY harness takes --deps (PyFatFS), --control
(the existing debugger/headless API root), --emulator and --roms paths.
It uses the caller-configured emulator runtime environment. These paths
are local inputs; none is required by the DOS-native installation kits.
Before developer emulator builds/runs, set TANDY_EMULATOR_LOCK to the
existing coordinator-provided shared lease file. A missing setting is an
error; the runner never creates a replacement lease.
