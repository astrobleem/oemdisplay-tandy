# IBM PCjr driver proposal (TNDYJR): first probe results

Status: **a PCjr driver candidate, TNDYJR.DRV, now builds through the pinned
BUILD88 pipeline and passes its instruction, REP-prefix and link audits. It
has not run under Windows yet.** Nothing here changes the shipped TANDY88/TR5
drivers, the WINXT disk, the accepted hashes or the Tandy RESERVE helper.
Every result below is DOSBox / DOSBox-X emulation; no physical PCjr has run
any of it.

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
verifies the dumps on the host without trusting the guest.

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
PCjr build is 80 bytes larger. The binary is not committed; rebuild it or
take it from the session hand-off. The listing confirms the 8086 encodings
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
3. Runtime: Windows 3.0 real mode on DOSBox-X `machine=pcjr` with owned
   media, display.drv=TNDYJR.DRV, launched through JRGUARD; then the usual
   CPU/memory/framebuffer, cursor-edge, ROP, text and paint/save/reopen
   tests. The build itself is done (above).
4. Keyboard, mouse and speed: the PCjr's keyboard reaches INT 9 through its
   BIOS translation, it has no DMA controller, and RAM in the low 128KB is
   slowed by video contention. Each needs its own Windows check.
5. The animated splash programs the Tandy palette through 3DEh; a PCjr build
   should use the static startup until that is ported.
6. Expected support boundary: 320x200x16 only to start. 640x200x4 (mode 0Ah)
   is a later profile; 640x200x16 does not exist on a PCjr.

## Sources

- [Tandy Graphics Adapter (Wikipedia): PCjr 16KB B8000h window aliased at BC000h, venetian-blinds incompatibility](https://en.wikipedia.org/wiki/Tandy_Graphics_Adapter)
- [PCjr video register notes (VGADOC PCJR.TXT): 3DFh page register fields, mode 09h/0Ah bank layout](https://pdos.csail.mit.edu/6.828/2014/readings/hardware/vgadoc/PCJR.TXT)
- [COMPUTE! March 1985, PCjr memory expansion and the video buffer below 128KB](https://atarimagazines.com/compute/issue58/pcjr_memory.html)
