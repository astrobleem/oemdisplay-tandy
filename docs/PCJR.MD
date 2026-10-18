# IBM PCjr driver proposal (TNDYJR): first probe results

Status: **TNDYJR.DRV builds through the pinned BUILD88 pipeline, passes its
audits, and boots Windows 3.0 real mode on DOSBox-X's PCjr machine. A clean
Windows 3.0 Setup with PCjr fonts, a PCjr-safe grabber and fresh groups
passes a scripted session there (see "Clean Windows 3.0 installation").
Not yet run on a real PCjr.** Nothing here changes the shipped TANDY88/TR5
drivers, the WINXT disk, the accepted hashes or the Tandy RESERVE helper.
Every result below is DOSBox / DOSBox-X emulation; no physical PCjr has run
any of it.

## Download and install

**[Download PCJRSET.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/PCJR/PCJRSET.ZIP)**
([checksums and packet details](../downloads/experimental/PCJR/README.MD)).
Extract PCJREXP to `C:\PCJREXP`, then follow its `INSTALL.TXT` for native
Windows 3.0 Setup and the guarded `JRWIN` launch. The packet includes the
pinned driver/guard/launcher, PCjr-safe grabber, original XT Pixels fonts
and static logo. Your own Windows/DOS media supplies the operating system.
The new rebuilds match the clean-install emulator evidence byte for byte;
physical hardware and real PCjr memory expansion remain unqualified.

## Why the PCjr is close

The Tandy 1000 was built as a PCjr clone, and the current 320x200x16 driver
already has the right shape for it:

- It uses BIOS mode 09h, which the PCjr introduced (with 08h and 0Ah).
- All drawing goes to a private four-plane shadow; only the flush routines
  (one site in raw `V1.ASM`, four after TR5 staging) and two cursor routines
  in `TCURSOR.ASM` touch video memory.
- The renderer never programs the video gate array directly, so the
  PCjr/Tandy difference in palette-register data ports (PCjr writes data
  to 3DAh; Tandy uses 3DEh) does not affect it.
- The mode 09h layout is identical: four 8KB banks selected by `y & 3`,
  160 bytes per bank row, two pixels per byte, left pixel in the high nibble.

## The three real differences

**1. B800h is not the framebuffer on a PCjr.** The PCjr's CPU window at
B8000h is one 16KB page, repeated at BC000h. Mode 09h needs 32KB, so the
current driver's B800h writes for banks 2 and 3 would land on top of banks 0
and 1 - the "venetian blinds" effect Tandy programs show on a PCjr. The fix
is to write through the page's *physical* address. The BIOS keeps a copy of
the CRT/CPU page register (port 3DFh) at 40:8Ah; its low three bits give
the displayed page in 16KB units.

**2. The framebuffer is in the middle of DOS memory.** The PCjr's video
RAM is the top of its internal 128KB, not the top of 640KB. With memory
expansion, that page sits under DOS unless a PCjr memory driver keeps it out
of the allocator. The Tandy RESERVE helper deliberately refuses PCjrs.

**3. Identity.** PCjr: F000:FFFE = FDh. Tandy: FFh plus FC00:0000 = 21h.

## Clean Windows 3.0 installation (2026-10-17)

The first boot below reused an AT/EGA Windows install with only
`display.drv` changed. That gap is closed: stock Windows 3.0 Setup installs
a PCjr configuration from scratch, with PCjr-appropriate fonts, a grabber
that handles PCjr video, a clearly labelled Setup choice and fresh Program
Manager groups. **All of it is emulator evidence (DOSBox-X `machine=pcjr`).
Nothing in this section has run on a real PCjr.**

User instructions: [`src/pcjr/INSTALL/INSTALL.TXT`](../src/pcjr/INSTALL/INSTALL.TXT)
(the same file ships in the install folder).

### What the final evidence used

The emulator results in `docs/pcjr/INSTALL` come from committed scripts on
a clean tree; each of `SESSION.JSN`, `CONVERT.JSN`, `MODET.JSN` and the three
`GR*.JSN` records its `source_commit` and `source_tree_dirty: false`.
`SESSION.JSN` is from **commit `9ae44084127fe5d2f0c57ee1e1842d1ee1885573`**; the others are from **commit
`c7144d1ec808eff012d0e5ac2b44e24489e7442d`**. The only change between the two adds the JRHOLDT exit-code
requirement to the session's held-page check (`JRCHK.PY`, `JRSESS.PY`,
`TESTPACK.PY`); the grabber, conversion and self-test runs do not use it. `TOOLS.JSN` is
`src/pcjr/BUILDCOM.PY`'s build record of the test tools (sizes and SHA-256;
it has no commit field); the `JRMODE.COM` and `JRHOLDT.COM` hashes recorded
in the result files match it. The guest files `JRLOG.TXT`, `GUARD0.TXT` and
`HELD.TXT` are copies from the session run.

