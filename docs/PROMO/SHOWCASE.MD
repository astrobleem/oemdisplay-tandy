# Windows XT showcase captures

The homepage uses real emulator captures and frames from Chad's earlier video. The hill wallpaper and screen
captures are optional components; the images do not imply that every add-on
is installed by the disk image. No UI was generated or repainted.

| Image | Source and scope |
| --- | --- |
| [Startup](XTWAVE.GIF) | Accepted independent slow-wave recording, native 320x200, steady pane colors and lettering. [Capture provenance](XTWAVE.JSON) and [starter guide](../../examples/WXTSPL/WAVE/README.MD). The rc.3 DOS installer enables the guarded wave for eligible Color mode; other modes retain static startup. |
| [Desktop](../../examples/HILLS/HILL320.PNG) | Actual Windows 3.0 sixteen-color desktop with optional green hill wallpaper and Tandy Start 13; 640x400 emulator output with doubled axes. [Wallpaper guide and capture notes](../../examples/HILLS/README.TXT). |
| [Shutdown](XTEXIT.PNG) | Frame 60 from the existing `moon-cursor-80-final` native `shellsel_000.avi` recording, decoded losslessly from indexed ZMBV; 640x400 DOS text output. This was a direct FINISH artwork test, not a new full Windows exit test. An earlier [normal Windows exit capture](../SHOTS/NIGHT08.PNG) and [lifecycle provenance](../SHOTS/README.MD) remain available. |
| [Buddy Holly animation](https://raw.githubusercontent.com/astrobleem/oemsound-tandy/5411fe5f9c2cccdbe09900a779ebda382a407a74/docs/SHOTS/BUDCAP04.GIF) | Existing BUDCAP 0.4 six-second silent GIF from a genuine native DOSBox-X capture, 320x200, 24 frames. Linked directly to the [Tandy sound companion](https://github.com/astrobleem/oemsound-tandy). [Original capture provenance](https://github.com/astrobleem/oemsound-tandy/blob/5411fe5f9c2cccdbe09900a779ebda382a407a74/docs/SHOTS/README.MD#budcap-04-animated-preview). Reused unchanged; no new video export or runtime test. |
| [Pinball](../../examples/PINBALL/EVIDENCE/V2/SCORING.PNG) | Current V2 game with a live score, native 320x200. [Guide](../../examples/PINBALL/README.MD) and [test record](../../examples/PINBALL/TESTS.MD). |
| [Maze preview](XTMAZE.PNG) | Exact left 320x200 frame from the published [two-frame capture](../../examples/MAZE/GAME/EVIDENCE/320X16.PNG), crop `(2,2,322,202)`, without rescaling or retouching. [Current game guide](../../examples/MAZE/GAME/README.MD). PR #116 is merged, but the disk image retains the older saver; the game is a separate preview. |
| [Starfield](../SHOTS/STARS10.PNG) | Final cursor-fixed build 10, actual idle fast/64-star state. Direct SDL capture, 640x400 with doubled rows from logical 640x200 monochrome, reused unchanged. [Source and native scope](../../experiments/VISPART2/README.MD). |
| [Matrix](../SHOTS/MATRIX.PNG) | Historical on-demand 320x200x16 appearance, decoded from the actual guest framebuffer and verified pixel-for-pixel. Reused unchanged; this still does not verify automatic idle or `/S` behavior. [Source and native scope](../../experiments/VISPART1/README.MD). |
| [Tandinator](../../examples/TANDINAT/SHOTS/320x200x16.PNG) | Actual canonical v0.2 sixteen-color character-guessing frame, displayed at doubled size. [Guide and native scope](../../examples/TANDINAT/README.MD). The separate [0.3.8 experimental download](../../experiments/TANDI11/README.MD) is available; this image does not depict its notebook UI. |

The shutdown recording's direct DOS test returned exit 0 and DONE.TXT with
no bounded stop on October 8, 2026. Selected frame 60 decoded successfully;
later parsing stopped after frame 120, so complete-video decoding is not
claimed. The displayed images are retained screenshots and frames from existing recordings.

## Earlier Windows 3.0 video

The comparison's [Program Manager frame](BF2030.PNG)
is at 20:30.000 (frame 36900, 30 fps). An additional
[Solitaire frame](BF2200.PNG) is at 22:00.000 (frame 39600).
Both are untouched 640x360 decoded images, including the recorded black
borders, from Chad's supplied local original `windows3old.mp4` (43,602,632 bytes).
They are compressed-video frames. Their geometry is preserved.

[Source video](https://www.youtube.com/watch?v=yNisFBDLXos), titled
"Let's Install - Windows 3.0 on a Tandy 1000 EX | 640x200 4 Color Driver",
identifies the older 640x200 four-color setup. The paired [Windows XT Paintbrush capture](PBRUSH16.PNG) shows the actual
320x200 sixteen-color mode, one unobstructed Paintbrush window, a complete
160x100 nearest-neighbor copy of the original hill image, and the full palette.
It is untouched native frame 300; the palette strip contains 16 distinct RGB
colors. [Capture identity](PBRUSH16.JSON). The different modes and recording formats compare appearance;
these stills provide no speed measurements. The supplied local video's identity
is recorded here; byte identity with a remote YouTube rendition is not claimed.

```text
4570c3658dee50c54479b53f33bfd138bc678f77588377334893c35fc58bc221  windows3old.mp4
3c54b37ee138283daa4afae96b3870d934b768c8b916c562ef5a861a6eda1c46  BF2030.PNG
6a3e1d61d5c9ad9841e247ca92a7480337c61be9d3ee9c4524bb68d67a6b10bd  BF2200.PNG
```

## Image identities

Screen-saver image SHA-256 identities:

```text
b1de772388c0fec4ea272acebd096e0254b04a288a4de357cf7cb91d01c25f34  docs/SHOTS/STARS10.PNG
ec544bf5aba64ab508c92a60b70c00185c762c14a0d717b265ec0324b7b4dddc  docs/SHOTS/MATRIX.PNG
```

Buddy Holly GIF SHA-256 (companion-owned asset, referenced unchanged):
`58c9193e3f8454326d1563e215a9972d8e0557cde936f97f1430c6535dbfab99`.

```text
de807eeab5a5840b9df4a722cd81e626f85200f1dd7c0b2420fa36789a1bedd5  PBRUSH16.PNG
ec152976482f94ed1c0e11fa1ad64810be584f9ce19461b3f57ed7ff0e01d975  XTWAVE.GIF
43ced11530f1fba7a354fc6f776ef8e8ad10e4c0a4f47766df2943afa4e1fc7e  examples/HILLS/HILL320.PNG
e234470b54ccdacf61e354c964386fd1d8a5c3744e20617a34d327fdf4843208  XTEXIT.PNG
5363e98f40f7c8a43abf73b4dd22e8fe5a8f8edbf6ce9b683a61ffc1e7bb2ed5  examples/PINBALL/EVIDENCE/V2/SCORING.PNG
52a1d17d669cc4374787b2356b2c90d0cdeffcbb9f8b481f56764a0ffb2345b0  XTMAZE.PNG
c1ee426a871573fd629ea932feb949a33c0a6727e2f881c8768d62f43ad48282  examples/TANDINAT/SHOTS/320x200x16.PNG
```

Shutdown source recording SHA-256:
`53794e8fe7d1815c8b29338d4f03de68ecb3fb6bdc8320514088030147bbdcd5`.
Maze source composite SHA-256:
`44eb774e69c1375a2687a1d56777e3064170360bdcd5fac0d140569689edb7cf`.

[User manual](../USERMAN.MD) · [Project showcase](../../README.md)
