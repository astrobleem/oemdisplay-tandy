LEARN11 - HOST LEARNING PROTOTYPE FOR REVIEW, NOT A TANDINATOR RELEASE

Open UI.HTM for the offline 320x200 clickable design, or UI.PNG/UI.SVG for four
static panels. Read POLICY.TXT for the bounded format, feedback restraint,
storage recovery and native memory proposal; UI.TXT describes the flow.
Run: python TESTS/CHECK11.PY
Requires Python 3 and a host C89 compiler. This Windows fixture uses GCC from
C:\msys64\mingw64\bin if present, otherwise gcc on PATH. No private Windows,
DOSBox, display driver, compiler redistribution or installed app is required.
The check rebuilds only TESTS/ENGINE.DLL, linked to pinned verbatim ENGINE.C/DB.C.

Completed evidence
------------------
68 checks: strict explicit opt-in/confirmed completed manual identity; reject
demo/replay/learned-game reports; UNKNOWN/base-known exclusion; preserve all
four non-neutral strengths; two matching reports; all conflicting strengths
inactive; duplicate retry/import guards; reset tombstones; 128-session and
256-cell refusal; structural/counter/base/length/CRC/oversize validation; every
single-byte corruption position; six interrupted-save stages; backup recovery;
seven deterministic full-roster repeats and default-off/disputed baseline paths.
Full-roster engine paths: 7 models * 256 targets * 2 answer policies * 2 repeats
= 7,168 evaluated games, plus 126 completed training games. Timings are host-only.

The exact delegated Claude policy is reimplemented here: beginning at Q4, flip
the first two non-UNKNOWN input facts using 4-v; reject wrong guesses; after Q25
guess only; fail on a wrong guess after 10 earlier rejections or no candidates.
It reproduces the pinned canonical standard 31 versus AUDIT08 36 failures and
truthful first misses 23 versus 19. The original Claude ZIP was not downloaded
here, so matching policy/outcomes is not a claim of executing its source archive.

Learning comparison with FIXED independent scripted answers
-----------------------------------------------------------
The reference fills only 255 standard UNKNOWN cells from separate AUDIT08 across
21 characters. Other known cells stay unchanged. The same answer rows are used
for every evaluated model; learned DATs do not supply their own supposed truth.
This is a scripted audit-based reference, not independent human factual proof.
Each training condition has 42 completed games, two per character. Both sessions
use the frozen unlearned base; learned facts cannot choose their own confirmation.

Model                   Active   Truthful first misses   Two-wrong failures
Unlearned fixed ref        0              22                     28
Two truthful reports      11              21                     36
Consistent false reports  52              23                     33
Repeated Claude-noisy     20              24                     34
All 11 truth cells disputed 0             22                     28

All five models eventually solve all 256 truthful targets under the bounded
reject policy. Truthful training reduces mean questions 14.40625 -> 14.28125 and
rejections 41 -> 39, but noisy failures worsen 28 -> 36. This experiment's 28
baseline uses the fixed extended input reference, not canonical UNKNOWN inputs;
do not compare its deltas directly to the separate canonical 31/36 validation.

Concrete benefits: Poseidon truthful play improves from 25 questions/two wrong
guesses to 23/no wrong guesses; Ernie and Cristiano Ronaldo first guesses improve.
Concrete harms: truthful learning creates new noisy failures for Catwoman, Scarlet
Witch and others, and worsens truthful first guesses for No-Face and Lionel Messi.
Consistent false training makes truthful Rapunzel require six rejected guesses
instead of zero, and creates new noisy failures for Zeus, LeBron James and others.
The all-inverted FALSE training is an explicit adversarial fixture, not the Claude
policy; NOISE training and every noisy evaluation use the exact delegated policy.
Two agreeing reports can therefore activate consistent misinformation. Counts do
not establish independent corroboration. Correct new facts can also alter global
question selection; the same flip rule can flip different adaptive questions.

Native integration needs review
-------------------------------
Do not enable these overlays in the installed app. Default off and conflict
fallback protect the base; matching reports alone do not guarantee useful or
robust guessing. Review activation/scoring policy and the observed noisy
regressions before native integration. No thresholds were changed here.
Maximum serialized state is 7,228 bytes; observed truth/false/noisy files are
1,536/2,028/1,644 bytes. This is not measured native RAM. TANDI10's DGROUP minimum
is 56,624 bytes, so two full state copies would exceed a 64-KB segment. POLICY.TXT
proposes streaming provenance/writes and <=1,536 bytes of compact active records.
Host DAT snapshots only test actual engine effects; they do not measure runtime
overlay lookups. Win16 storage/guards, DGROUP/stack, opcodes, disk costs and native
rename recovery remain unimplemented/unqualified. Native test media is not needed
for this host review. Reset retains 128-token provenance; rollover is unresolved.

BASE contains only pinned first-party source/data from immutable TANDI10. TESTS
and EVIDENCE contain synthetic host fixtures, no personal reports. No publication,
network upload, learning in the native app, canonical promotion, installed
settings changes, CF writes or TANDI10 modifications were performed.
