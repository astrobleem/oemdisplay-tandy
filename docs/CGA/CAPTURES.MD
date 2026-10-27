# CGA image sources

These are unretouched decodes of saved video memory from the recorded native
Windows 3.0 runs on IBM XT/CGA emulation: 8088 at 4.77 MHz, 640 KB, IBM CGA
with snow enabled. They are not photographs or complete monitor captures.
Original PNGs retain every logical pixel. The X images only repeat pixels:
4x4 at 160x100, 2x2 at 320x200, and 1x2 at 640x200. These are pixel enlargements,
not simulations of CRT aspect ratio, overscan, blanking or composite output.

| Image | Recorded run / video-memory capture | Logical size | Colors used |
| --- | --- | --- | --- |
| [Paintbrush — Twilight Cove](PAINT100.PNG) | native-cga-paint100-02 / 002.VRM | 160x100 | 16 |
| [Paintbrush palette view](PAINTPAL.PNG) | native-cga-paint100-02 / 004.VRM | 160x100 | 16 |
| [Program Manager](DESK100.PNG) | native-cga-consumer100-02 / 001.VRM | 160x100 | 4 |
| [Notepad File Open](OPEN100.PNG) | native-cga-consumer100-02 / 006.VRM | 160x100 | 4 |
| [File Manager](FILE100.PNG) | native-cga-filemgr100-02 / 001.VRM | 160x100 | 5 |
| [Windows palette test](PAL100.PNG) | native-cga-filemgr100-02 / 005.VRM | 160x100 | 16 |
| [Four-color-mode File Open](OPEN320.PNG) | native-cga-consumer320-01 / 006.VRM | 320x200 | 3 |
| [Monochrome File Open](OPEN640.PNG) | native-cga-consumer640-02 / 006.VRM | 640x200 | 2 |

The Paintbrush image is a fresh native Windows 3.0 capture using the published
CGA100 driver. Paintbrush opened [COVE16.BMP](COVE16.BMP), an original 80x48
pixel-art scene; no app chrome or picture was composited into the capture.
The complete displayed picture matches all 3,840 input pixel indices exactly
and uses all 16 colors independently of the app's palette. The second [palette view](PAINTPLX.PNG) uses the existing Ctrl+Alt+End command
to expose Paintbrush's lower palette. It retains the visible brush cursor
(six pixels over the picture); the main PAINT100 image is the exact match. The
[art source](COVE.PX.JS) uses physical RGBI preview colors; the BMP encodes
brown as Windows logical RGB(128,128,0), which this display renders as brown.

The older palette frame was drawn by a private Windows GDI test, not inserted into
the image. It contains all 16 RGBI indices, including both bright and dark
colors; the small grid exercises adjacent pairs. Program Manager and File
Manager use fewer colors even though the driver mode supports 16.

All 17 installed files in the 100/640 runs, including the fresh Paintbrush run, match the published CGA.ZIP exactly.
The 320 run used the same selected driver, fonts and helper; its unused old
640 dialog face was subsequently replaced. No image here comes from that
superseded 640 font. The public ZIP changes only root README relative to the
final reviewed packet. The fresh Paintbrush run added only input artwork; accepted driver, font and helper bytes were unchanged.

[PROOF.JSN](PROOF.JSN) records the public ZIP/member bindings, capture hashes,
RGBI pixel counts and image transformations. The adjacent matching VRM files
are the original raw memory for each PNG; installer receipts preserve the
recorded source. The final native/review records remain in
[qualification](../QUAL/CGA/README.MD), and the earlier developer discussion
is preserved in [the implementation record](../QUAL/CGA/IMPLEMENT.MD).

## CGAPAN viewport and settings

PANSET.PNG and PANAPPLY.PNG are complete, unretouched frames returned by
the fixed 86Box headless capture API in busy-final2 (022.PNG and
SETTINGS-APPLY.PNG). The first shows the settings window; the second shows
Step 20 rounded to 24 after Apply. Follow and Edge were disabled before the
run to isolate the queued-key test. The screen displays 160x100 logical
pixels; each emulator frame retains its own scaling and border.
PANPAL.PNG is a complete Paintbrush detail capture from that final run.
PANPAINT.PNG reuses the settled pan-paint-4/003.PNG frame: its CGAPAN driver,
fonts and all 18 non-owner installed files match the final packet exactly.
That earlier run used the prior PANCTL owner; its install receipt and raw frame
are retained. Paintbrush opened its stock PARTY.BMP in both runs.
These are actual emulator frames, not composed UI or physical scanout.

All runtime bytes in busy-final2 match the integrated CGA.ZIP. Exact
identities, scope and raw captures are retained in ../QUAL/CGAPAN/FINAL.JSN
and EVIDENCE.ZIP. Earlier settings/edge and paired-driver captures are
retained there as supporting history, with their exact reuse scope. Pointer
edge checks used guest Windows APIs; no physical mouse or hardware claim.
