# Unified panning integration

The owners remain separate: XTPAN for vertical framebuffers and its existing fixed
window workspace; XYCTL for HPXY and its existing fixed fallback; PANCTL for
CGAPAN; CGACTL for ordinary CGA. PANCFG is the common configuration entry.
Adapter drawing and memory ownership remain in their existing backends.

`src/panui` holds one adaptive settings layout, the bounded queued-key DLL/client,
owner routing, target arithmetic and startup token editing. The 31-command usable
queue posts one wake and drains/coalesces in the owner; hooks never draw.
No extra resident broker is installed. PANCFG is transient.

Build with `BUILD.PY --toolchain <explicit C6/DDK view> --dosbox <DOSBox-X>
--lease <existing shared lease> --watcom <managed Watcom> --out <new directory>`.
`PREPARE.PY` stages private native installers and expanded packets for acceptance.
Neither command qualifies runtime behavior. External compiler/OS/ROM inputs stay
outside this repository and public packets. Follow ../../BUILDING.MD and AGENTS.md.

`PUBLISH.PY` packages only the separately accepted helper and native installer
bytes. It refuses incomplete native coverage or independent review. The preserved
BASE packets and src/panui/LEGACY.ZIP keep preceding accepted binary/source
qualification intact. Current consumer packages contain no Python or nested ZIP.
Native verification records and real captures belong under docs/QUAL/UPAN.

Measured on the 640KB native fixtures, XTPAN plus PANKEY uses 26,336 bytes while
active; both PCjr and the fixed window workspace returned that amount on OFF.
PANKEY's fixed code is 1,301 bytes and fixed data 288 bytes (2,085-byte NE file).
XTPAN plus PANKEY occupies 29,444 disk bytes, versus 29,199 for the preceding
XTPAN alone. PANCFG is 11,281 bytes and exits after forwarding/configuring.
See docs/QUAL/UPAN/COSTS.JSN for exact identities and measurements. Unused
adapter owners are installed files, not additional resident tasks.

The core also fixes CPSET compatibility with the current grabber metadata:
APPLY accepts its exact 49848-byte CRC-checked variant and migrates only an owned
same-path 49840-byte readiness marker after installed-system checks. Foreign
markers and changed metadata remain refused. BASE/CPSET.C retains the exact
preceding shipped source; the driver/grabber payloads remain unchanged.
