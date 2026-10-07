LEARN12 - BOUNDED ALTERNATIVES AND COLLECTION-ONLY RECOMMENDATION
Isolated host review. No native integration, publication or third-party code.
TANDI10 and the qualified LEARN11 packet remain byte-identical.

Clarification: canonical 23/31 versus reference 22/28
----------------------------------------------------
Canonical control uses each character's stored standard DAT answers, including
UNKNOWN. It reproduces 23 truthful first misses and 31 Claude-two-wrong failures.
The fixed reference supplies non-UNKNOWN user inputs for 255 of those UNKNOWN
cells. Values were borrowed from the separate file named AUDIT08, but HERE THEY
ARE SCRIPTED REFERENCE ASSUMPTIONS, NOT EXTERNALLY VERIFIED FACTUAL CLAIMS.
No external factual audit was performed by this prototype. The remaining 3
known-to-known AUDIT08 changes are excluded from the reference. All known standard
facts and the base engine/DAT remain unchanged in this experiment.
This changed input vector alone yields 22 first misses and 28 two-wrong failures,
even with no overlay. Different inputs can change scores, questions and which
facts the flip policy inverts. Compare learning methods against 22/28 within this
reference, never subtract canonical 23/31 from a learned reference result.
LEARN11 filenames TRUTH and 'truthful learning' mean consistent with that scripted
reference only; they do not certify previously UNKNOWN facts. REF is the clearer
label here. Both experiments use fixed answer vectors independent of learned DATs.

Alternatives fixed BEFORE evaluation, without canonical engine changes
----------------------------------------------------------------------
Collection: retain reviewed reports, but never use them for guesses, questions
or confidence. It reproduces every base-only path for every report condition.
Tie-only: after the unchanged engine reaches Q25, break exact base-score ties
using the actual score-table contributions from recorded answers and agreed
overlay cells. Earlier guesses/questions/confidence always remain base-only.
Cap2: after Q25, consider only candidates within 2 base points; divide secondary
evidence by 4 with integer truncation and clip to [-2,+2]. Prefer higher base score
then base ID on adjusted ties. No score, utility, threshold or confidence change.
A prospective native secondary pass scans at most the roster and 256 active
records * 25 observed answers (6,400 pair checks per guess), with a small signed
accumulator. It need not allocate a candidate list. These are design bounds, not
measured Win16 overhead; the host trace counters are retained in the evidence.
The 2-point cap is a predeclared small influence bound, not an optimized parameter.
Both methods act only after all questioning is finished, so secondary facts cannot
select their own questions or alter the noisy policy's flipped question IDs.
Reject only the actual displayed candidate, with the actual engine rejection code.
Base-score arrays never receive secondary evidence. All candidates remain eligible
until explicitly rejected. No Ask Two, loss reveal, undo or extra questions.

Comparisons
-----------
Same pinned 42-session report conditions REF/FALSE/NOISE from LEARN11; no new
training, chosen facts or tuning. Actual unchanged ENGINE.C and DB.C. Six answer
policies: reference, Claude one/two wrong, two UNKNOWN substitutions, softer
answer strength, and a fixed alternate flip rule (Q2+, first two known even IDs).
30,720 games. Every model preserves all 1,536 base question/answer paths and base
scoring work, with deterministic full repeats. Host costs are not native timings.

Reported condition/method     Reference first misses  Two-wrong failures
Collection, any condition              22                    28
REF tie-only / cap2                    21                    27
FALSE tie-only / cap2                  22                    28
NOISE tie-only / cap2                  22                    27

Additional policies matter: FALSE raises one-wrong first misses 54 -> 55 and
soft-strength first misses 23 -> 24. REF improves one-wrong first misses 54 -> 52;
tie-only improves soft-strength 23 -> 22, whereas cap2 stays 23. The alternate
flip policy stays at 12 final failures for every method. No aggregate guarantee
or parameter sweep is implied by these limited scripted cases.
Even narrowly bounded false tie-breaks can hurt; a consistent or noisy report
occasionally helping does not make it factual. Preserve all per-target changes in
EVIDENCE/CHECK12.JSN and raw case/repeat files. Prefer collection-only initially.

Capacity and reset semantics
----------------------------
Standard DAT contains 13,116 UNKNOWN cells; AUDIT08 contains 12,861. The prototype's
256-cell limit covers 1.95% of standard holes. It is an explicit small notebook
bound for Win16 feasibility, NOT a claim to learn the whole roster. 256 records
cost 3,072 bytes for counters; the 128-token ledger costs 4,096 bytes on disk;
header/trailer 60 bytes gives a 7,228-byte maximum serialized file. Existing
TANDI10 DGROUP minimum is 56,624 bytes; two full state copies are unsafe in 64 KB.
Collection-only needs NO active overlay in gameplay. Stream ledger validation and
transactional writes; load at most one bounded counter view plus scratch only
during review/save. Native footprint/I/O/crash behavior still requires measurement.

The pinned 42-game REF fixture has only 16 games with eligible answers, teaching
11 different cells. A future UI should disable Save when no eligible answer exists,
rather than spending notebook capacity on an empty contribution. The pinned
fixture and current tested format retain those empty-session tombstones unchanged.
Once either capacity is reached, refuse the whole new contribution with a clear
message. No eviction, majority override, conflict erasure or automatic rollover.
Reset facts clears counters, retains all session tombstones and does NOT free the
128-session ledger. A disputed cell becomes empty only after explicit reset; old
imports/retries still cannot silently reactivate it. Subsequent new reports need
two fresh agreeing completed sessions. Report IDs are not independent-human proof.
For a first collection-only release, defer import/merge and automatic rollover.
When full, retain the read-only notebook and continue standard guessing. A later
explicit archive/new-notebook design needs a notebook identity and an import rule
that rejects cross-notebook old session reports; it is not implemented or claimed
by resetting these files. No silent provenance reuse after overflow.

Minimal UI/format refinements
----------------------------
UI.HTM/UI.PNG show collection-only wording: 'reports agree', not 'facts became
active'; 'not used for guessing'; only eligible changed answers on optional pages.
Choose the named identity explicitly; default Skip. No 130-question review.
Disable Save for an empty report. Display cells and reports separately, including
the limits. Save uncertainty says 'Could not confirm save; Retry / Skip' and reuses
the SAME token. Clear/Reset states 'old report IDs remain; capacity not freed'.
Keep the tested v1 format, exact base pin and five-valued counters; do not store
an enable/activation flag that an imported notebook could use to affect gameplay.
Collection-only always leaves guessing unchanged even after two reports agree.
New names and known-fact edits remain deferred. No uploads or personal data access.

Reproduce: python TESTS/CHECK12.PY (Python 3, local host C89 GCC).
BASE sources/data are pinned; BRIDGE.C adds host-only read access and explicit
post-cap rejection. No private Windows or native toolchain is needed.
