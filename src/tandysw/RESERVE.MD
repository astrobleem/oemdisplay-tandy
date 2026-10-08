# Normal-640K Tandy video-memory reservation

`RESERVE.COM` reserves the conventional-memory portion of the 32KB Tandy mode-09 framebuffer before Windows 3.0 real mode starts. It does not enable expanded base memory and does not change the BIOS memory-size word.

## Supported configuration

- Original Tandy signature checked as in [archived TANBOX.ASM](https://github.com/astrobleem/oemdisplay-tandy/blob/96ce6971a1757f3c77094322ed82741791c79646/tanvidasm/TANBOX.ASM); PCjr is deliberately excluded
- Normal 640KB shared-memory layout: BIOS reports 624KB, and the conventional DOS MCB chain ends at segment `9C00h`
- BIOS text mode 3 when the helper starts
- DOS 3.0 or newer with allocation-strategy functions
- 8086/8088 instructions only; no resident interrupt hooks

Other layouts, an occupied video overlap, or an unrecognized existing reservation fail with DOS exit code 1. Do not treat a failure as permission to start the Tandy driver. The current helper deliberately does not generalize to smaller-memory machines, linked UMB arenas, expanded-base-memory configurations, different Tandy models, or another program's reservation.

## Normal installation and launch

The ready-to-use [OEM disk](../../TANDY88.ZIP) includes this helper. Run its DOS
INSTALL, then use C:\TANDY88\TANDY88 SETUP for installation and
C:\TANDY88\TANDY88 to start Windows. The supplied launcher performs the check
for you every time; end users do not need to build a helper or write a batch.

In plain terms, mode 09h needs 32 KB at the top of the Tandy's shared RAM, but
the BIOS keeps only the upper 16 KB out of DOS's way. RESERVE asks DOS to keep
the remaining video overlap unavailable to programs before Windows starts.
It is not extra memory or a graphics accelerator. It leaves BIOS memory size
unchanged, stays reserved until reboot, and refuses unsupported/occupied layouts.

## Developer launch example

The following explains the guard used by the supplied launcher. For normal
installation use the complete disk's instructions above.

Copy the built `RESERVE.COM` onto the guest drive, then use this DOS batch sequence before Windows:

    @ECHO OFF
    RESERVE
    IF ERRORLEVEL 1 GOTO FAILED
    WIN /R
    GOTO DONE
    :FAILED
    ECHO Video reservation failed. Windows was not started.
    :DONE

Run it from a directory containing the helper or put its directory on PATH. Run it before Windows, while the overlap is still available. It may be run again: an exact matching installation returns success without allocating another TSR. There is no unload command; reboot to remove it or replace it with a different build. A reservation left by a different build is not automatically adopted.

## Memory layout and implementation

Mode 09 uses physical `98000h-9FFFFh`. The normal Tandy BIOS already excludes `9C000h-9FFFFh` from the DOS arena, leaving the lower 16KB exposed to DOS allocations. This is the overlap described in [archived tanvidasm/NOTES](https://github.com/astrobleem/oemdisplay-tandy/blob/96ce6971a1757f3c77094322ed82741791c79646/tanvidasm/NOTES).

The helper uses DOS calls to retain:

- A 1,776-byte low-memory owner block, including its PSP and explicit stack
- A 16,384-byte high block at segment `9800h`
- The two required 16-byte MCB headers

The high block's MCB is at `97FFh`, outside video RAM. This placement matters: reserving only from `9801h` would leave a DOS header inside the framebuffer. The total retained allocation and headers is 18,192 bytes; the existing BIOS-exclusive 16KB is not allocated again.

The helper first shrinks its COM allocation and frees its environment. Freeing the environment before reservation is important when an inherited last-fit strategy placed it at the high end. It then reads and validates the real conventional DOS MCB chain using the DOS list-of-lists pointer, including its exact upper boundary and the final free run. Adjacent free MCBs need not already be coalesced. It temporarily selects conventional last fit, allocates 0400h paragraphs, verifies the returned segment, MCB type, size and owner, and restores the previous allocation strategy. It never edits an MCB directly.

Only after successful verification does it write a versioned marker into the low owner block. It closes inherited DOS handles after printing, including redirected stdout, and terminates-and-stays-resident with INT 21h/AH=31h. Both owned allocations remain unavailable to subsequent DOS clients. The signature, low owner MCB, high MCB and allocation sizes are checked on repeated invocation. The marker and stack are never placed in the video overlap.

Reducing BDA `0040:0013` alone would not shrink an existing DOS arena. This helper therefore leaves that word unchanged and reserves through the allocator that Windows uses.

## Reproducible build and actual DOS tests

On the tested Linux host:

    python3 src/tandysw/RESERVE.PY --dosbox /path/to/dosbox-x --out /path/to/new-output

To exercise DOSBox-X's 8088-style four-byte prefetch configuration too:

    python3 src/tandysw/RESERVE.PY --dosbox /path/to/dosbox-x --out /path/to/another-new-output --cpu 8086_prefetch

The output directory must not already exist. The harness uses the repository's existing MASM 5.10, LINK and EXE2BIN, compiles `.8086` source, and boots an independent emulator for every case. Each process has a 60-second timeout; host logs are capped at 64KB. It does not need Windows files. Outputs include `RESERVE.COM`, assembler listings, per-case reports and `RESULT.JSON`.

`RESERVET.ASM` is an isolated regression fixture, not an installation component. In addition to real DOS allocations and video writes, its negative tests can deliberately change the emulated BIOS memory-size word or shorten the free terminal arena. Run these tests only in disposable emulator sessions, never on a user's live DOS system.

## Verified results, 2026-10-02

DOSBox-X 2026.08.31, commit b13702c, Linux SDL2 build; machine=tandy, expanded base memory disabled, no XMS/EMS/UMB. DOSBox-X's built-in DOS reported version 3.30 for normal cases. A version-2.11 case verifies the helper's version gate; it is not a test against genuine MS-DOS 2.11.

- 24 checks pass with `cputype=8086`, configured `core=normal`
- 24 checks pass with `cputype=8086_prefetch`, configured `core=normal`
- Real maximum DOS allocation stops at segment `97FFh` after installation
- A full 32KB write through mode-09 `B800h` is verified to alias physical `9800h`; the ordinary allocation guard and all 16 bytes of the reserved block's MCB survive
- The reservation remains valid after returning to text mode and invoking the helper again
- Repeated invocation preserves owner, allocation count and memory topology
- First-, best- and last-fit strategies are restored and pass the allocation/video test
- The TSR retains no inherited open handles
- Another owner's partial overlap or exact-size block is rejected without taking its memory
- Unexpected arena end, BIOS size, video mode, CGA, expanded-base-memory configuration and DOS version are rejected
- An independent strict instruction audit checks 261 emitted helper instructions with zero unsupported instructions; code ends immediately before `expected_id` at COM offset `03BCh`

Final helper: 1,512 bytes.

SHA256: `644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8`

These are emulator-level allocator and memory-safety results. They do not establish physical EX/HX hardware compatibility, cycle-accurate 8088 timing, or a successful Windows GUI test. Those are separate acceptance checks.

## References

- Repository [archived tanvidasm/NOTES](https://github.com/astrobleem/oemdisplay-tandy/blob/96ce6971a1757f3c77094322ed82741791c79646/tanvidasm/NOTES) and [archived TANBOX.ASM](https://github.com/astrobleem/oemdisplay-tandy/blob/96ce6971a1757f3c77094322ed82741791c79646/tanvidasm/TANBOX.ASM)
- [Microsoft MS-DOS Encyclopedia, system calls](https://www.pcjs.org/documents/books/mspl13/msdos/encyclopedia/section5/): allocation, resize, strategy and TSR interfaces
- [DOSBox-X DOS process termination implementation](https://github.com/joncampbell123/dosbox-x/blob/master/src/dos/dos_execute.cpp): retention of owned allocations for TSR termination
- [DOSBox-X CPU settings](https://dosbox-x.com/wiki/Guide%3ACPU-settings-in-DOSBox%E2%80%90X): accepted CPU names; plain `8088` is not a supported selector in the tested build