| Input | Identity |
| --- | --- |
| Windows 3.00 media | PCjs 1.2 MB diskettes, verified against PCjs's own MD5 (`MEDIA.TXT`); 282 pooled files, manifest SHA-256 `342d34b0...` (`win30_manifest_sha256`) |
| Install folder | built by `JRPACK.PY` from this commit; every file's SHA-256 in each result's `packet_sha256` |
| `TNDYJR.DRV`, `JRGUARD.COM`, `JRWIN.COM` | `a29cabba...`, `10e6f01e...`, `18ccaa02...` (release pins) |
| `JRGRAB.GR2` | `2453cd1e...`, 2,159 bytes (`src/pcjr/INSTALL/PINS.JSN`) |
| Test tools | `JRMODE.COM` 11,552 bytes `476dc8d1...`; `JRHOLDT.COM` `23903985...` (`BUILDCOM.PY`, pinned MASM 5.10) |
| Emulator | DOSBox-X 2024.03.01, `machine=pcjr`, 640 KB, `8086_prefetch`, `cycles=fixed 200000`, serial mouse |

**Correction.** Earlier versions of this evidence used a private copy of the
same PCjs diskettes produced by a faulty conversion: 46 files differed,
including `SETUP.EXE` and `SETUP.INF`. `PCJSFLP.PY` now converts the PCjs
JSON and refuses any image whose MD5 differs from the one PCjs records; all
evidence was rerun on the verified images. The retail `CGA.GR2` used for
comparison was not affected.

### The install folder (`C:\PCJREXP`)

`src/pcjr/INSTALL/JRPACK.PY --bin <dir> --out <new>` assembles it and
refuses unless every input matches its pin. Every file is first-party; no
Microsoft file is needed from the packet or committed here:

| File | What | Pin |
| --- | --- | --- |
| `TNDYJR.DRV`, `JRGUARD.COM`, `JRWIN.COM` | the released driver, guard and launcher | `experiments/DISPLAY3/PINS.JSN` (experimental-displays-2026-10-12) |
| `JRGRAB.GR2` | PCjr-safe 286 grabber, built from the DDK CGA grabber (below) | `src/pcjr/INSTALL/PINS.JSN` |
| `XTESYS.FON`, `XTEFIX.FON`, `XTEOEM.FON` | XT Pixels EGA-aspect fonts (MIT), the set the Tandy 320x200 configuration uses | hashes in `JRPACK.PY` |
| `XTSTATIC.LGO`, `WXTSPL01.RLE` | static mode-6 startup logo (MIT); the animated splash programs Tandy palette ports and is not used | hashes in `JRPACK.PY` |
| `OEMSETUP.INF` | one Setup entry: `EXPERIMENTAL IBM PCjr 320x200 16 colors` | checked by `JRPACK.PY` |
| `INSTALL.TXT`, `FONTLIC.TXT`, `LOGOLIC.TXT`, `SHA256.SUM` | guide, licences, hashes | |

`OEMSETUP.INF` names the absolute `C:\PCJREXP` disk path: a relative `.`
made Windows 3.0 Setup ask again for each file. The font row uses the
`133,96,72` aspect, as the Tandy 320x200 configuration does, so Setup
installs the EGA-aspect XT Pixels set; Windows' CGA fonts target 640x200 and
are not installed. `JRPACK.PY` counts **every** entry in the `[display]`
section, whatever its key, and refuses unless there is exactly one, the PCjr
entry.

### Grabbers and DOS programs, every PCjr BIOS mode

`JRGRTEST.PY` runs `JRMODE.COM m` from File > Run for each mode, with only
`286grabber=` changed between runs (`docs/pcjr/INSTALL/GR*.JSN`). JRMODE sets
the mode, draws a pattern through the BIOS, snapshots it by reading it back,
waits, then reads it again and writes `MODE m OK` only if nothing changed.

| Mode | Retail Windows 3.0 `CGA.GR2` (`1fc24254...`) | Unmodified DDK CGA grabber (`310988d7...`) | `JRGRAB.GR2` |
| --- | --- | --- | --- |
| 0, 1 (40x25 text) | switches; **screen not restored** (program data intact) | switches; restored exactly | switches; restored exactly |
| 2, 3 (80x25 text) | switches; **screen not restored** (program data intact) | switches; restored exactly | switches; restored exactly |
| 4, 5 (320x200x4) | switches; restored exactly | switches; restored exactly | switches; restored exactly |
| 6 (640x200x2) | switches; restored exactly | switches; restored exactly | switches; restored exactly |
| 8 (160x200x16, PCjr) | **switches; screen not restored** | refuses; undisturbed | refuses; undisturbed |
| 9 (320x200x16, PCjr) | **switches; program's screen data changed (2,392 cells)** | refuses; undisturbed | refuses; undisturbed |
| 0Ah (640x200x4, PCjr) | **switches; screen not restored** | refuses; undisturbed | refuses; undisturbed |

