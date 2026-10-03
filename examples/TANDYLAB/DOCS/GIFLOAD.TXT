GIFLOAD: bounded GIF-to-BMP companion for Windows 3.0
====================================================

STATUS
This is a companion converter, not a modification of Paintbrush. Paintbrush's
Open and Save As format lists are unchanged. Source and native executable are
original work; no CompuShow or Microsoft codec implementation was copied.

The exact acceptance matrix is in EVIDENCE.JSON. Native Windows 3.0 / 8086
codec tests and automated Paintbrush open/edit/save/reopen tests are separate
evidence. The Paintbrush test uses native Windows messages and its guest
clipboard. It is not a manually operated mouse/keyboard session. Physical
Tandy hardware remains untested.

RUN
Use the existing installed Tandy driver and its normal protected-video-memory
launcher. Copy GIFLOAD.EXE and a GIF to a DOS directory. Start GIFLOAD.EXE from
Windows 3.0. Type the complete GIF input path and a NEW BMP output path, then
choose Convert. Existing output names are refused, even if the name is the
input itself. Choose a different name; this proof deliberately has no overwrite
operation. On success choose Open BMP to start Paintbrush; GIFLOAD exits after
WinExec succeeds. Paintbrush must be installed in the Windows directory.
Input/output paths are limited to 127 characters and Paintbrush launch requires no spaces or quotes.
No COMMDLG DLL is needed. File selection is by typed path in this first proof.

The native helper chooses the palette from current driver width/NUMCOLORS:
- 320x200x16 and 160x200x16: the driver's 16 logical RGB colors
- 320x200x4: black/cyan/magenta/white
- 640x200x4: black/red/green/white
- 640x200x2: black/white
There is no dithering. Each GIF palette color maps to nearest squared RGB
distance, with the lowest output index winning ties. Logical RGB values follow
MODECHK.PY, not a claim that analog Tandy output has calibrated RGB values.
The helper window adapts to 160 pixels; its edit fields horizontally scroll,
and Tab moves between fields/buttons. Stock Paintbrush menus can still clip
in the narrow display modes. No image scaling or pixel-aspect correction is
performed. A 96x64 image is used for the native Paintbrush workflow proof.

SUPPORTED SUBSET
- GIF87a or GIF89a signature
- Exactly one image, filling its logical canvas, origin (0,0)
- Width 1..320 and height 1..200; file size at most 262144 bytes
- Global or local palette, up to 256 source colors
- Interlaced or sequential row ordering
- LZW minimum code sizes 2..8, clear codes, 3..12-bit codes, dictionary saturation
  and deferred clear after saturation
- Comment extension and opaque non-user-input graphics-control extension
- Normal bottom-up BI_RGB BMP with 1-bit (two colors) or 4-bit (four/16 colors)
  pixels, a 40-byte BITMAPINFOHEADER and explicit palette

Deliberately rejected: transparency; multiple images/animation; application
extensions (including looping metadata); plain-text extensions; subrect/offset
images; invalid/reserved controls; missing palette; excess/truncated pixels;
missing end code/trailer; trailing data; oversized input. Some otherwise valid
GIFs fall outside this subset. This is not an unrestricted GIF89a decoder.

SAFE FILES / MEMORY
The input is opened read-only. Output uses O_CREAT|O_EXCL, so existing files are
never truncated. The converter removes only the output it just created if a
conversion fails; cleanup failure is reported. A crash/power loss may leave an
incomplete new BMP. Treat only a successful conversion as usable. No global
TEMP directory scan or unrelated-file cleanup occurs.

Fixed LZW storage is 16384 bytes (4096 unsigned-short prefixes, 4096 suffixes,
4096 stack bytes). Palette, map, target and scanline buffers add 1232 bytes;
there is no whole-frame or 24-bit working buffer. Maximum scanline is 160 bytes.
Rows are mapped and seek-written directly into a normal bottom-up BMP; interlace
uses the four GIF pass orders. Compiler/linker maps give the actual module data,
code and requested 4096-byte heap plus 4096-byte stack. C-runtime FILE buffering
and Windows allocation overhead are separate from the fixed codec buffers.

BUILD
From the repository root, using its existing licensed C6/Windows toolchain:
python3 examples/GIFLOAD/BUILD.PY --dosbox <DOSBox-X> --out <new-output-directory>
This invokes CL /G0 /Gw /AS /W3 /Od and LINK4 with SLIBCEW.LIB/LIBW.LIB. The
resource-free NE expected-Windows-version word is stamped 3.0, as in the other
examples. Runtime requires Windows 3.0 real mode, original 8086/8088 semantics,
640 KB, no EMS/XMS/UMB workaround. The build emulator has more RAM; that is not
the runtime configuration. Only first-party sources, executable and test
fixtures belong in the deliverable, not Windows media or compiler libraries.

