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
restores the prior text page, cursor shape and position. Ordinary DOS return,
Windows re-entry and full-screen DOS/grabber interactions need actual tests.

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
small fonts and pinned support. It automatically stages the helper source and
header. BUILDSET.PY compiles that CGA-only helper in a coordinated leased slot.
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

## Native development results

All three drivers passed native C6/MASM/link/resource and 8086 audits from
source checkpoint 5e1c8cde. The 58,208-byte CGA100 driver SHA-256 is
3c204d3515f94893750c2352d9089977a4e675de582a4128828ae7bbf1f035bd.
Native DOS SETUP installed/switched 100, 320, 640, 100 and UNDO restored both
INIs exactly. These tests used the normal shared lease and owned watchdog.

The first IBM XT 4.77 MHz / 640 KB / IBM CGA snow-enabled Windows run loaded
160x100x16, 48x40 dpi and 4x6 System/Fixed/OEM fonts. Program Manager menus
and Notepad worked. Notepad's actual File Open dialog clipped its right and
bottom controls: its stock Helv 8 template is 192x130 dialog units. The
first six-row dialog face is rejected for fit. A 3x5 dialog-only strike is
now staged for retest; desktop fonts/driver bytes are unchanged. SETUP now
prints per-file checking/copy progress for slow 8088 installation.

Windows exited to an ordinary C:\\WINDOWS prompt with BIOS mode 3 / 640 KB.
This is an initial native smoke check, not complete palette/cursor/GDI,
re-entry, other-mode GUI or physical-hardware acceptance. The first helper's
window-text measurements had a varargs pointer bug and are not evidence;
its screen/font metrics and actual captured frames are retained. The private
86Box capture fixture will use simple line doubling for the next run, avoiding
the raw unscaled framebuffer's stale lower rows. No image editing supplies
native proof. No publication has occurred.

Native slots remain coordinated through the parent and normal shared lease.

The next candidate's progress output exposed tight C6 small-model memory:
its native map leaves 1,568 bytes after the data/stack reservation. Its file
copy ran much slower and was stopped with the private image/records intact.
Stream-buffer allocation is the working cause, pending the next native
comparison. The INI buffers now cap each input at 18,000 bytes, freeing
4,000 bytes. BUILDSET rejects maps with less than 4,096 bytes of remaining
data-group address space. The shared INI source and published SETUP remain
unchanged. A separate native font/GDI fixture may reuse the first complete
install; it is explicitly not proof of the revised consumer transaction.

That font/GDI fixture confirmed a 32x32 custom cursor restores the captured
16 KB scene exactly after four tested positions, with unchanged VRAM padding.
It exercised immediate pixels, RGB brush fills and a 16x4 memory BitBlt.
The fill colors dithered against the inherited Windows logical palette;
the helper's draw time included logging and is not a speed benchmark.
Native window measurements still show Run at 220 pixels wide and File Open
at 202x115 after the smaller dialog files were supplied. The new strike is
not being selected as intended. Registration/mapping remains under diagnosis;
neither font fit nor this packet's usability is accepted yet.

A subsequent native probe confirms Helv is available at startup and maps to
5x3 before explicit AddFontResource (which also succeeds). Run and its
controls instead report a System 6x4 LOGFONT. The next font candidate makes
System/Helv proportional five-row UI faces with average width three, retaining
spacing for capitals/digits. Fixed/OEM remain 4x6; Courier is 4x5. The ANSI
variable descriptor follows 5x3. Native acceptance remains pending.

Using exact inherited Windows logical-palette RGBs, the second GDI probe
produced native bar codes 0..15 and all four expected 16-pixel BitBlt rows.
The last pixel was code 4. A 32x32 cursor at odd origin (1,1), then three
edges, restored all 16 KB exactly and left padding unchanged. The draw suite
measured 1,978 guest milliseconds excluding log writes; it is one workload,
not a speedup claim or a physical-hardware timing result.

The proportional System prototype reports System height 5 / average width 3,
with fixed/OEM still 4x6. Native File Open now fits at 154x98; Save As is
153x86; Find is 159x58; a message box is 98x46. An actual Notepad open/new/save
workflow produced the exact expected two-line file. Checkbox and radio
accelerators changed their native states. Run's frame is 168 pixels wide,
but its command field and all buttons fit (rightmost control edge 156).
The bounded exploratory run ended before its final DOS-exit check. A rebuilt
consumer packet with passive instrumentation still needs acceptance.

The current headless FRAME API returns target_buffer from row zero, while
CGA's scanout blits from firstline. Its raw PNGs retain upper blanking and
can omit lower scanout rows; they are raw-buffer records, not complete monitor
screenshots. Native control bounds, saved-file bytes and complete VRAM captures
are separate evidence. No reconstructed image is presented as native scanout.

Offline follow-up tightens lower-case r/t so Directory: fits its observed
26-pixel static control; the actual five-row glyphs and label widths pass
the independent font checks. The passive probe now records text extents,
check states and center hit-test handles, plus an explicit draw-under-cursor
test. These changes await their scheduled native run. The native rebuilt
driver is 58,208 bytes, SHA-256
75d9e93c619ff4647bf6a06f6b94056fe6b3bcd6448c05ee332661373c1921e3;
all eleven NE code/data segment payloads match the earlier tested driver.

A host-only audit flags larger stock Control Panel templates for native
confirmation. It is not a fit verdict: applications can hide or resize those
controls. Basic Run/Open/Save/Find results do not qualify every desktop dialog.
If native controls remain unreachable, evaluate the existing software viewport
and task-time helper contracts in src/softpan/SPPATCH.PY and src/xtpan/XTPAN.C
before proposing another renderer. No viewport or peer branch is changed here.

The complete revised consumer packet now installs natively on the IBM XT
fixture and passively selects System/ANSI variable fonts at height 5 / average
width 3. SETUP's C6 map leaves 5,568 bytes after data/stack, passing its gate.
The native GUI continuation verifies identical installed payloads and performs
no explicit font registration. Run/Open/Save As/Find controls fit; Directory:
measures exactly its 26-pixel control width. Checkbox/radio states and center
hit tests are recorded. Notepad's saved two-line file matches exactly.

The current native VRAM oracle passes all 16 palette indices, all 256 adjacent
color pairs, memory BitBlt, drawing beneath an odd-origin cursor, three edges,
hide/restoration and untouched bank padding. Windows returns normally to DOS
mode 3 with 640 KB. The owned process stops and releases the shared lease.
See src/cga/NATIVE.JSN for exact packet, build, probe/run and evidence pins.
Larger desktop dialogs, normal-mode IBM GUI and physical hardware remain
separate gates; this is still an unpublished development candidate.