"Program screen shown" is checked before every switch attempt
(`JRCHK.jrmode_screen`): the 640x400 capture must show JRMODE's pattern for
that mode, with the mode's pixel geometry (a 160-pixel row is 4x2 blocks in
mode 8, 320 is 2x2 in modes 4, 5 and 9, 640 is 1x2 in modes 6 and 0Ah), the
pattern colours, the title and a black background; text modes check all 15
attribute cells. Modes 4/5, 0/1 and 2/3 differ only in colour burst, which
DOSBox-X does not render, so their captures are indistinguishable.

"Restored exactly": after Alt+Tab away and back, one of up to eight
captures equals the screen before (text modes blink a cursor). "Refuses;
undisturbed": Alt+Tab leaves the program on screen, the capture equals the
one before, and the program's own readback finds no change. In every row the
Windows desktop after the program equals the first desktop, and the program
completed. Mode 7 (monochrome) does not exist on a PCjr and was not tested.

**The unmodified DDK build behaves like JRGRAB on this emulator.** That is
not evidence that it is safe: for modes 8, 9 and 0Ah its `GetMode` copies an
`InfoContext` from the bytes that follow its 7-entry table (`IT0`-`IT6`), so
its refusal comes from undesigned data that a rebuild could change. JRGRAB
makes the refusal explicit (`fBadMode`, mode-6 bounds) and takes the mode
from the BIOS on a PCjr instead of the 6845 light-pen measurement. The
retail build, which differs from this DDK revision in seven instructions
(a beep loop, and no Zenith fallback), restores text programs in the wrong
mode here; the DDK revision does not. Which of the seven instructions
accounts for that was not isolated. Whether either build misreads a real
PCjr is untested.

`BUILDGR.PY` builds the DDK grabber twice in DOSBox-X with the pinned MASM
5.10/LINK/EXE2BIN: unmodified (control) and with ten anchored edits. Two
builds gave the same hash. No DDK file is committed.

| Capture | What it shows |
| --- | --- |
| `pcjr/INSTALL/GRJRTXT.PNG` | JRGRAB: `JRMODE 3` text screen after Alt+Tab away and back, identical to before |
| `pcjr/INSTALL/GRCGATXT.PNG` | Retail `CGA.GR2`: the same text screen after returning, shown as graphics |
| `pcjr/INSTALL/GRMODE9.PNG` | `JRMODE.COM 9` in PCjr mode 9 before the switch attempt |
| `pcjr/INSTALL/GRCGAM9.PNG` | Retail `CGA.GR2`: the mode 9 program after switching away and back |
| `pcjr/INSTALL/GRJRM4.PNG` | JRGRAB: CGA mode 4 restored after switching away and back |
| `pcjr/INSTALL/GRJRM8.PNG` | JRGRAB: `JRMODE 8` (160x200x16) as left on screen after the refused switch |
| `pcjr/INSTALL/GRJRMA.PNG` | JRGRAB: `JRMODE A` (640x200x4) as left on screen after the refused switch |

### Scripted install and session

`JRSESS.PY` types everything a user would into the guest; nothing in
`C:\WINDOWS` is edited from the host. Result
`docs/pcjr/INSTALL/SESSION.JSN`: **verdict PASS, 26 of 26 checks**.

| Step | Checked |
| --- | --- |
| Guard | `JRGUARD > C:\GUARD0.TXT` before Setup: its own text "OK, video page is held by a DOS system block." and exit code exactly 0 |
| Install | SETUP from `C:\WIN30SRC`; Display = Other, `C:\PCJREXP`, the PCjr entry; Keyboard = PC/XT (84 keys); no network; optional procedures off; CONFIG/AUTOEXEC changes declined; **Return to DOS** |
| As installed | SYSTEM.INI `display.drv=TNDYJR.DRV`, `286grabber=JRGRAB.GR2`, the three XTE fonts, keyboard `type=1`; installed files equal the packet's; no CGA/EGA display files; **WIN.COM is byte for byte the media's `WIN.CNF` (expanded on the host) + `XTSTATIC.LGO` + `WXTSPL01.RLE`**; fresh Main/Accessories/Games groups; Program Manager's saved window (`32 20 288 160`) and every group window inside 320x200; no CONFIG.SYS/AUTOEXEC.BAT written |
| Session 1 (`JRWIN`) | exact 320x200 desktop; File menu from the keyboard and exact restore; serial mouse to an exact pixel and a click opening the same menu; Notepad text saved byte-exact; Paintbrush box drawn with the mouse, saved, reopened through File > Open with an identical canvas, BMP equal to the screen; COMMAND.COM wrote a file, Alt+Tab away and back restored the text screen exactly, EXIT returned to an identical desktop; Exit Windows |
| Session 2 (`JRWIN`) | desktop identical to session 1's |
| Refusal | `JRHOLDT` keeps the page as an ordinary resident program and must exit 0 (it stays resident only with its block at exactly 1800h; exit 2 would leave the page free and give the same refusal text); `JRWIN > C:\HELD.TXT` must contain exactly JRGUARD's "not reserved by DOS" refusal followed by JRWIN's "guard refused/failed. Windows not started.", with exit code exactly 1 |
| Exit codes | `GUARD 0`, `WIN1 0`, `WIN2 0`, `HOLDT 0`, `HELD 1`, each logged exactly (0-4, 5+) by the harness `C:\JRRC.BAT` |

