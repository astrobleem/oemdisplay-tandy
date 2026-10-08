# Tandy 320x200x16 software-raster bring-up

This is an additive, reproducible Windows 3.0 **real-mode prototype**. It leaves the existing src/tandy16 driver and build path unchanged.

## Verified V1

The included bin/TANDYV1.DRV is the exact binary used for the successful Windows 3.00 GUI test:

- Program Manager desktop, icons, colored title bars and menus
- Maximize/repaint, Run dialog and application launch
- Notepad typing, caret, selection, copy/paste, close and background repaint
- Paintbrush launch and color palette
- Serial mouse cursor movement and background restoration
- Clean Windows exit back to DOS

Size: **46,288 bytes**

SHA256: **995d0079278a42254d997684fb51bd4285bd19bedc2e32cca3bf5065d3cfc61a**

A clean rebuild using only the existing main-branch DDK/toolchain inputs reproduces this binary exactly. No Windows installation media is needed to build it.

## Important limits

- Tested in DOSBox-X 2026.08.31 SDL2, machine=tandy, **cputype=386**, normal core, WIN /R
- **Not an 8088/8086 hardware-ready driver.** Generic DDK includes still select .286 and contain later-CPU instruction encodings. An 8086 port remains separate work
- Mouse clicks, window dragging, Paintbrush drawing, standard/enhanced modes and physical hardware are not verified
- V1 flushes the full shadow framebuffer after drawing; substantial redraws are slow
- The tested configuration requires expanded Tandy base/video memory as described below. A normal 640KB shared-memory Tandy needs an additional reservation solution before Windows
- Existing CGA grabber entries are not a claim of enhanced-mode support

See [TESTING.md](TESTING.md) for precise coverage and [PROVENANCE.md](PROVENANCE.md) for dependencies and source history.

## Rebuild

Requirements: Python 3, DOSBox-X, and this repository's existing BIN, LIB and DDK directories.

From the repository root:

    python3 src/tandysw/build.py --dosbox /path/to/dosbox-x --out /path/to/fresh-build-directory

Use --repo /path/to/repository when invoking from a staged source directory. On Windows, use python and the path to dosbox-x.exe.

The output directory must not already exist. The script:
1. Copies existing tracked DDK source/assets into the output directory
2. Applies ten small software-memory-backend edits without changing the DDK originals
3. Assembles/links the renderer and software cursor
4. Builds the configuration/font/color-table resources
5. Attaches all 74 Win16 resources
6. Requires exact resource and driver SHA256 matches

Successful output contains TANDYV1.DRV, RESULT.json, assembler/linker logs and prepared source. Some MASM A5104 short-jump suggestions and LINK L4021/L4046 warnings are expected; zero severe assembler errors and the final exact hash are required.

To verify an existing output:

    python3 src/tandysw/verify.py /path/to/TANDYV1.DRV

## Install in a separate Windows 3.0 test copy

Start from a working stock-CGA Windows 3.0 installation.

1. Copy bin/TANDYV1.DRV to C:\WINDOWS\SYSTEM\TNDY16LO.DRV
2. Install EGASYS.FON, EGAFIX.FON and EGAOEM.FON from your Windows 3.0 media in C:\WINDOWS\SYSTEM
3. Set SYSTEM.INI [boot]:

       display.drv=tndy16lo.drv
       fonts.fon=egasys.fon
       fixedfon.fon=egafix.fon
       oemfonts.fon=egaoem.fon

4. Retain the stock Microsoft mouse driver
5. Start with WIN /R

The supplied run.py launcher uses a prepared guest directory:

    python3 src/tandysw/run.py /path/to/guest-drive-c /path/to/dosbox-x

The launcher writes TANDY.LOC beside itself and bounds console output by discarding it. For debugging, use a separate bounded log/PTY harness.

## Required DOSBox-X configuration

    [dosbox]
    machine=tandy
    memsize=16
    allow more than 640kb base memory=true

    [cpu]
    cputype=386
    core=normal
    cycles=100000

    [serial]
    serial1=serialmouse

### Why the memory setting matters

BIOS mode09 uses 32KB of shared video RAM. Switching from text mode can overwrite the extra 16KB at the top of conventional memory if Windows has already allocated it. The repository's tanvidasm/NOTES documents this reservation requirement too.

The expanded-base-memory setting avoids that overlap in the tested emulator. It is not a fix for an unmodified physical 640KB Tandy. Do not treat this checkpoint as hardware verification.

### Why a serial mouse

Windows 3.0's stock PS/2 detection excludes the Tandy machine ID. With the default mouse hardware, USER briefly displayed an hourglass and then explicitly hid the cursor. COM1 Microsoft serial-mouse emulation enabled a visible moving cursor.

Use DOSBox-X Ctrl+F10 to capture/release the mouse. Enable keyboard capture through its Main menu if the host intercepts Alt+Space.

At 320x200, some application dialogs are wider than the display. Program Manager may inherit off-screen positions from a larger display; maximize it with Alt+Space, X.

## Architecture

The DDK's generic four-plane memory renderer draws into a 32KB shadow bitmap. Wrappers substitute the shadow descriptor for screen devices, preserving memory-bitmap arguments. A conversion pass maps scan-interleaved R/G/B/I planes into packed Tandy I/R/G/B pixels:

    video_offset = (y & 3) * 8192 + (y >> 2) * 160 + (x >> 1)

Even x is the high nibble. The software cursor is a clipped save-under overlay in VRAM, excluded around framebuffer flushes.

The module is named DISPLAY and uses canonical Windows 3.0 display ordinals, including cursor exports 101-104. Required named OEMBIN/FONTS resources are present; the original loader and resource failures are documented in TESTING.md.

## Next work

- Complete mouse click/drag/drawing regression
- Finish and GUI-test the dirty-rectangle optimization separately
- Port all reachable DDK code to actual 8086 instructions
- Validate conventional/video-memory reservation and then physical hardware
- Polish OEM installation packaging after runtime coverage

Cleanup note: the legacy src/tandy16 implementation and tanvidasm
provenance cited by this historical record are preserved at
[the exact DEV snapshot](https://github.com/astrobleem/oemdisplay-tandy/tree/96ce6971a1757f3c77094322ed82741791c79646/). Current source and
accepted binary identities remain unchanged.
