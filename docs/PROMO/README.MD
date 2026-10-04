# Project promotional artwork

These retro-style promotional mockups are illustrative art, not photographs
of a tested physical installation or official Tandy/Microsoft packaging.
The WOW poster's monitor uses an authentic native emulator screenshot; its
surrounding computer scene is artwork. Verified software scope remains
Windows 3.0 real mode.

## Corrected 16 COLORS. WOW!

[16WOW.WEBP](16WOW.WEBP), 1448x1086, 221,620 bytes. The recovered final
artwork retains the three-bar RGB monitor badge, black 5 1/4-inch floppy with
handwritten label, and Windows 3.0 headline. The monitor power LED is red.

The screen is a deterministic nearest-neighbor perspective composite of the
[existing native Paintbrush capture](../tandy-dib-roundtrip.png), originally
320x200. It shows actual Windows 3.0 real-mode rendering and the 16-color
bitmap roundtrip on the Tandy driver. No UI was regenerated or retyped.
The CRT edge mask fits the pictured curved glass. This geometry fitting and
the later WebP encoding resample the displayed image; the linked source
remains unchanged. See [original test scope](../../src/tandysw/DIB88.MD).

Only the screen surface and 32 LED pixels changed from the corrected base.
The badge, floppy and headline were checked byte-identical before web
encoding. No new runtime or physical-machine test is claimed by this edit.

- Corrected base PNG SHA256:
  3e027ac2c3e655b9113921d70daf860d9fcff383003ca072d89dc4c58313b9b2
- Original native screenshot SHA256:
  cbefffc81cec457f84406031421b40cb020a7712e53e926c0f2731a6e9069703
- Final composite PNG SHA256:
  3971f44495ca1d3a8d4f81c711a7f4337ab12c7d9af4b0d250e7ba5277d8e5c9
- Current web copy SHA256:
  49b436116ab19c7637f657ef1501417515f402685c16c780a653373c02766b16

The web copy preserves full dimensions/composition, uses WebP quality 88 and
strips metadata. The original artwork and earlier versions remain preserved.

## Windows XT concept box (unchanged)

[WINXTBOX.WEBP](WINXTBOX.WEBP), 1122x1402, 189,682 bytes.
Original PNG SHA256:
9e42c4b34760771659a80d9677637901cf52c0b26c6b2bb279a2609602b22aa7
Web copy SHA256:
7cc3c851621c3db390ceb03d8b8124e825a2489bc471c2cbeded1ec12dfde00d
