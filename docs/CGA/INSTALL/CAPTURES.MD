# CGA installation screenshots

These are genuine DOS screens from a private IBM XT/CGA emulator fixture.
The historical public `CGA.ZIP` and its installer were unmodified. They show
the root package directory, a completed `SETUP C:\WINDOWS 100`, and the
subsequent `WIN /R` launch. The latter was captured in a continuation boot
of the same installation, with installed payloads and INIs unchanged.

| Step | Original image | Enlarged image | Raw capture | Captured text |
| --- | --- | --- | --- | --- |
| Package directory | [FILES.PNG](FILES.PNG) | [FILES2X.PNG](FILES2X.PNG) | [FILES.VRM](FILES.VRM) | [FILES.TXT](FILES.TXT) |
| Successful Setup | [SETUP.PNG](SETUP.PNG) | [SETUP2X.PNG](SETUP2X.PNG) | [SETUP.VRM](SETUP.VRM) | [SETUP.TXT](SETUP.TXT) |
| Windows launch | [START.PNG](START.PNG) | [START2X.PNG](START2X.PNG) | [START.VRM](START.VRM) | [START.TXT](START.TXT) |

The originals decode all 80×25 text cells from the guest's captured B800 video
memory using the exact 8×8 CGA thick font loaded by the emulator. Their logical
size is 640×200. The enlarged images repeat each pixel 2×2. No console text
was retyped or overlaid. These are video-memory decodes, not physical-monitor
photographs or a simulation of CRT aspect ratio. The font ROM is not included.

`PAUSE` and `IF ERRORLEVEL` belong to the capture harness. They let the recorder
stop at each stage and are not additional commands for users to enter.
The success screen shows the final portion of the install log after earlier
lines have scrolled out of the 25-row display.

These captures show the existing-Windows route. They predate `FRESH.EXE`
and the `FRESH640` folder, so the directory image is not a current extraction
layout or evidence of fresh graphical Setup. See [the current guide](../../CGA.MD)
for the fresh-install paths and [its native evidence](../../QUAL/CGAFRESH/README.MD).

## Exact version scope

The capture used the preceding public package:

- `CGA.ZIP`: 414,463 bytes, SHA-256
  `f66bca3c0708923e2ecd9e56fddee5d092149831d68d535e866be212d30dafe9`.
- Root `SETUP.EXE`: 32,265 bytes, SHA-256
  `a02e7ae5f2e3ee7c417fdb47e0b339abd99596c5fd40ebf35013f9ead0c49de5`.
- Selected display: `CGA100.DRV`; the screenshot records that selection and
  the successful install message.

A later package checked when this capture record was written was 460,460 bytes, SHA-256
`1768cffab6a770ee01494fb493c9ffe4e3caf2a41a9617b2ccec7bc9909e37d2`.
It adds the common `PAN` entry and updates helpers and the DOS installer.
All four display-driver files remain byte-identical. The root layout, all four
mode commands, final success message and `WIN /R` launch are unchanged.
File sizes and helper-copy lines in the screenshots therefore differ from a
new installation of that package. Settings use `PAN /SETTINGS`.
These captures do not establish a new native test of the updated installer
or helper bytes.

[PROOF.JSN](PROOF.JSN) records the exact package, installer, source-delivery,
font and capture identities, pixel transformations and completed-session scope.
No Windows/DOS media, installed disk image, emulator or ROM is redistributed.

The [Program Manager image](../DESK100X.PNG) in the guide is the separately
documented earlier fixed-mode capture; see [CGA image sources](../CAPTURES.MD).
