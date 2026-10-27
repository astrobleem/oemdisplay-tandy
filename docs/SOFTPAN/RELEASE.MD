# PCjr and ColorPlus: one Panning application

The current drivers expose a 640x400 desktop through a 320x200, 16-color screen.
Both axes move. The normal driver launcher installs the same Panning application
and selects its backend automatically. See [Panning](../PANNING.MD) for settings,
keyboard controls, memory limits and the standalone PAN package.

| Hardware | Download | Extract | Start Windows |
| --- | --- | --- | --- |
| IBM PCjr | [JRPAN.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/JRPAN.ZIP) | Its JRPAN folder to `C:\JRPAN` | `C:\JRPAN\JRSTART` |
| Plantronics ColorPlus | [CPPAN.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CPPAN.ZIP) | All files to `C:\CPPAN` | `C:\CPPAN\CPWIN` |

Use installed Windows 3.0 real mode in `C:\WINDOWS` with 640 KB. PCjr's DOS
memory driver must already reserve the 32 KB video page; the included guard
checks that reservation before Setup and every start. ColorPlus uses card RAM.

1. Exit Windows and run `INSTALL` from the extracted folder.
2. In Setup choose Display / Other, enter that folder, and select its
   640x400 software-panning entry. Complete changes and return to DOS.
3. Start Windows with the matching command above. Run `PAN /SETTINGS` for controls.

A 128,000-byte shadow retains the larger desktop: 64,000 bytes more than the
previous vertical-only profile. Existing installations of that exact preceding
panning driver upgrade through the normal launcher. Both adapters now use the
same two-axis PAN controls, with no extra startup program to select or copy.
[Current native acceptance and screenshots](../QUAL/PAN/README.MD).
To choose fixed mode, exit Windows, repeat INSTALL and select 320x200 fixed.

[Earlier vertical-driver test records](README.MD) describe the superseded driver;
they are retained as history, not evidence for the new two-axis driver.
