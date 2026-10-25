# PCjr and ColorPlus: a larger software desktop

Each kit provides a **320x400 Windows desktop through a 320x200, 16-color
viewport**, with an included helper and fixed-driver switch-back.

| Your adapter | Download | Folder | Start Windows |
| --- | --- | --- | --- |
| IBM PCjr | [JRPAN.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-softpan-2026-10-24/JRPAN.ZIP) | `C:\JRPAN` | `C:\JRPAN\JRSTART` |
| Plantronics ColorPlus | [CPPAN.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-softpan-2026-10-24/CPPAN.ZIP) | `C:\CPPAN` | `C:\CPPAN\CPWIN` |

Use an existing Windows 3.0 real-mode installation in `C:\WINDOWS`.
Extract the matching ZIP to `C:\`, exit Windows, and run `INSTALL` from
the kit's folder. In Setup choose **Display → Other**, enter that same
folder, and select the **320x400 software-panning** entry. Return to DOS
and start Windows with the command in the table. In Program Manager's
**File → Run**, run `PANCFG` from the kit's folder.

The helper follows the pointer and newly activated windows. Alt+PgDn pans
down; Alt+PgUp pans up; Alt+F9 returns to the top.

To switch back, run `PANCFG OFF` from Windows, exit, and run the kit's
`INSTALL` again. Choose its **320x200 fixed (rollback)** entry. The same
start command continues to work.

PCjr's DOS memory driver must reserve the 32 KB video page; the included
guard checks it before Setup and each start. Both downloads include their
grabber, fonts, logos and helper programs. No manual
checksums, file searches or INI editing are required.

The shadow uses 64,000 bytes, 32,000 more than fixed mode. These are software
copies, with Windows evidence from DOSBox-X PCjr and 86Box XT/Plantronics,
each with 640 KB RAM. They do not claim hardware panning or physical-machine
qualification. [Qualification and captures](README.MD).
