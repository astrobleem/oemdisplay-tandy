# PCjr and ColorPlus: a larger software desktop

Each packet includes a 320x400 desktop viewed through a 320x200, 16-color
screen, plus its fixed 320x200 choice, fonts, grabber, logos and helpers.

| Hardware | Download | Extract | Start Windows |
| --- | --- | --- | --- |
| IBM PCjr | [JRPAN.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/JRPAN.ZIP) | Extract its JRPAN folder to `C:\JRPAN` | `C:\JRPAN\JRSTART` |
| Plantronics ColorPlus | [CPPAN.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CPPAN.ZIP) | Extract all files directly to `C:\CPPAN` | `C:\CPPAN\CPWIN` |

Use installed Windows 3.0 real mode in `C:\WINDOWS` with 640 KB. PCjr's DOS
memory driver must already reserve the 32 KB video page; the included guard
checks that reservation before Setup and every start. ColorPlus uses its card RAM.

1. Exit Windows and run `INSTALL` from the extracted folder.
2. In Setup choose **Display / Other**, enter that folder, and select its
   **320x400 software-panning** entry. Complete changes and return to DOS.
3. Start Windows with the matching command above. In Program Manager File / Run,
   run `PANCFG` from the extracted folder once.

The viewport follows the pointer and newly activated windows. Alt+PgDn pans
down, Alt+PgUp pans up, and Alt+F9 returns to the top. To select fixed mode,
run `PANCFG OFF`, exit Windows, repeat `INSTALL` and select **320x200 fixed**.

Software panning uses 32,000 additional shadow bytes. Native results cover
DOSBox-X PCjr and 86Box XT/Plantronics, rather than physical hardware.
[Test records](README.MD) and [ColorPlus details](../PCP.MD) are separate from installation.