The guest's own files are kept: `JRLOG.TXT`, `GUARD0.TXT`, `HELD.TXT`.

| Capture | What it shows |
| --- | --- |
| `pcjr/INSTALL/SELECTOR.PNG` | Setup's OEM list after Display = Other, `C:\PCJREXP`: the one labelled PCjr entry |
| `pcjr/INSTALL/LIST.PNG` | Setup's list with the PCjr display, PC/XT keyboard, no network |
| `pcjr/INSTALL/DESKTOP.PNG` | First desktop of the clean install: fresh groups inside Program Manager |
| `pcjr/INSTALL/MOUSE.PNG` | File menu opened by a serial-mouse click at (51,45) |
| `pcjr/INSTALL/NOTEPAD.PNG` | Notepad with the typed keyboard line before saving |
| `pcjr/INSTALL/PBRUSH.PNG` | `C:\JRTEST.BMP` reopened in Paintbrush |
| `pcjr/INSTALL/DOSAWAY.PNG` | Windows while COMMAND.COM is switched away |
| `pcjr/INSTALL/REFUSED.PNG` | `TYPE C:\HELD.TXT` after the refused launch |

### Changing an existing install

`JRCONV.PY` makes a stock Windows 3.0 install (Setup detected CGA:
`cga.drv`, `cga.gr2`, CGA fonts), appends a `[PCjrTest]` section to WIN.INI
from DOS, then runs `JRGUARD > C:\GUARD0.TXT` and `SETUP` in `C:\WINDOWS`,
picks the PCjr entry and keeps Setup's default "make NO changes" at its
CONFIG.SYS question (`pcjr/INSTALL/CONVCFG.PNG`). Result
`docs/pcjr/INSTALL/CONVERT.JSN`: **verdict PASS, 8 of 8**.

- SYSTEM.INI: exactly six entries changed, all Setup's own:
  `display.drv`, `286grabber`, `fonts.fon`, `fixedfon.fon`,
  `oemfonts.fon` and `[boot.description] display.drv`.