HOST CHECK
Compile the same core as a CLI on a POSIX host (Pillow required for the oracle):
gcc -x c -std=c89 -DHOSTCLI -D_POSIX_C_SOURCE=200809L -DS_IREAD=S_IRUSR \
 -DS_IWRITE=S_IWUSR GIFCORE.C -o gifcore
python3 TESTHOST.PY --exe <absolute-gifcore-path> --out <new-test-directory>
CLI mode values are 2 (mono), 4 (cyan/magenta), 5 (red/green), and 16.
The test compares actual decoded BMP pixels to an independent Pillow decode
and independently implemented palette quantization, verifies input preservation
and existing-output protection, and checks malformed streams leave no output.
Native /T is an automated test entry that reads C:\CASES.TXT, uses numbered
C:\Fnnn.GIF and C:\Onnn.BMP files, and writes C:\GIFTEST.LOG. Use only in an
isolated test copy, with new output names. The native fixture runner compares
native BMP bytes to the already pixel-checked host outputs.

EVIDENCE LIMITS
Host sanitizer fuzzing exercises 10000 deterministic mutations. LeakSanitizer
cannot operate in the execution environment; the successful rerun disables its
leak check while retaining AddressSanitizer and UndefinedBehaviorSanitizer.
Native GetFreeSpace checks establish no change in free space across the suite,
not physical-hardware timing or a complete memory-profiler proof. No speed claim
is made. Physical Tandy hardware and every stock Windows dialog at 160 pixels
remain unverified. Automated native acceptance does not claim manual CUA
coverage; that desktop-control connection was unavailable.

FORMAT SOURCE / ATTRIBUTION
Original implementation based on the published GIF89a grammar and LZW rules:
https://www.w3.org/Graphics/GIF/spec-gif89a.txt
The Graphics Interchange Format copyright and GIF service mark belong to
CompuServe Incorporated. No source-code reuse from CompuShow is assumed.

PAINTBRUSH LAUNCH DETAIL
Native testing found that passing C:\TEST.BMP while starting Paintbrush from
C:\WINDOWS could report the file missing. The same BMP opened successfully
when present in the inherited working directory. To avoid that issue, GIFLOAD
resolves the output to a full DOS path, temporarily selects its drive and
directory, launches the Windows-directory PBRUSH.EXE with the basename, then
restores the target drive's saved directory and the original drive. Nested paths
are passed without a trailing slash (DOS chdir rejects that form). Root paths
retain the root slash. The native test deliberately uses a directory different
from C:\WINDOWS and separately checks D: and C-root paths.

REPRODUCIBLE NATIVE TESTS
Use an existing installed guest created through the project's normal installer.
The runners clone that guest into a NEW output directory; they never edit the
source installation. Supply your own Windows 3.0 media/installation and the
existing licensed C6/Windows SDK toolchain. None is included here.

Core suite (after TESTHOST.PY generated the fixtures):
python3 TESTNAT.PY --guest <installed-guest> --build <GIFLOAD-build> \
 --fixtures <host-test-output> --dosbox <DOSBox-X> --out <new-directory>
Repeat against each of the five installed profiles. It checks all 243 results
and exact native BMP bytes against the host/Pillow oracle, including refusal
cases and unchanged free conventional-memory totals.

Build the separate, test-only Paintbrush harness:
python3 BUILD.PY --repo <repository> --dosbox <DOSBox-X> \
 --paintbrush-test --out <new-test-build>

Run the actual helper and Paintbrush:
python3 TESTPB.PY --guest <installed-guest> --build <GIFLOAD-build> \
 --test-build <PBTEST-build> --fixtures <host-test-output> --dosbox <DOSBox-X> \
 --profile <baseline|160|3204|6404|6402> --out <new-directory>
Optional --output-drive D uses D:\ART\TEST.BMP; R uses C:\TEST.BMP.
Default is C:\ART\TEST.BMP. This tests the helper's automatic mode palette,
checks every helper control fits on screen, opens the new BMP in unmodified
Paintbrush, uses Edit/Paste to add an 8x8 white bitmap from the guest clipboard,
saves, closes, reopens, and saves again. It then verifies that only the patch
changed and all 6144 pixels survive reopening exactly. PBTEST.EXE refuses to
run without the isolated-run marker. Never run this QA harness on a live guest: 
it intentionally creates named test files and replaces the guest clipboard.

SANITIZER MUTATION TEST
Build GIFCORE.C with HOSTCLI and main renamed to gifcli, then link FUZHOST.C
with AddressSanitizer and UndefinedBehaviorSanitizer. FUZHOST.C takes seed GIF,
new mutation input path, and new mutation BMP path. It performs 10000 seeded
mutations. Use ASAN_OPTIONS=detect_leaks=0 in environments where LeakSanitizer
cannot operate. The successful run still retains ASan/UBSan checking.
