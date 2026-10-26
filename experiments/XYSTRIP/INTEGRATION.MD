# Private 2,816-byte HPXY Windows integration candidate

This report preserves the focused A/B driver qualification. Subsequent
normal-package acceptance and the same-name install fix are in CANONICAL.MD.

The focused Windows integration passes. Keep the 2,816-byte staged budget and
the pure-Y4 no-blank path for this local candidate. The 5,504-byte experiment
exceeds XRBUILD's existing project allocation budget by 2,040 bytes; that alone
does not establish exhaustion of a 640 KB machine. No retrace scheduling redesign, helper-control change, publication,
package replacement or physical EX write was performed.

## Source and preserved baseline

The isolated source base is main `8d48aa04560a4730c9ee3d946bed865ca9be0c43`.
AGENTS.md, CLAUDE.md and BUILDING.MD were reread; no `.agents/skills` directory
was present in the checkout or its workspace ancestors. The CGA checkout and
shared helper sources were not edited.

`C:\Users\chad\Documents\Codex\2026-10-26\task\tandy-pan-integration`
holds separate verified baseline/candidate source views, build outputs and
private Windows-image clones. The dependency lock is the preserved
`96ce6971a1757f3c77094322ed82741791c79646` input set. Dependencies passed exact
membership, SHA-256 and size checks. Source objects were read by exact Git
object identity; the candidate overlay is closed by four file hashes in
INTEGRATION.JSN. The source views differ only in those four files.

The accepted installed HPXY bytes (`9db7bbd8...`, 56,704 bytes) remain preserved
as PRESERVED.DRV in each clone and were not overwritten in their source image
or accepted packet. The A/B baseline is a fresh build of current main source;
it is not byte-identical to that older accepted binary.

| Build | File bytes | Gross NE allocation | SHA-256 |
| --- | ---: | ---: | --- |
| Current-source baseline | 60,400 | 125,421 | `c418dff91b27940437d03d0143b99d4d0b9185890bb7f6ff76a89d0fae837d30` |
| Local candidate | 61,856 | 126,883 | `c86a243c9e724401de3fa40d2c304bb6e336c6f8ad5df241c2e4ff1911d297a9` |

Both real MASM 5.10/LINK4 builds pass the existing build/instruction checks.
The candidate adds exactly 86 code bytes and 1,376 scratch bytes, or 1,462
gross allocated bytes. Its data segment is 3,776 bytes. Shadow allocations
remain 64,000+17,920 bytes. The existing ceiling is 127,531 gross bytes,
leaving **648 bytes**; it was not relaxed. This is the project's 24 KiB budget
above the R3 gross NE segment-minimum sum, not remaining DOS RAM or a hardware
640 KB limit. The measured Windows heap headroom is reported separately below.
No per-pan allocation is added.

The source changes are the byte-budget preflight, disjoint exposed strips,
matching 2,816-byte scratch allocation, and safe Y4 commit before retrace.
Recovery now explicitly blanks before full software conversion even when the
Y4 path had not blanked. XRBUILD's stage-size report is updated to match.
PROTOTYPE.PATCH contains the exact four-file source diff.

## Actual Windows evidence

Four private boots used the previously passing installed Windows 3.0 fixture,
its existing RESERVE guard and WIN /R path, with the test driver and a focused
Win16 GDI probe. No display-selection or installer qualification is claimed.
The emulator is the existing headless 86Box Tandy 1000 HX surrogate, configured
for an 8088 at 7,159,092 Hz and 640 KB. The guest reports 624 KB after its
normal reservation. It is not physical EX qualification.

The probe uses actual driver exports, Windows GDI and a real CreateCursor
cursor, rather than cursor stubs. Two matched A/B suites passed:

* X16 and X24 in both directions; Y4 in both directions; pure Y16;
  positive/negative X16/Y8 diagonals; high-origin moves between 304,48 and
  320,56; aligned/clamped upper edges; far jumps through the full fallback.
* A canonical 81,920-byte shadow stream, packed VRAM conversion, all active
  bank addresses and expected cursor AND/XOR composition. Moving the cursor
  and subsequently hiding it restores the exact underlying image.
* GDI fills, lines and text; a further blue fill followed by panning; drawing directly beneath the
  visible cursor, then panning and hiding
  it without leaving stale saved-under pixels.