- WIN.INI (including the user's section), CONTROL.INI, PROGMAN.INI and the
  three group files are byte-identical.
- The PCjr files are installed; WIN.COM was rebuilt as the media's
  `WIN.CNF` + the static logo; JRGUARD printed its OK (exit 0) and `JRWIN`
  started Windows (exit 0) on an exact 320x200 desktop.

Because PROGMAN.INI is kept, Program Manager comes up at its old CGA
position (`64 20 392 160`), partly off the right edge
(`pcjr/INSTALL/CONVDESK.PNG`). INSTALL.TXT tells the user to maximize or
move it once; a clean install does not have this. No backup or rollback
machinery is added: going back is the same Setup step with the previous
display.

### How the checks avoid false positives

Review found checks that could pass for the wrong reason. Each is now a
pure function in `src/pcjr/INSTALL/JRCHK.PY`, and `TESTPACK.PY` feeds it
the bad cases (no emulator; the CI workflow `pcjrinst.yml` runs them):

- **Refused launch.** Previously any capture that was not a 320x200
  frame passed. Now only JRGUARD's exact refusal text + JRWIN's refusal
  line + exit code 1 passes, and only after JRHOLDT exited 0 (resident at
  exactly 1800h). Rejected in tests: JRWIN's missing-WIN.COM and
  abnormal-exit messages, JRGUARD's "not a PCjr" and "chain not valid"
  refusals, silence, JRWIN's line alone, codes 0, 2, 5+ or none, and
  JRHOLDT codes 1, 2, 5+ or none.
- **OEMSETUP.INF.** Previously only lines starting `TNDYJR` were counted.
  Now every `[display]` entry counts; a second entry with another key, or a
  sole entry with another key, is refused.
- **Static logo.** Previously WIN.COM's size (7,879 bytes) was checked. Now
  its bytes must equal the expanded `WIN.CNF` + the packet's logo files, and
  the installed `SYSTEM\WIN.CNF` must equal the media's. Rejected in tests:
  another logo, a damaged logo, another `WIN.CNF`, and a same-size
  rearrangement the old check accepted. The SZDD expander reproduces the
  retail `CGA.GR2` expansion byte for byte.
- **DOS programs.** `JRMODE` compares against its own first readback, not
  against the BIOS's view of the drawn pattern: DOSBox-X's PCjr BIOS reads
  pixels wrongly in mode 0Ah (the screen itself is exact), which JRMODE
  reports separately as `READ hhhh`. `JRMODET.PY` proves the check works in
  every mode: `JRMODE m X` changes one cell itself and must report
  `BAD 0001` (`docs/pcjr/INSTALL/MODET.JSN`: 20 of 20 as required).
  `jrgrab_expected` is tested against each wrong outcome (PCjr mode
  switched, refused but disturbed, text not restored, CGA mode refused,
  program data changed, desktop changed, program screen not shown).
- **Program screen shown.** Previously any capture that was not the
  desktop counted, including a capture that failed to decode. Now the
  capture must be JRMODE's own screen for the mode (above). Rejected in
  tests: blank, missing and wrong-size captures, single-pixel faults, every
  distinguishable wrong-mode pairing, the desktop; the committed mode 4, 8,
  9 and 0Ah captures pass only for their own mode (mode 4 also as 5).
- **Media.** `PCJSFLP.PY` refuses an image whose MD5 differs from PCjs's;
  the test includes the original conversion defect.

### Reproducing

Private inputs, none committed: the PCjs Windows 3.00 1.2 MB diskette JSON
(`MEDIA.TXT` has the repository commit and every hash); the pinned DDK view
from `tools/BUILDDEPS`; DOSBox-X 2024.03.01; an Xvfb display; the
experimental-displays-2026-10-12 `PCJR.ZIP` files.

    python3 src/pcjr/INSTALL/PCJSFLP.PY <WIN300-1200K-DISK1..5.json> --out <img>
    for n in 1 2 3 4 5; do mcopy -n -m -i <img>/WIN300-1200K-DISK$n.IMG ::/* <win30>/; done
    python3 src/pcjr/INSTALL/BUILDGR.PY --repo <ddk view> --dosbox <dosbox-x> --out <gr>
    python3 src/pcjr/BUILDCOM.PY --deps <inputs> --dosbox <dosbox-x> --out <t> \
        --src src/pcjr/INSTALL/JRMODE.ASM --src src/pcjr/JRGUARD.ASM \
        --src src/pcjr/JRFREET.ASM --src src/pcjr/JRHOLDT.ASM
    python3 src/pcjr/INSTALL/JRPACK.PY --bin <PCJR.ZIP files + JRGRAB.GR2> --out <pk>
    python3 src/pcjr/INSTALL/JRMODET.PY --tools <t> --out <m>
    python3 src/pcjr/INSTALL/JRSESS.PY --packet <pk> --win30 <win30> --tools <t> --out <s>
    python3 src/pcjr/INSTALL/JRGRTEST.PY --installed <s>/C --grabber <GR2> \
        --tools <t> --out <g> [--expect-jrgrab]
    python3 src/pcjr/INSTALL/JRCONV.PY --packet <pk> --win30 <win30> --out <c>
    python3 -B src/pcjr/INSTALL/TESTPACK.PY

`JRGUARD`, `JRFREET` and `JRHOLDT` rebuild to the hashes under "Tools in
src/pcjr". Each emulator script runs under `src/xtpan/EMULOCK.PY`.

### Remaining limits and findings for review

- Emulator only. DOSBox-X's own DOS keeps the video page in a DOS-owned
  block; PC DOS on a real expanded PCjr may not, and JRGUARD will then
  refuse (open item 1 below still applies).
- A DOS program in PCjr modes 8, 9 or 0Ah cannot be switched away from; it
  must be ended to return to Windows.
- The unmodified DDK grabber passes the same emulator matrix as JRGRAB
  (above); choosing JRGRAB rests on its explicit refusal and BIOS mode
  source, which only real hardware can fully test.
- DOSBox-X's PCjr BIOS returns wrong pixel values in mode 0Ah (INT 10h
  0Dh); the displayed image is exact. Real-PCjr BIOS behaviour is unknown.
- Windows 3.0 Setup and some dialogs (File Save As) are wider than 320
  pixels; they work from the keyboard.
- Paintbrush 3.0 does not open a drive-qualified file name given on its
  command line; File > Open works.
- PCjr keyboard hardware, the serial port and timing are not modelled
  faithfully by the emulator and are not claimed. Mouse input was a
  byte-exact Microsoft serial mouse on COM1. Sound was off, so no beep is
  claimed for a refused switch.
- The install folder is not part of any release yet; the released
  `PCJR.ZIP` still documents the display.drv-only change.
- Windows 3.1 is not supported.

## First Windows 3.0 boot on an emulated PCjr

**TNDYJR.DRV runs Windows 3.0 real mode on DOSBox-X `machine=pcjr`.** The
desktop, a dialog, Program Manager and Solitaire draw correctly in 16 colors
with a working mouse cursor; windows open and close; Exit Windows returns to
a clean DOS text screen. A scripted guard, Windows, guard, Windows, guard
cycle (`pcjr/JRCYCLE.BAT`) passed with every JRGUARD returning 0
(`pcjr/JRCYCLE.TXT`). The unmodified TR5 driver in
the same guest shows the expected PCjr "venetian blinds".

| Capture | What it shows |
| --- | --- |
| `pcjr/WINJR01.PNG` | First screen after `JRGUARD` + `WIN /R`: dialog, cursor |
| `pcjr/WINJR02.PNG` | Solitaire running, card art and colors intact |
| `pcjr/WINJR03.PNG` | Solitaire closed, Program Manager redrawn |
| `pcjr/WINJR04.PNG` | Exit Windows dialog |
| `pcjr/WINJR05.PNG` | Back in DOS after exit. Superseded as restart evidence: its post-exit `JRGUARD` ran from `C:\WINDOWS` and was not found ("Bad command or filename") |
| `pcjr/WINJR06.PNG` | Second `WIN /R` typed by hand, **unguarded**; shows only that Windows restarts |
| `pcjr/WINJR08.PNG` | Second Windows session of the guarded cycle |
| `pcjr/WINJR07.PNG` | End of the guarded cycle: third JRGUARD reports the page held by a DOS system block, then the log shows all three guards at exit 0 |
| `pcjr/CTLJR01.PNG` | Control: unmodified TR5 320x200x16 driver, same guest: every other pair of lines lands in the wrong bank |

How it was run (2026-10-10):

- Windows: the public Foxlum/pcjs-wiki `PCDOS320-WIN300-EGA.json` disk linked
  by the Windows XT browser workshop (an AT/EGA PC DOS 3.20 + Windows 3.0
  install), converted with `src/pcjr/PCJSIMG.PY` and extracted with mtools.
  Raw image SHA-256 `f55fe24b...117561`. No Microsoft file is in this
  repository; the guest stayed in a private temporary directory.
- Only change to the install: `display.drv=TNDYJR.DRV` (SHA-256
  `a29cabba...a23c4`) in SYSTEM.INI. Its EGA fonts, EGA grabber, AT keyboard
  type and PS/2-or-serial mouse driver are unchanged.
- DOSBox-X 2024.03.01, `machine=pcjr`, `memsizekb=640`, `cputype=8086_prefetch`,
  `cycles=fixed 200000`, no XMS/EMS/UMB, serial mouse. DOSBox-X's own DOS,
  not PC DOS. First boot: `JRGUARD` then `WIN /R`. Restart evidence: the
  `JRCYCLE.BAT` autoexec, which calls `C:\JRGUARD.COM` by full path before
  each Windows start and after the last exit, stops on any nonzero exit, and
  logs each step to `C:\JRLOG.TXT`. Windows was exited through Exit Windows
  both times.
- Captures are X11 screenshots of the DOSBox-X window under Xvfb (640x400,
  each line doubled), input sent with xdotool.

Expected rough edges from reusing an EGA install, not driver faults: Program
Manager reports its group files as damaged (they were saved at 640x350), and
saved window positions sit partly off the 320x200 screen.

Not covered yet: the PCjr's own keyboard path (input came through DOSBox-X's
keyboard emulation), PC DOS on a real expanded PCjr, Paintbrush save/reopen,
the repository's MODETEST frame oracle (it reads VRAM through B800h and would
need the same physical-page change), a CGA-grabber install, and real hardware.
The install, grabber and Paintbrush items are now covered in emulation by
"Clean Windows 3.0 installation" above.

## Review fixes (2026-10-10)

An external review of the first version found real problems. Fixed:

- **JRGUARD accepted any program's memory.** It passed when any in-use MCB
  covered the page, including a TSR, another program or the launching
  COMMAND.COM, any of which can release or reuse that memory. It now passes
  only when the page lies above the DOS arena or inside one block owned by
  DOS itself (owner 0008h). Demonstrated: with `JRHOLDT` (emulator-only)
  holding 1800h-1FFFh as an ordinary resident program, the old guard
  reported OK (`pcjr/OLDGOUT.TXT`); the new one fails.
- **JRPROBE was destructive on real hardware.** Setting BIOS mode 09h clears
  the page, and the probe then wrote a pattern there, without checking who
  owned it. It now checks the predicted page with the same rule as JRGUARD
  *before* the mode set, writes only to the page it validated, touches video
  on non-PCjr machines only with `/C` (emulator control runs), and exits
  0 = pattern written and dumped, 2 = report only.
- **Test tools reported success on missing data.** JRRUN now records exact
  exit codes (0/1/2/3+), takes expectations (`--expect JRGUARD=1`) and fails
  on any mismatch, missing result or emulator error. JRCHECK fails unless the
  report is complete, the pattern was written, mode 09h was confirmed and both
  dumps are exactly 32KB.
- **JWasm builds.** The DOS tools are now built with the pinned MASM 5.10,
  LINK and DDK EXE2BIN (`BUILDCOM.PY`). MASM 5.10 rejected four conditional
  jumps that JWasm had silently extended; they now branch around near jumps.

## Evidence (DOSBox-X 2024.03.01 and DOSBox 0.74-3, Ubuntu packages)

`src/pcjr/JRPROBE.ASM` records machine identity, BIOS memory, the real MCB
chain and 40:8Ah before/after mode 09h. Only after the safety gate passes does
it write a 320x200x16 pattern with the TANDY88 bank formula through the
physical page and dump the page and the B800h window separately. `JRCHECK.PY`
verifies the dumps on the host without trusting the guest. It accepts a
16KB alias only when that 16KB equals one half of the verified page, so a
blank, open-bus or unrelated window that merely repeats is a FAIL. The four
rows below were re-verified with that rule (`*CHK.JSN`; each window holds
17 distinct byte values). `src/pcjr/CHKTEST.PY` runs both host verifiers
against synthetic good and bad dumps, including all-zero and all-FFh B800h
windows and good TGA-II images under unsafe reports; it needs no emulator.

| Guest | 40:8Ah after mode 9 | Page | Pattern (32,000 bytes) | B800h window |
| --- | --- | --- | --- | --- |
| DOSBox-X `machine=pcjr` | F6h (CRT page 6) | 1800h, held by a DOS-owned (0008h) MCB of exactly 0800h paragraphs | 0 mismatches | 16KB, repeated at BC00h |
| DOSBox 0.74 `machine=pcjr` | F6h | same | 0 mismatches | full 32KB (more lenient than a real PCjr) |
| DOSBox-X `machine=tandy`, `/C` control | F6h | B800h | 0 mismatches | full 32KB; BIOS 624KB, arena ends 9C00h as in ALTMODES.MD |
| DOSBox 0.74 `machine=tandy`, `/C` control | F6h | B800h | 0 mismatches | full 32KB; this build reports 608KB |

The DOSBox-X PCjr result matches the documented PCjr window behavior and is
the one to design against. Writing through the physical segment is correct on
both emulators; writing through B800h is correct on only one of them.

Full matrix, all run with `JRRUN.PY` and explicit expected exit codes; every
row's verdict is PASS on both emulators (`pcjr/*RUN.JSN`, guest output
`pcjr/*OUT.TXT`, probe reports `pcjr/*PRB.TXT`, host checks `pcjr/*CHK.JSN`):

| Scenario (machine) | JRPROBE | JRGUARD | Other |
| --- | --- | --- | --- |
| Page reserved by DOS (pcjr) | 0, pattern verified | 0 | |
| DOS block freed by `JRFREET` (pcjr) | 2, did not set the mode | 1 | |
| Page held by resident `JRHOLDT` (pcjr) | 2, did not set the mode | 1 | old guard: 0 (false pass) |
| `/C` control (tandy) | 0, pattern verified | 1, not a PCjr | T2PROBE 2, unmapped |
| No `/C` (tandy) | 2, untouched | | |

`pcjr/XJRPREV.PNG` is an illustrative decode of the DOSBox-X page dump with a
standard IRGB palette, not an emulator screenshot.

Both emulators' DOS layers pre-reserve the page as a 0008h block. A real PC
DOS on a real expanded PCjr may not, and a PCjr memory driver might reserve
it some other way. JRGUARD is deliberately strict; widening it needs evidence
from real configurations.

## Tools in src/pcjr

**JRGUARD.COM** - read-only pre-Windows check, the PCjr counterpart of the
RESERVE step in the launcher. Exit 0 only if the DOS arena ends at or below
segment 1800h, or one MCB owned by DOS (0008h) covers 1800h-1FFFh. It
shrinks its own allocation first so its own block is never judged.

**JRPATCH.PY / BUILDJR.PY** - the driver change. Three edits, each of which
must match an exact count or nothing is written:

1. a public `video_seg` word (default B800h) in the driver Data segment;
2. in `TEnable`, after INT 10h mode 09h, on a PCjr only,
   `video_seg = (40:8Ah & 6) * 400h`;
3. every VRAM site loads ES with `mov ax,seg video_seg / mov es,ax /
   mov es,es:video_seg` instead of `mov ax,0B800h / mov es,ax`. That is the
   same `seg` idiom the renderer already uses for `shadow_bits`, does not
   depend on DS, and clobbers only AX as before.

After all TR5 port steps the staged renderer has **four** VRAM sites (full
flush, retained-cursor rows, retained-cursor columns, column flush) and the
cursor has two; the raw `V1.ASM` has only one, which is why the build applies
the edits to the staged sources, not to `src/tandysw`. On non-PCjr machines
`video_seg` stays B800h, so the drawing path is today's.

`BUILDJR.PY` runs the view's unchanged `BUILD88.PY` for 320x200x16 and
interposes only between staging and the first assembly:

    python3 tools/BUILDDEPS/DEPS.PY view ... --profile display --out <view>
    python3 src/pcjr/BUILDJR.PY --repo <view> --dosbox <dosbox-x> --out <fresh>

Result (`pcjr/JRRES.JSN`, full BUILD88 report `pcjr/JRBUILD.JSN`):

    TNDYJR.DRV  54,976 bytes
    SHA256 a29cabbaa28b447893cd25d4cf9cf37435332697312fd4fcfcf6f4cddb8a23c4

Two independent builds gave the same hash. As a control, the same pipeline
and emulator (DOSBox-X 2024.03.01 Ubuntu package, not the 2026 nightly in
other records) reproduced the accepted TR5 320x200x16 driver exactly:
54,896 bytes, `33f681b0...6cef61`, matching `docs/TRIAL5/BUILDS.JSN`. The
PCjr build is 80 bytes larger. The original build did not commit the binary; the current Setup packet
linked above supplies the same pinned driver. The listing confirms the 8086 encodings
(`26: 8E 06` for the ES-override load, `D3 E0` for `shl ax,cl`).

**BUILDCOM.PY** builds JRPROBE, JRGUARD, JRFREET, JRHOLDT and T2PROBE with
the pinned MASM 5.10 / LINK / EXE2BIN in DOSBox-X and fails on any severe
error, link/convert error or missing output (`pcjr/COMBUILD.JSN`):

    JRPROBE.COM 548c64188a777bbf4e8e51fbb57955a6287ad2ce07d702c462ba3746eed8e439
    JRGUARD.COM 10e6f01e28a4da32bb80596f8743b02cd367d7619b167b96c962f3eb65eed756
    JRFREET.COM d5924644eb5d383c2bb9d0b5291e8417788055bb682fca821f9041658adff676
    JRHOLDT.COM 23903985c4e96191564c7d46e8c1515b847b5194166bac3881e438ff98ea7109
    T2PROBE.COM c844192ef549c0f52d359ff3a1005e104ca1ca0b990cb6b7275d70a25ba4acaa

JRFREET and JRHOLDT damage DOS's memory bookkeeping on purpose; they are for
emulator negative tests only.

**JRRUN.PY** reproduces a matrix row with an explicit emulator path:

    python3 src/pcjr/BUILDCOM.PY --deps <inputs> --dosbox <dosbox-x> --out <bin>
    python3 src/pcjr/JRRUN.PY --emu dosbox-x --exe <dosbox-x> --machine pcjr \
        --bin <bin> --out <fresh-dir> --cmd JRHOLDT.COM --cmd JRGUARD.COM \
        --cmd JRPROBE.COM --expect JRGUARD=1 --expect JRPROBE=2
    python3 src/pcjr/JRCHECK.PY <fresh-dir-of-a-pattern-run>

## Proposed launcher (not yet in any package)

    @ECHO OFF
    JRGUARD
    IF ERRORLEVEL 1 GOTO FAILED
    WIN /R
    GOTO DONE
    :FAILED
    ECHO PCjr video page is not reserved by DOS. Windows was not started.
    :DONE

## Open items, in order

1. Run `JRPROBE` (report-only unless the page is DOS-reserved) on a real
   PCjr with the owner's actual memory expansion and DOS. Record 40:8Ah and
   the MCB holding 18000h. The guard's fixed 1800h assumption comes from
   emulators only.
2. Decide whether JRGUARD should grow into a reserving helper (RESERVE-style,
   last-fit allocation of exactly 1800h-1FFFh) or keep requiring an existing
   PCjr memory driver. That depends on what item 1 finds.
3. Runtime beyond the clean install (done in emulation: Setup, fonts,
   grabber, Paintbrush save/reopen, DOS program switch): MODETEST
   frame-by-frame checks (after teaching its VRAM reader the physical page),
   cursor edges and ROPs.
4. Keyboard, mouse and speed: the PCjr's keyboard reaches INT 9 through its
   BIOS translation, it has no DMA controller, and RAM in the low 128KB is
   slowed by video contention. Each needs its own Windows check.
5. The animated splash programs the Tandy palette through 3DEh; the PCjr
   install uses the static startup logo until that is ported.
6. Expected support boundary: 320x200x16 only to start. 640x200x4 (mode 0Ah)
   is a later profile; 640x200x16 does not exist on a PCjr.

## Sources

- [Tandy Graphics Adapter (Wikipedia): PCjr 16KB B8000h window aliased at BC000h, venetian-blinds incompatibility](https://en.wikipedia.org/wiki/Tandy_Graphics_Adapter)
- [PCjr video register notes (VGADOC PCJR.TXT): 3DFh page register fields, mode 09h/0Ah bank layout](https://pdos.csail.mit.edu/6.828/2014/readings/hardware/vgadoc/PCJR.TXT)
- [COMPUTE! March 1985, PCjr memory expansion and the video buffer below 128KB](https://atarimagazines.com/compute/issue58/pcjr_memory.html)
