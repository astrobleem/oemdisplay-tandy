# Original Setup-compatible static logo (rc.6)

XTSTATIC.LGO is an independently written MIT 8086 module. It replaces
CGALOGO.LGO's renderer in Windows Setup's static WIN.COM construction.
It consumes the existing original WXTSPL01.RLE, preserving the accepted
static artwork. CONTRACT.MD records the measured interface, memory/state
bounds and Windows loader limitations. No Microsoft code is copied.

This revision starts from rc.5. The slow Color wave, wrapper, reservation,
seven original fonts, driver binaries and Windows kernel remain unchanged.
Windows Setup will construct WIN.COM from owned WIN.CNF + XTSTATIC.LGO +
WXTSPL01.RLE. The separate slow-wave XTTEST.COM still uses WIN.CNF + the
accepted original XTLOGO.LGO. Both routes retain the owned Windows loader.

Build on a modern host using explicitly supplied existing OpenWatcom tools:

    python tools/XTLOGO/BUILD.PY --out NEW-DIRECTORY --wasm PATH/wasm.exe --wlink PATH/wlink.exe
    python tools/XTLOGO/TEST.PY --out NEW-DIRECTORY

Two independent assemblies produced identical 361-byte LGO files, SHA-256
995d71e3626de64c8fe21bc1f037e0dece0853d4f0d09082bf607b2d237b37ef.
HOST640.PNG is a host artwork specimen. It is not a native screenshot or
proof that Windows Setup has loaded the new module.

TEST.PY --cpu runs actual module instructions under optional Unicorn 2.1.3
with synthetic BIOS services. That is host CPU QA, not Windows/native QA.
It checks exact frame pixels, ABI state, relocated/repeated hide, unsupported
entry state and malformed input. Follow emulator allocation requirements
before executing emulator-based tests. Structural checks do not execute it.

INTEG.PY prepared this isolated source revision with distinct XTSTATIC.LGO
OEM records and original runtime pins. TINST/PREPXT and diagnostic variants were rebuilt with the approved private
MSC6 toolchain. Installer pins were regenerated, PREPXT was rebuilt against
them, and HELPER.SHA now binds the resulting helper. Host package checks pass.
The final native gates passed, including Setup 6402/TEXT, exact common-loader
resources, unchanged wave and DOS return. QUALIFICATION.JSON binds accepted
evidence; earlier NATIVE-CHECKPOINT records remain historical. Publication
uses the strict rc.6 source/runtime/evidence guard in tools/FLASHDISK/PUBLISH.PY.

Only CGA.GR2 remains an own-media support
file. Existing DOS/Windows, SYSTEM/WIN.CNF, Setup, kernel and the other
non-font Windows components are still required. The module cannot correct
WIN.CNF's existing branch that skips hide on a nonzero kernel exit. CGA
grabber/kernel/loader replacement is outside this phase.

The rc.6 public release is authorized. Installed Windows and CF are not
modified by these host tools. Final emulator qualification and private
staging are complete. Current documentation pins were host-refreshed while
preserving the measured implementation and all native/failure evidence.
