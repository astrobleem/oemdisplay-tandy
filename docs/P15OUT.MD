# PC1512 Output optimisation

The current PC1512 driver is native-qualified in 86Box's emulated 8 MHz
8086 PC1512, with 640 KB and built-in 640x200, sixteen-colour video.
The original shipped driver, a same-input current-main baseline and the
final candidate produced identical pixels in all 48 captured frames.
This is emulator evidence; physical PC1512 hardware remains unqualified.

## Bounded change

BUILD15 applies P15OUT once after P15PATCH and before assembly. It reuses
RRPATCH's marker no-copy and bounded-polyline gate, and the generic
synchronous X bounds/column flush. Only staged EGA/TSOFT.ASM TOutput changes.
There is no XR1 viewport, packed-pixel, cursor or panning adaptation.
Rejected calls retain FlushShadow; accepted drawing is presented before
return. The existing PC1512 plane selection and CGA interleaving remain.

An exact validated two-point scan spanning [0,640), and other validated
full-width spans, use the existing FlushRetainRows path. Narrow spans use
FlushRetainColumns. This avoids the measurable full-width overhead found
in the initial all-Columns candidate. That candidate was not promoted.

## Matched drawing results

All runs used the same saved installed fixture, probe executable, emulator
binary and configuration. Timings use the BIOS clock. Application figures
are medians of three forced redraws, not launch or whole-session speedups.

| Workload | Baseline | Final candidate | Ratio |
| --- | ---: | ---: | ---: |
| Calculator redraw | 25,211 ms | 3,076 ms | 8.2x |
| Reversi redraw | 3,954 ms | 823 ms | 4.8x |
| Twenty small rounded keys | 16,477 ms | 1,373 ms | 12.0x |
| 20,000 full-width direct scans | 59,154 ms | 59,209 ms | within one 55 ms tick |
| 20,000 narrow direct scans | 55,255 ms | 33,999 ms | 1.6x |

The original 54,448-byte consumer driver is retained as the comparison
anchor. Its 48 frames equal the 58,128-byte main baseline, and its drawing
timings are within a timer tick of that baseline for these cases. The
3,680-byte increase predates this patch: RLE88 adds 2,933 bytes, SDIB88 adds
646, BMC_MAIN adds 73, and file layout/relocations account for 28. Resources,
TSOFT and TCURSOR match; this is the stock profile without diagnostics.
See [the focused map comparison](pc1512/OUTPUT/SHIPSIZE.JSN).

The final driver is **58,368 bytes**, SHA256
`2f9f59e29a7e472e17a39fa54bd138cdb5b3f4d9562690791fddb3b5f4a76998`.
Compared with the same-input main baseline, _TEXT grows by 240 bytes;
_DATA stays 1,636 bytes and the four-plane shadow stays 64,000 bytes.
Free memory before the probe is 294,976 versus 294,752 bytes (224 fewer).
Compared with the shipped control, total file growth is 3,920 bytes.
The candidate launched on the same 640 KB fixture and returned to DOS.

## Native checks and retained evidence

P15BENCH minimally adapts RRBENCH. Capture reads actual port 3DEh plane
selection 0..3, copying each displayed 8,000-byte bank atomically before
DOS file I/O, then restoring the read selector to zero. Each row has 80
bytes; alternate rows start at +0000h/+2000h. A capture contains exactly
64,000 displayed bytes across four planes. Distinct plane sentinels and
write-mask probes check selection, 3DDh=0Fh and default 3DEh=0. Flat B800h
and packed-pixel probes are not used as PC1512 evidence.

The 19 stages include left/right edges, immediate output after consecutive
calls, idle visibility, markers, 2/3/1024-point polylines, preserved fallback,
cursor overlap/restoration, Calculator, Reversi and Paintbrush. Independent
pixel oracles supplement byte equality for direct scans and markers.
All 48 frames pass against both references, with zero differing pixels.
Every driver build passed BUILD88 instruction, REP-prefix and link audits.

The shipped run's original receipt retains its failed mode-3 assertion.
Its separate assessment records the actual DOS prompt, post-WIN marker,
BIOS mode 6 and 640 KB. Both comparison runs returned the same state;
mode-3 restoration is not claimed. No raw failure receipt was rewritten.

[QUALIFY.JSN](../tools/P15PACK/QUALIFY.JSN) binds current source, compiled
and executed driver bytes, three runs, captures, probe, effective emulator
profile and the new native carrier transaction. [OUTPUT](pc1512/OUTPUT)
contains the replayable records. The original installer/OEM Setup receipt
in tools/DRVSET/NATIVE.JSN remains unchanged. All installer, launcher,
fonts, grabber and logo bytes are preserved. The rebuilt carrier separately
passed default extraction, fixed-target refusal, case retry and exact
payload checks. The current release's ZIP guide overlay retains every
runtime member from that qualified packet.

## Replay and rebuild

```text
python -B src/pc1512/P15PATCH.PY --check
python -B src/pc1512/P15OTEST.PY
python -B src/pc1512/P15CTEST.PY
python -B src/pc1512/P15VERIFY.PY
python -B tools/DRVSET/VERIFY.PY
```

These commands replay saved native evidence on the host; they do not run
Windows or measure new performance. P15OTEST has 29 source/model tests;
P15CTEST includes deliberate corruptions of the planar proof. Fresh native
builds use BUILD15's existing pinned external display view and actual
MASM/LINK toolchain, as documented in tools/BUILDDEPS/README.MD.
Final staged TSOFT SHA256 is
`3cefcb55501525e769884d4728cc79050d91df1602aa8bf9722e84d691d1ce1e`;
TCURSOR remains `4ded456320df4280c8bd8f074bbe5143325d8099dd3323a44f70d9e3f1beb775`.
No other adapter binary or release is part of this replacement.
