# CGA image sources

These are unretouched decodes of saved video memory from the recorded native
Windows 3.0 runs on IBM XT/CGA emulation: 8088 at 4.77 MHz, 640 KB, IBM CGA
with snow enabled. They are not photographs or complete monitor captures.
Original PNGs retain every logical pixel. The X images only repeat pixels:
4x4 at 160x100, 2x2 at 320x200, and 1x2 at 640x200. These are pixel enlargements,
not simulations of CRT aspect ratio, overscan, blanking or composite output.

| Image | Recorded run / video-memory capture | Logical size | Colors used |
| --- | --- | --- | --- |
| [Program Manager](DESK100.PNG) | native-cga-consumer100-02 / 001.VRM | 160x100 | 4 |
| [Notepad File Open](OPEN100.PNG) | native-cga-consumer100-02 / 006.VRM | 160x100 | 4 |
| [File Manager](FILE100.PNG) | native-cga-filemgr100-02 / 001.VRM | 160x100 | 5 |
| [Windows palette test](PAL100.PNG) | native-cga-filemgr100-02 / 005.VRM | 160x100 | 16 |
| [Four-color-mode File Open](OPEN320.PNG) | native-cga-consumer320-01 / 006.VRM | 320x200 | 3 |
| [Monochrome File Open](OPEN640.PNG) | native-cga-consumer640-02 / 006.VRM | 640x200 | 2 |

The palette frame was drawn by a private Windows GDI test, not inserted into
the image. It contains all16 RGBI indices, including both bright and dark
colors; the small grid exercises adjacent pairs. Program Manager and File
Manager use fewer colors even though the driver mode supports16.

All17 installed files in the 100/640 runs match the published CGA.ZIP exactly.
The320 run used the same selected driver, fonts and helper; its unused old
640 dialog face was subsequently replaced. No image here comes from that
superseded640 font. The public ZIP changes only root README relative to the
final reviewed packet. No capture or runtime was changed for this guide.

[PROOF.JSN](PROOF.JSN) records the public ZIP/member bindings, capture hashes,
RGBI pixel counts and image transformations. The adjacent matching VRM files
are the original raw memory for each PNG; installer receipts preserve the
recorded source. The final native/review records remain in
[qualification](../QUAL/CGA/README.MD), and the earlier developer discussion
is preserved in [the implementation record](../QUAL/CGA/IMPLEMENT.MD).
