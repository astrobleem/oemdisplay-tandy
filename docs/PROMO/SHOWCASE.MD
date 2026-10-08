# Windows XT showcase captures

The homepage uses real emulator captures. The hill wallpaper and screen
captures are optional components; the images do not imply that every add-on
is installed by the disk image. No UI was generated or repainted.

| Image | Source and scope |
| --- | --- |
| [Startup](XTWAVE.GIF) | Accepted independent slow-wave recording, native 320x200, steady pane colors and lettering. [Capture provenance](XTWAVE.JSON) and [starter guide](../../examples/WXTSPL/WAVE/README.MD). The disk image still uses static startup. |
| [Desktop](../../examples/HILLS/HILL320.PNG) | Actual Windows 3.0 sixteen-color desktop with optional green hill wallpaper and Tandy Start 13; 640x400 emulator output with doubled axes. [Wallpaper guide and capture notes](../../examples/HILLS/README.TXT). |
| [Shutdown](XTEXIT.PNG) | Frame 60 from the existing `moon-cursor-80-final` native `shellsel_000.avi` recording, decoded losslessly from indexed ZMBV; 640x400 DOS text output. This was a direct FINISH artwork test, not a new full Windows exit test. An earlier [normal Windows exit capture](../SHOTS/NIGHT08.PNG) and [lifecycle provenance](../SHOTS/README.MD) remain available. |
| [Pinball](../../examples/PINBALL/EVIDENCE/V2/SCORING.PNG) | Current V2 game with a live score, native 320x200. [Guide](../../examples/PINBALL/README.MD) and [test record](../../examples/PINBALL/TESTS.MD). |
| [Maze preview](XTMAZE.PNG) | Exact left 320x200 frame from the published [two-frame capture](../../examples/MAZE/GAME/EVIDENCE/320X16.PNG), crop `(2,2,322,202)`, without rescaling or retouching. [Current game guide](../../examples/MAZE/GAME/README.MD). PR #116 is merged, but the disk image retains the older saver; the game is a separate preview. |
| [Cookie Clicker](../../examples/COOKIE/EVIDENCE/baseline/LOADED.PNG) | Actual saved-state capture with 39 cookies and one cookie per second, native 320x200. [Guide](../../examples/COOKIE/README.MD) and [tests](../../examples/COOKIE/TESTS.MD). |

The shutdown recording's direct DOS test returned exit 0 and DONE.TXT with
no bounded stop on October 8, 2026. Selected frame 60 decoded successfully;
later parsing stopped after frame 120, so complete-video decoding is not
claimed. No new guest was launched to create these showcase images.

## Image identities

```text
ec152976482f94ed1c0e11fa1ad64810be584f9ce19461b3f57ed7ff0e01d975  XTWAVE.GIF
43ced11530f1fba7a354fc6f776ef8e8ad10e4c0a4f47766df2943afa4e1fc7e  examples/HILLS/HILL320.PNG
e234470b54ccdacf61e354c964386fd1d8a5c3744e20617a34d327fdf4843208  XTEXIT.PNG
5363e98f40f7c8a43abf73b4dd22e8fe5a8f8edbf6ce9b683a61ffc1e7bb2ed5  examples/PINBALL/EVIDENCE/V2/SCORING.PNG
52a1d17d669cc4374787b2356b2c90d0cdeffcbb9f8b481f56764a0ffb2345b0  XTMAZE.PNG
570129cd15d2ab64d8a10ae6dfb06a8343a4a4713bb9319d10e90fc92c491f25  examples/COOKIE/EVIDENCE/baseline/LOADED.PNG
```

Shutdown source recording SHA-256:
`53794e8fe7d1815c8b29338d4f03de68ecb3fb6bdc8320514088030147bbdcd5`.
Maze source composite SHA-256:
`44eb774e69c1375a2687a1d56777e3064170360bdcd5fac0d140569689edb7cf`.

[User manual](../USERMAN.MD) · [Project showcase](../../README.md)
