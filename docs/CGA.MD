# IBM CGA display for Windows 3.0


**[Download CGA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CGA.ZIP)**

Three fixed display choices share one native DOS installer: **160x100 in 16
RGBI colors**, **320x200 in black/bright cyan/magenta/white**, and **640x200
monochrome**. The packet includes compact fonts, controls and dialog faces.
It targets IBM CGA RGBI, an existing Windows 3.0 real-mode installation,
DOS 3.3+ and normal 640 KB. Physical IBM cards/CRTCs/monitor scanout remain
unqualified; clones, composite, PCjr, Tandy and EGA/VGA are separate targets.

Extract the whole ZIP. Keep root `SETUP.EXE`, `README.TXT` and the expanded
`CGA` folder together. Exit Windows completely, then run:

```text
SETUP C:\WINDOWS 100
```

Use your actual Windows path. Choose `100`, `320` or `640`; wait for success,
change to the Windows directory and run `WIN /R`. Changing mode requires exit
and SETUP again. The root installer registers all selected dialog fonts and
controls; the OEM descriptor alone does not complete this installation.
No Python, manual INI changes, extra font media or support-file gathering is
required. Windows itself is not included.

At 160x100, Ctrl+Alt+arrows moves the window workspace, Ctrl+Alt+Home recovers
its origin and Ctrl+Alt+End exposes the active frame's bottom/right. The shared
placement helper also exposes clipped control groups; it does not change
Windows logical geometry. Five-row proportional ASCII faces and six-row
controls reduce the space needed. Unsupported extended characters use boxes.
320/640 startup makes disabled labels readable, then the helper exits.

Keep the packet for `SETUP UNDO C:\WINDOWS`. UNDO restores this installer's
settings while preserving unrelated edits and changed/referenced files.
`SETUP RESTORE C:\WINDOWS` explicitly restores whole saved INIs and discards
later INI edits; use it only for that intended recovery. See the included
[full DOS instructions](../downloads/experimental/CGA/README.TXT).

All three modes passed actual native SETUP, mode switching, dialogs, exact
file saves, palette/drawing/cursor tests and ordinary DOS return in IBM XT/CGA
emulation. Populated File Manager views passed at 160x100 and 640x200.
A DOS-command return is a smoke check, not general DOS/PrintScreen coverage.
The 160x100 access policy blanks video around VRAM writes; physical snow,
flicker and performance remain to be measured. No CGA speedup is promised.
[Final qualification and independent review](QUAL/CGA/README.MD) and
[source/build guide](../src/cga/README.MD) retain the exact evidence scope.

## Original coverage audit and implementation record

Audit base: oemdisplay-tandy main `09238b7dbada62047601138291fa940b77426752`,
including the current-guidance correction `679d363d`. The companion
text-mode-windows main `b24a1b118ec730bf8266051e513d81f72057d43d` contains
the TEXT80 landing-page README; the implementation is in this repository.
Neither repository supplies a 160x100 driver at that audit base. This is not
a claim of historical novelty or of absence in other Windows projects.

## Existing coverage

| Existing source | Actual scope at audit |
| --- | --- |
| `src/text80/`, `src/txt40/` | Text presentation over TR5; TEXT80 has hints, snapshots, native DOS transactions and compact text-grid resources. They are not a 160x100 pixel backend. |
| `src/tandysw/MODEEXT.PY` | 160x200x16 Tandy BIOS 08h, 320x200x4 BIOS 04h with black/bright cyan/magenta/white, 640x200x2 BIOS 06h black/white. Two 8192-byte VRAM banks, 80 visible bytes/scanline. Existing evidence is Tandy scoped. |
| `src/tandysw/MODEPROF.PY` | Five fixed profiles; four logical DDB planes even at reduced physical depth. Widths 160/320/640 use 16/32/64 KB shadows at 200 rows. |
| `REPCOPY88.PY`, `BYTECOL.PY`, `CURKEEP.PY`, `OUTROWS.PY`, `WIDESCAN.PY` | Existing interrupt-safe copies and synchronous bounded redraw/cursor paths. Reused, not a new optimization claim. |
| `COMPACT.PY`, `tools/XTFONTS/` | Original fonts/serializer and 160x200 compact controls. Eight-row existing controls consume too much of a 100-row screen. |

