# CGA 160x100 and normal graphics: coverage and bounded candidate

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
sweeping is used. This combination still needs native scanout verification.

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

## Current native checkpoint

This is an unpublished development candidate with partial acceptance. The
preserved basic-dialog/graphics checkpoint is `8cc53057`; runtime source for
the latest access client is `e30579b7623039fc3fe2dff1decce236adb5ae67`.
Exact binary hashes, earlier failed attempts and component receipts remain in
`src/cga/NATIVE.JSN` and the private native evidence directories.

All three drivers passed C6/MASM/link/resource and 8086/REP audits. The normal
320/640 renderer bytes remain unchanged. The current 58,208-byte CGA100 driver
has SHA-256 `75d9e93c619ff4647bf6a06f6b94056fe6b3bcd6448c05ee332661373c1921e3`.
On the IBM XT 4.77 MHz, 640 KB, IBM CGA snow-enabled emulator fixture, the
160x100 driver passes all 16 palette indices, all 256 adjacent color pairs,
memory BitBlt, immediate drawing beneath an odd-origin 32x32 cursor, three
edges, hide/restoration and untouched VRAM padding. Ordinary Windows exit
returns to DOS mode 3 with 640 KB. These are emulator results, not physical
card, snow-free scanout, clone, composite or real-mouse qualification.

The five-row proportional System/Helv and six-row fixed/OEM faces are selected
without explicit font loading in the accepted basic-dialog run. Run's outer
frame is 168 pixels wide, but its controls fit; Open is 154x98, Save As 153x86,
Find 159x58 and the tested message box 98x46. Native checkbox/radio states,
text extents and center hit-test handles are recorded. Notepad saves the exact
expected two-line file. All five qualified CGA100 font files remain unchanged.

The 320-mode font-selection unit now passes Run/Open/Save As/Find text and
control bounds, exact file save, palette/blits/cursor/padding and DOS exit.
Its CG2 System/Helv resources use 48x40 dpi and 11 points while driver logical
DPI remains 96x48. Wider original M/W/m/w forms retain an alphabet average of
four, preventing the truncated dialog-unit width from clipping static labels.
An earlier 96x48/9-point resource loaded successfully but mapped to a ten-row
Helv face; the rejected attempts remain evidence. The metadata experiment
changed several fields, so it does not isolate one field as the sole cause.

The 640-mode font-selection unit passes the same dialog/file/graphics/cursor
and DOS checks using the existing TEXT80 8x8 Helv/Courier derivation. XTC
System/fixed/OEM selection stays unchanged. These normal-mode font units are
not final consumer-packet installation acceptance.

The 23-file expanded packet's actual native SETUP installs all 17 selected
files in the 160x100 consumer fixture, including autoloaded CGACTL. It uses
the final shared source pair display `1449b9e4` and libwintandy `35f142dc`;
all six runtime source blobs match the earlier qualified shared pair. WDWIN
remains the only root-placement owner. Grid End/Home and Desktop controls
have native bounds/hit-test, traversal, recovery and DOS-exit evidence.

A settled follow-up caught a real defect: child hit rectangles moved while
icon pictures stayed behind. CGACTL now invalidates each child after
SWP_NOREDRAW. The focused native updated-helper unit changes the same pixel
comparison from zero matching cells to five exact unobstructed matches.
All 34 differences in the sixth cell are accounted for by the same stationary
6x5 pointer image in both captures; this supplemental finding is offline VRAM
analysis. The unit also passes Home and DOS exit. It updates only the helper
in the previously installed consumer image; final new packet delivery is a
separate gate. The owned process stopped and released the shared lease.

The current host transaction suite passes 24 groups, 193 invocations and 106
fixtures for the closed 23-file/17-installed inventory, including all modes,
collisions, interrupted copies, rollback/retry, INI limits and exact undo.
The latest native SETUP map leaves 5,216 bytes beyond data/stack. The final
helper is built; prepared07 contains its exact bytes. Its native SETUP build
and final packet assembly wait for the coordinated slot after WDESK.

Still pending are final normal-mode consumer startup and the reduced-color
disabled-label fix, plus final native delivery/mode-switch/exact-tree UNDO.
The new helper sets session COLOR_GRAYTEXT black and exits in 320/640 modes;
that branch has compiled but has no accepted Windows runtime check yet.
File Manager reachability and full-screen DOS/grabber/re-entry have no accepted
evidence here. Physical IBM CGA acceptance remains a separate hardware gate.
No push, merge, release or accepted product replacement has occurred.

The headless FRAME API reads row zero while CGA scanout begins at firstline;
raw PNGs can include blanking and omit lower rows. Native control/file/VRAM
checks are separate evidence. Decoded VRAM illustrations are labeled as such
and are not presented as complete monitor screenshots. Retain failed receipts
and wait for a complete TREE END plus idle before diagnostic captures.