* Forced presentation failure from the Y4 path, software recovery with
  correct viewport bytes, cleanup to home/software mode and normal DOS return.

All **152 frame comparisons / 4,864,000 packed bytes** pass. Each run contributes
38 frames. Every visible custom-cursor pixel is independently composed from
the cursor masks, while every other viewport byte must equal the shadow.
The GDI interior-color assertions also pass; the initial oracle's mistaken
dark-blue expectation was corrected to bright-blue index 9, with its failed
oracle receipt retained. No driver change was needed for that correction.

The candidate's free memory was 154,624 bytes warm in the first suite and
154,592 in the extended suite. Each value remained unchanged after its pan
sequence. Baseline values were 156,096 and 156,064 respectively, so the
candidate consumes **1,472 additional allocated bytes** in Windows. The extended
candidate's largest free block was 149,280 bytes warm and after the sequence.
This establishes headroom for this probe and no observed per-pan loss; it is
not an exhausted-memory or arbitrary-application claim.

All four runs report normal DOS return with the post-WIN batch marker and
mode 3. Their owned emulator processes stopped and leases released. Final
FAT copies match in all four stopped images. Transient FAT-copy warnings
during live read-only observation did not persist after DOS returned.

## Focused movement measurements

These are individual Windows GetTickCount measurements around the Escape
call, excluding probe file logging. The timer resolution is about 55 ms.
They are guest measurements in this configured emulator, not physical EX
latency, statistical confidence intervals or optical blanking measurements.

| Requested movement | Baseline | Candidate | Candidate work |
| --- | ---: | ---: | ---: |
| X16, either direction | 1,208-1,209 ms | 165 ms | 1,600 bytes |
| X24, either direction | 1,208-1,209 ms | 165 ms | 2,400 bytes |
| Y16 | 1,209 ms | 165 ms | 2,560 bytes |
| X16/Y8, low origin | 1,208-1,209 ms | 165 ms | 2,816 bytes |
| X16/Y8, high origins/reversals | 1,208-1,209 ms | 165-220 ms | 2,816 bytes |
| Y4 | 109 ms | 55-110 ms | 640 bytes; no blank call |
| Far jump beyond budget | 1,208-1,209 ms | 1,208 ms | 32,000-byte fallback |

The representative X24 traversal rate rises from about 20 to 145 pixels/s;
X16/Y8 rises from about 13/6.6 to 97/48 pixels/s. These rates describe the
measured calls, not sustained helper navigation. Existing 8/4 helper steps,
timer cadence and far-target chunking policy are unchanged.

The earlier standalone DOSBox timing results are a separate emulator model.
They must not be combined with these Windows/HX measurements. Windows tests
support retaining the Y4 no-blank path because its exact framebuffer and
cursor behavior passed in both directions; they do not measure its optical
black interval. The common retrace wait and all other blanking placement
remain unchanged.

## Deliverables, blockers and next step

The local integration directory contains INTEGRATION.JSN, MOVEMENTS.CSV,
BUILD-COMPARISON.JSN, FILESYSTEM.JSN, CANDIDATE.SHA, both full build directories,
and four completed Windows run directories with driver identities, guest logs,
shadow/VRAM dumps, limited PNG captures and process/lease receipts. The final
suite directories end in `-qual`. The probe sources and host verifier are
retained here; generated source copies in each build preserve both probe
revisions. PROTOTYPE.PATCH is the reviewable source change.

An additional attempt was blocked before launch by another DOSBox process,
PID 24932. That BLOCKED receipt is retained in windows-baseline-final; no child
was launched or stopped there. Once the slot became available, the final
matched suites completed. No permission denial or pending emulator blocker
remains. Each emulator action acquired the real nonblocking byte-range lease;
the lock file's contents were never treated as proof of availability.

This is a qualified **local focused Windows-emulator candidate**. Remaining
gaps are physical EX scanout/blank timing, arbitrary applications and interactive
input, deliberately exhausted memory, natural retrace timeout behavior and
installer/package acceptance. Negative out-of-range coordinates and repeated
application reopen stress were not separately added to these focused suites.
The next step is independent source review and broader private Windows use,
then separately authorized physical EX measurement before any promotion.