Stock Windows' ordinary CGA support and these repository profiles must not be
confused with the new low-resolution 16-color candidate. Physical low-resolution
reports in STATUS.MD have unconfirmed exact mode/bytes, not CGA100 qualification.

## Candidate architecture and primary references

[IBM's CGA manual](https://minuszerodegrees.net/oa/OA%20-%20IBM%20Color%20Graphics%20Monitor%20Adapter%20%28CGA%29.pdf)
lists 160x100/16 at printed page 9, requiring 16,000 adapter bytes. Printed
pages 17 and 19-21 document CRTC values, blink/background intensity, video
disable, safe-access status and mode sequencing. Its page-20 note calls for
special programming and a 40x25 setup; it does not publish a complete 160x100
register/character recipe. The candidate must not be described as that exact
IBM recipe.

The candidate uses 80 columns of DEh right-half-block characters, two scanlines
per character row, 100 rows. Left pixel is the attribute's background/high
nibble; right pixel is its foreground/low nibble. Blink is off (3D8h=09h), so
both halves retain all 16 RGBI indices. Characters are written as well as
attributes on every flush, preserving full shadow-resync behavior.

The derived CRTC table combines IBM's 80-column horizontal table with its
graphics vertical table: `71 50 5A 0A 7F 06 64 70 02 01`, then hardware cursor
off and zero start/cursor addresses. This preserves 262 scanlines/frame and
vertical sync at line 224. The
[Motorola MC6845 data sheet](https://bitsavers.trailing-edge.com/components/motorola/_dataSheets/6845.pdf),
register descriptions/table 2, establishes the row/scanline and total-adjust
units used in that calculation. No zero-width timing or exploratory port
sweeping is used. Physical scanout qualification remains separate from the emulator results.

Target is explicitly IBM CGA with the documented MC6845 behavior and RGBI.
No clone/CRTC-variant, EGA/VGA, composite-video, PCjr or Tandy compatibility is
inferred. IBM's character-ROM font jumper and adapter revisions belong in the
hardware matrix. PCjr/Tandy BIOS 08h 160x200 is a different mode and memory
architecture. The implementation does not probe/detect those machines.

At a 4:3 active picture, pixel width/height is `(4/3)/(160/100)=5/6`;
square-pixel images look too wide. Actual monitor active-area/overscan can
change this. GDI style distances/aspect and the new font dpi are adapted
together. Font specimens show both raw pixels and a labeled 4:3 approximation.

## Source work and resource budget

`src/cga/STAGECGA.PY` retains the exact BUILD88 pipeline and pins. Normal
modes stage byte-identically. `CGA100.PY` changes only the final 160-wide stage:
8,000-byte R/G/B/I shadow, BITMAP/GDI/DIB bounds, 100-row conversion, linear
160-byte VRAM rows, cursor offsets and full-pair save/restore. The maximum
32x32 cursor at odd X needs 1,088 saved bytes; that bound is checked. The
other modes' source, resources and accepted binaries are untouched.

`CGA100E.ASM` contains the derived mode entry. `CGAVRAM.ASM` conservatively
disables video around every converter/cursor VRAM access; nested access keeps
video blank until the outer end. Only bounded depth/port changes mask
interrupts; conversion has no polling loop or long CLI region. Blanking can
flicker and is not a proven fast path. BIOS mode restoration additionally
restores the prior text page, cursor shape and position. Ordinary DOS exit has the native evidence below; Windows re-entry and
full-screen DOS/grabber interactions remain separate tests.

`CGAFONT.PY` reuses XT Pixels' FNT/FON writer for original five-row
proportional System/Helv, 4x6 fixed/OEM and 4x5 Courier ASCII faces;
`CGAUI.PY` reuses the compact BMP serializer for six-row controls. These are
first candidates, not proof of native text quality or complete charset support.
`CGAMODEL.PY` validates host/reference VRAM captures; it is not a new renderer.
`BUILDCGA.PY` wraps BUILD88 with the existing shared watchdog/lease runner.
The `cga` source-view profile closes over those tools and the font kit.

## Consumer integration source

The renderer/font checkpoint is preserved at `32d89b42`. Further work is on
`work/cga-install`. `src/cga/SETUP.C` provides the expanded root-SETUP/README/CGA
folder pattern for an existing Windows installation. `CGASET.PY` adapts the
exact T80SET transaction in build output without changing shared source or
published installer runtime. It selects display/fonts and private CGAGRAB.GR2
together; 160x100 also registers the small Helv/Courier faces and compact borders.

Native copy code checks compiled size/CRC pins, refuses unrelated collisions
and records only its own new files. UNDO preserves unrelated later INI edits
and changed/referenced files. Explicit whole-INI RESTORE and a completed-undo
marker make this packet's interrupted copy/cleanup retryable. No historical
formats or directory-wide cleanup are added.

Host fault tests found and fixed a failed deletion leaving an INI temporary
after its copy journal was removed. They also caught oversized INIs refused
only after payload copying; size checks now precede all copying. The adapted
INI buffers use a 18,000-byte limit for small-model data/stack headroom.
These host C89 results do not establish native DOS or GUI acceptance.

PACKCGA.PY prepares a closed payload from actual driver receipts, generated
small fonts and pinned support. It requires a matching native CGACTL
receipt and stages the DOS installer sources/headers. BUILDSET.PY compiles
that CGA-only SETUP in a coordinated leased slot.
Finalization rejects host executables, extra files and synthetic fixtures,
then emits a development ZIP with root SETUP.EXE/README.TXT and one CGA folder.
Current core products, published installers and renderer profiles are unchanged.

All modes still present 16,000 visible VRAM bytes per full repaint. A dirty
eight-pixel logical column writes 8 bytes in CGA100, 2 in CGA320 or 1 in
CGA640. These are write-volume facts, not elapsed-time measurements. Measure
baseline/candidate typing, scroll, window moves, immediate Pixel/Output,
BitBlt, text, cursor overlap and full-screen paints on the same configuration.
Do not promise speed from reduced shadow size or host script timings.

## Gates before a usable native packet

1. Host: `TESTCGA.PY`; existing five-profile `tools/BUILDDEPS/TESTSRC.PY`;
   dependency adapter tests; CRLF/8.3 and closed source/payload inventory.
   Host results qualify only reference memory behavior, resource structure
   and source staging. Preserve failed receipts as well as the passing run.
2. Scheduled native build: pinned `--profile cga` view; each mode through
   BUILDCGA; successful 8086 instruction, REP-prefix, link/resource audits;
   actual compiler logs/listings and owned-process stop/release receipts.
3. Native DOS/Windows install: the complete movable expanded SETUP packet,
   with selected fonts/grabber/startup assets bundled. Validate the implemented
   small Helv/Courier registration and native undo; exercise
   success, refused inputs, interrupted copy/recovery, exact rollback and
   mode switches with Windows closed. No consumer Python, manual INI edits or
   individual support-file collection. The source OEMSETUP.INF alone is not
   completion of this gate. Never hot-switch Windows logical geometry.
4. IBM CGA emulation: normal 640 KB and Win3.0 /R; independently verify CRTC
   dimensions, colors 0..15 in both halves, foreground/background intensity,
   blink off, clipping and untouched padding. Check every GDI/cursor path,
   saved-footprint overlap, immediate drawing, enable/disable and DOS return.
   Test Run/Open/Save/message-box reachability, menu and radio/checkbox states,
   focus/tab/accelerators, all four edges and repeated starts. Capture native
   evidence honestly and measure the redraw suite; source/model PNGs are not
   native proof. Decide whether existing viewport work is needed for dialogs.
5. Physical IBM CGA: identify card revision, CRTC, monitor/output and ROM
   jumper. Confirm sync, snow/blanking and cursor/DOS behavior. Clone, PCjr,
   Tandy and composite claims require separate explicit qualification.
6. Consumer packet/publication: accept only separately qualified bytes and
   full manifests/recipes/notices. Preserve other modes, current release
   identities and old assets. Push, merge and publication need authorization.

## Final local native checkpoint

Runtime source is e2bf87b0214db50d9bc4e6b6fa1062bf837ec307. The preserved
basic-dialog/renderer checkpoint `8cc53057` remains unchanged. All three native
drivers pass C6/MASM/link/resource and 8086/REP audits. Normal renderer bytes
remain unchanged. Exact binaries, failed attempts and evidence pins are in
src/cga/NATIVE.JSN and the local review QUALIFY.JSON.

The expanded 23-file packet installs 17 files. Native DOS switches 100/320/640/100
and exact original fixture-tree UNDO pass. The managed-host transaction suite
passes 24 groups, 193 invocations and 106 fixtures. The native SETUP map leaves
5,200 bytes beyond its data/stack reservation. Consumers receive native SETUP,
README and one expanded CGA folder, with no support gathering or Python.

All three modes pass Run/Open/Save As/Find control and text bounds, an exact
Notepad save, palettes/blits/all 256 logical pairs, odd 32x32 cursor restoration,
draw-under, edges, padding and normal DOS exit to mode 3 with 640 KB in the IBM
XT 4.77 MHz/IBM CGA emulator. CGA100 System/Helv are five rows averaging three;
320-mode proportional faces are six rows averaging four. CG6 Helv preserves
all 224 original XT Pixels glyph ink matrices with proportional advances; its
Directory label is 57 pixels against a 61-pixel allowance, resolving the actual
640-mode clipping. Other font and renderer bytes stay unchanged.

Actual consumer startup loads one shared WDWIN/WTPLACE access owner in 100 mode.
The exact shared source pair is display 1449b9e4 and libwintandy 35f142dc; all
six runtime blobs match the earlier qualified pair. Child-group movement now
invalidates each moved child, fixing stale Control Panel icon pictures. Home,
Desktop controls, normal shutdown and pixel-following-hit-target evidence are
retained. In 320/640 the helper sets COLOR_GRAYTEXT black and exits; native
Find captures show visible disabled labels without a resident placement owner.

File Manager displays populated directory windows at [10,22,140,77] in 160x100
and [35,48,605,172] in 640x200, using ordinary maximize/MDI/File Open operations.
A DOS command writes the exact expected file and returns to Windows. The
following 100-mode graphics/cursor comparison establishes display count -1;
an earlier 26-pixel difference was exactly a still-visible pointer at its two
positions, not discarded evidence. The corrected complete VRAM comparison
passes with no excluded regions and matches the earlier qualified scene hashes.
The probe records original count 1 and hidden count -1, then restores count 1.

The final qualification composes the preserved basic 100 dialogs with its
unchanged 17-file focused continuation. The 320 GUI was tested in packet 05;
the 640-only follow-up changes only an unused font and notice for that mode.
Every selected 320 runtime byte is identical, and revised native DOS delivery
is separately checked. Final README-only packaging preserves every tested
payload and SETUP byte. These scopes are explicit in QUALIFY.JSON.

The private probe launches stock WINFILE.EXE normally and locates its File
menu by caption because maximized MDI children insert a system menu before it.
It loads no fonts and is excluded from consumer contents. Earlier controller
launch/menu/timing failures and the visible-pointer comparison remain preserved.

Physical IBM cards/CRTCs, snow/blanking, monitor scanout, clones and composite
remain separate qualifications. One DOS-command smoke test does not establish
general DOS-program or PrintScreen/grabber compatibility. The original local checkpoint predates publication approval; the current
public packet and evidence pins are recorded in tools/CGAPACK/ACCEPT.JSN.

The headless FRAME API can include blanking and omit lower scanout rows.
Native control/file/VRAM checks are separate evidence. Decoded VRAM images are
labeled as such and are not presented as complete monitor screenshots.
