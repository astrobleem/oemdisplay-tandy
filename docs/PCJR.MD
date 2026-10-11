# IBM PCjr driver proposal (TNDYJR): first probe results

Status: **proposal plus probes. No Windows driver binary exists.** Nothing in
this folder changes the shipped TANDY88/TR5 drivers, the WINXT disk, the
accepted hashes or the Tandy RESERVE helper. Every result below is DOSBox /
DOSBox-X emulation; no physical PCjr has run any of it.

## Why the PCjr is close

The Tandy 1000 was built as a PCjr clone, and the current 320x200x16 driver
already has the right shape for it:

- It uses BIOS mode 09h, which the PCjr introduced (with 08h and 0Ah).
- All drawing goes to a private four-plane shadow; only `FlushRows` in
  `V1.ASM` and two cursor routines in `TCURSOR.ASM` touch video memory.
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

## Evidence (DOSBox-X 2024.03.01 and DOSBox 0.74-3, Ubuntu packages)

`src/pcjr/JRPROBE.ASM` records machine identity, BIOS memory, the real MCB
chain, 40:8Ah before/after mode 09h, which MCB holds the page, then writes a
320x200x16 pattern with the TANDY88 bank formula through the physical page,
and dumps the page and the B800h window separately. `JRCHECK.PY` verifies the
dumps on the host without trusting the guest.

| Guest | 40:8Ah after mode 9 | Page | Pattern (32,000 bytes) | B800h window |
| --- | --- | --- | --- | --- |
| DOSBox-X `machine=pcjr` | F6h (CRT page 6) | 1800h, held by a DOS-owned (0008h) MCB of exactly 0800h paragraphs | 0 mismatches | 16KB, repeated at BC00h |
| DOSBox 0.74 `machine=pcjr` | F6h | same | 0 mismatches | full 32KB (more lenient than a real PCjr) |
| DOSBox-X `machine=tandy` control | F6h | B800h | 0 mismatches | full 32KB; BIOS 624KB, arena ends 9C00h as in ALTMODES.MD |
| DOSBox 0.74 `machine=tandy` control | F6h | B800h | 0 mismatches | full 32KB; this build reports 608KB |

The DOSBox-X PCjr result matches the documented PCjr window behavior and is
the one to design against. Writing through the physical segment is correct on
both emulators; writing through B800h is correct on only one of them. See
`pcjr/XJRCHK.JSN`, the raw probe reports `pcjr/*PRB.TXT`, guest output
`pcjr/*OUT.TXT` and exact configs `pcjr/*.CNF`. `pcjr/XJRPREV.PNG` is an
illustrative decode of the DOSBox-X page dump with a standard IRGB palette,
not an emulator screenshot.

Both emulators' DOS layers pre-reserve the page. A real PC DOS on a real
expanded PCjr may not; that is exactly what the guard below checks.

## Starter pieces in src/pcjr

**JRGUARD.COM** - read-only pre-Windows check, the PCjr counterpart of the
RESERVE step in the launcher. Exit 0 only if the DOS arena ends below
segment 1800h, or one in-use MCB (not free, not the guard's own PSP) covers
1800h-1FFFh. It shrinks its own allocation first; an early version without
that passed incorrectly because a COM program owns the largest free block
and could be "protecting" the page itself. Results:

| Case | DOSBox-X | DOSBox 0.74 |
| --- | --- | --- |
| PCjr, page reserved by DOS | PASS, exit 0 | PASS, exit 0 |
| PCjr after `JRFREET` frees that block (emulator-only test) | FAIL, exit 1 | FAIL, exit 1 |
| Tandy control | FAIL (not a PCjr), exit 1 | FAIL, exit 1 |

**JRPATCH.PY** - stages `V1JR.ASM` and `TCURJR.ASM` from the current sources
with three edits and refuses to write anything if any edit does not match
exactly: a public `video_seg` word (default B800h); in `TEnable`, after INT
10h mode 09h, on a PCjr only, `video_seg = (40:8Ah & 6) * 400h`; and the
three VRAM sites load ES from `video_seg`. `FlushRows` reads it before DS
switches to the shadow segment. On non-PCjr machines the staged code takes
the same B800h path as today. Run `python3 src/pcjr/JRPATCH.PY --diff` to
review; `--check` is a source self-test only.

**JRRUN.PY** reproduces the emulator matrix with an explicit emulator path:

    python3 src/pcjr/JRRUN.PY --emu dosbox-x --exe <dosbox-x> --machine pcjr \
        --bin <built-COMs> --out <fresh-dir> --cmd JRPROBE.COM --cmd JRGUARD.COM
    python3 src/pcjr/JRCHECK.PY <fresh-dir>

Build note: the probes are MASM 5.1 syntax, `.8086`, assembled here with
JWasm 2.21 (`-bin`, commit 7f6f32e) because the pinned MASM 5.10 toolchain
was not available in this session. Rebuild with MASM 5.10 + EXE2BIN before
anything ships. Hashes of the tested JWasm builds:

    JRPROBE.COM 43a23cc6ff124af337275dd4a4b2430f94abdee0bfe3dc39a5c0a53f074c4576
    JRGUARD.COM 16ac8ab9cef7fb73b43ca1f52e75c67f81d93e8c72a565d307dd7fd8d46324b9
    JRFREET.COM d5924644eb5d383c2bb9d0b5291e8417788055bb682fca821f9041658adff676

## Proposed launcher (not yet in any package)

    @ECHO OFF
    JRGUARD
    IF ERRORLEVEL 1 GOTO FAILED
    WIN /R
    GOTO DONE
    :FAILED
    ECHO PCjr video page is not protected. Windows was not started.
    :DONE

## Open items, in order

1. Run `JRPROBE` on a real PCjr with the owner's actual memory expansion
   and DOS. Record 40:8Ah, the MCB holding 18000h, and photograph the screen.
   The guard's fixed 1800h assumption comes from emulators only.
2. Decide whether JRGUARD should grow into a reserving helper (RESERVE-style,
   last-fit allocation of exactly 1800h-1FFFh) or keep requiring an existing
   PCjr memory driver. That depends on what item 1 finds.
3. Build the staged sources with the pinned DDK/MASM through a BUILD88
   profile under a new 8.3 name (proposed `TNDYJR.DRV`), then the usual
   CPU/memory/framebuffer, cursor-edge, ROP, text and paint/save/reopen tests.
   Windows 3.0 on DOSBox-X `machine=pcjr` is the first runtime target.
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
