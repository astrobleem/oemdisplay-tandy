# Original Tandy display-mode work

This note records the implementation boundary while selectable modes are under
development. It is not a support claim for an unreleased binary.

## Historical starting point

The repository already contains [archived win2/TANDYDSP.DRV](https://github.com/astrobleem/oemdisplay-tandy/blob/96ce6971a1757f3c77094322ed82741791c79646/win2/TANDYDSP.DRV), a 25,840-byte Windows 2.x
Tandy display driver. SHA256:
`d593c03e52e338074df3c5c70973197bc61deeb72d615459ad90124afea126e0`.
The accompanying README identifies a Windows 2.03 driver supplied by James
Blackmun, describes Windows 3.0 real-mode use, and says the GRB was renamed
from Windows 2.03 WINOLDAP.GRB. Its NE header identifies a Windows 2.01 target.

The author's [installation video](https://www.youtube.com/watch?v=yNisFBDLXos)
description points to the same TVDOG TANDYDSP archive. This is the genuine
four-color starting point, rather than evidence that no Tandy four-color
Windows driver existed.

Static inspection of the tracked binary shows:

- Real 640 x 200, one bit per plane, two-plane device; four display colors
- BIOS mode 0Ah, saved/restored prior video mode
- Byte-interleaved two-plane addressing across four 8KB banks
- Hardware palette blue, bright red, bright green, white (01h/0Ch/0Ah/0Fh)
- Complete historical drawing, text and cursor entry points
- No Windows 3 DIB conversion exports or modern driver parity claim

The tracked [archived src/tandy4](https://github.com/astrobleem/oemdisplay-tandy/tree/96ce6971a1757f3c77094322ed82741791c79646/src/tandy4) files are byte-identical generic Microsoft one-plane
DDK source, not the source for TANDYDSP. The tracked Ghidra databases contain
imported binary analyses, not a reproducible source build. The binary and
archive entered the repository at commit `1614b56`; this work did not download
or run an unknown third-party archive. Microsoft provenance is retained; no
additional third-party license grant was found in the archive.

## Bounded compatibility control, 2026-10-02

An isolated copy of the existing user-supplied Windows 3.0 installation booted
the unchanged tracked TANDYDSP binary through WIN /R. A standalone metrics
probe completed with:

    SM_CXSCREEN=640, SM_CYSCREEN=200
    HORZRES=640, VERTRES=200
    BITSPIXEL=1, PLANES=2, NUMCOLORS=4
    BIOS_MODE_DECIMAL=10, COMPLETE=1

The runtime used core=normal, cputype=8086_prefetch (the accepted four-byte
8088 prefetch queue), 640KB physical memory, no expanded conventional memory,
and the existing checked RESERVE helper. No BIOS AH=0Dh pixel read was used.
This is metrics/boot evidence only; it is not a full historical-driver GUI,
DIB, save/reopen or clean-OEM-install test. It is also not evidence for the
new source-built profile.

## New source-built profile

The new profile stages geometry, cursor, palette and physical VRAM changes
after the accepted 8088 and DIB transformations. Original DDK sources and the
default candidate05 binary remain unchanged. The default profile was rebuilt
and remains exactly SHA256
`ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee`.

The new 640 x 200 four-color backend deliberately retains four logical DDB
planes for the already-audited software drawing engine. Its private shadow
is 64,000 bytes; NUMCOLORS is four and BITSPIXEL/PLANES describe one bit in
each of four logical bitmap planes. This distinction must be documented,
verified in the actual GDI caps, and reflected consistently by ColorInfo,
brush realization, GetPixel, DDB/DIB input and saved bitmap palettes.

Implementation and runtime tests remain in progress. Do not replace the
accepted driver or claim new OEM selectable-mode support from this note.
