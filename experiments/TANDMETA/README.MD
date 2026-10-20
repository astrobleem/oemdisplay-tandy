# Tandinator Meta-assisted curation: isolated proof of concept

Host-only experiment, started 2026-10-20 against repository commit
`880aee0be7278ff0655d7116a9edf44e5e24e8ea`. No published source, runtime,
curated record, art, package, release or installation setting is changed.
Python 3.8+ and its standard library are sufficient for the simulation.

## Event and application findings (checked 2026-10-20)

The [official event page](https://cerebralvalley.ai/e/meta-ai-developer-hackathon)
currently advertises remote work October 26-November 4, submissions November 4
at 9 PM Eastern (8 PM Central), indie/startup tracks, a $1 million prize pool,
and Build for Your World / Push the Frontier themes. It explicitly supports
Meta open-weight models alongside the advertised event APIs. Indie judging
mentions creativity, ambition and working results. Full rules remain pending
before October 26; accepted participants must accept them. Existing-project,
pre-event development, team, deliverable and detailed license requirements
are therefore NOT established by this check. Treat this as preparation and
retain its date/history; do not represent pre-event code as event-period work.
The page's kickoff header says EST; confirm kickoff timing with organizers.

The approval email was read and confirms APPROVED; it contains no project
concept or credentials. Searches of related Gmail/application messages and
prior conversation context did not recover the application answers. This
Tandinator concept remains a candidate, not the recovered application idea.
No authenticated application-form history was accessible through these tools.

Candidate pitch: use a modern Meta model to help author and inspect knowledge
that an unchanged, disconnected Windows 3.0 game can consume on an 8088.
Build for Your World seems the closer theme; this is our assessment, not
organizer approval or eligibility confirmation.

## What is implemented

`CURATE.PY` loads the existing curated STARTER.JSON read-only and imports the
existing DBBUILD.PY compiler/validator. The model receives the original
questions, source-reference metadata, portrayal policy, and answer rows for
Mario, Luigi, Princess Peach and Bowser. It proposes up to three new questions
with four answer codes each, and up to three suspect existing answer cells.
It supplies reasons, never a claim of independently verified facts.

Every proposal gets a content hash. A separate review file requires a named
reviewer, approve/reject for EVERY proposal, and an evidence/rejection note.
The review is bound to the exact batch; the batch is bound to the base data.
Pending, missing, stale or altered reviews fail. Each finding is reviewed
independently; no model correction is automatically accepted.

Only approved proposals enter a separate PREVIEW.JSON / PREVIEW.DAT under this
experiment's OUT directory. Other 124 characters get explicit UNKNOWN answers
to each new question. They are not completed or inferred by the model. The
report calls out that limit. The original compiler validates ASCII, text/UI
limits, full answer matrices, capacity, binary layout/checksum and both packed
matrix orientations. Duplicate profiles are rejected. This is structural
validation, not factual verification or proof of improved guessing accuracy.

No command promotes a preview to SOURCE/data, RUN, a package or a release.
No runtime code or network behavior changes. The DAT uses the existing format;
this experiment has not been run on Windows or physical hardware.

## Reproduce the offline demonstration

Run from the repository root. Outputs must be fresh paths below OUT; reruns
can use new names. No pip packages, API keys or model downloads are needed.

```sh
python3 experiments/TANDMETA/TEST.PY
python3 experiments/TANDMETA/CURATE.PY propose experiments/TANDMETA/OUT/SIM.JSN
python3 experiments/TANDMETA/CURATE.PY review experiments/TANDMETA/OUT/SIM.JSN experiments/TANDMETA/OUT/REVIEW.JSN
python3 experiments/TANDMETA/CURATE.PY build experiments/TANDMETA/OUT/SIM.JSN experiments/TANDMETA/OUT/REVIEW.JSN experiments/TANDMETA/OUT/PREVIEW
```

The final command MUST fail until you edit REVIEW.JSN. Inspect the proposals
in SIM.JSN, set `reviewer`, then each `decision` to `approve` or `reject`, and
write a meaningful `evidence` note. For a real model batch, check the exact
portrayals against primary sources and record what you checked. Do not treat
a model rationale or its suggested source URL as verified evidence.
Then rerun the build command. All-rejected batches produce no preview.
The review file is an explicit local human signoff mechanism, not authenticated
identity or a security boundary against someone deliberately editing files.

Simulation proposes "Does your character usually wear a cap?" with codes
4,4,0,0 for the four sample characters. It is a HAND-AUTHORED TEST FIXTURE,
not a live model result. The unit test uses synthetic review decisions solely
to compile an in-memory preview: 128 characters / 129 questions, all original
cells unchanged and 124 new UNKNOWN cells. The HTTP test runs a fake local
server, checks the request and parses its response. It is transport coverage,
not inference. No actual Meta model output has been obtained in this workspace.

## Run actual Meta inference on your modern computer

The adapter uses [Ollama's documented /api/chat endpoint](https://docs.ollama.com/api/chat),
JSON mode, a bounded response, temperature 0 and a 16K context. An existing
local Ollama installation and an authorized Meta Llama model are prerequisites.
For example, after reviewing the model terms, on your own computer:

```sh
ollama pull llama3.2:3b
ollama serve
```

`serve` stays running in that terminal; use another terminal for:

```sh
python3 experiments/TANDMETA/CURATE.PY propose experiments/TANDMETA/OUT/LIVE.JSN --local-model llama3.2:3b
python3 experiments/TANDMETA/CURATE.PY review experiments/TANDMETA/OUT/LIVE.JSN experiments/TANDMETA/OUT/LIVEREV.JSN
```

Inspect and complete LIVEREV.JSN, then:

```sh
python3 experiments/TANDMETA/CURATE.PY build experiments/TANDMETA/OUT/LIVE.JSN experiments/TANDMETA/OUT/LIVEREV.JSN experiments/TANDMETA/OUT/LIVEPREV
```

The client only contacts 127.0.0.1 (port 11434, optionally --port), disables
proxies/redirects, and accepts a small explicit list of local Llama model tags.
It has no hosted API or payment support. Ensure your local service actually
runs the official weights, rather than an alias or custom proxy. Model names
and response fields are provenance records, not cryptographic attestation.
Raw response/model/token timing fields and the exact result are retained in
the batch, alongside base and prompt hashes. `mode=local-api` means a response
was received from that service; mocked test responses must never be presented
as live model evidence. Invalid/incomplete output fails rather than being
silently repaired. Revise/retry as a fresh batch if necessary.

No Ollama executable or event credentials were available here. Model quality,
false positives, factual correctness and guessing improvements are unmeasured.
This workflow demonstrates integration and review gates, not a completed
Meta-powered hackathon entry. The event API has no speculative adapter; connect
it only after its actual documentation, access and cost terms are available.
No paid request, account creation, credit redemption or submission occurred.

## Existing checks and recorded results

All 15 new tests pass. They cover schema/UI/answer constraints, unchanged
curated cells, UNKNOWN padding, independent finding rejection, pending review,
missing evidence/reviewer, stale base/review, altered proposals, duplicate
JSON keys, duplicate targets, unsupported models, and mocked HTTP transport.

The existing 53 compiler tests pass with the original 21,576-byte DAT hash
`8af110b129698f054ee9349b0fe84b5401b2b595852862e84f2c240fa4c4377d`.
The existing publication test passes all 201 archive entries, 200 manifest
hashes, runtime/art pins, 43 source identities and platform exclusions.
The test suite needs SOURCE/build to exist for its synthetic capacity fixture:

```sh
python3 examples/TANDINAT/SOURCE/tools/DBBUILD.PY examples/TANDINAT/SOURCE/data/STARTER.JSON examples/TANDINAT/SOURCE/build/TANDY.DAT
PYTHONDONTWRITEBYTECODE=1 python3 examples/TANDINAT/SOURCE/tests/DBTEST.PY
```

DBTEST writes a synthetic SCALE.DAT / SCALE.JSON under SOURCE/build. Those
are test artifacts, never authored game knowledge. TESTPUB checks every file
under SOURCE; run it in a clean checkout before generating build/cache files:

```sh
python3 examples/TANDINAT/TESTPUB.PY
```

The original suite initially had 52/53 passing because its build folder was
absent; after satisfying that prerequisite it passed 53/53. TESTPUB initially
saw a generated Python cache; after removing generated files it passed.
CURATE suppresses bytecode writes when importing the published compiler.

## Assets and publication boundary

This experiment includes no sprites, character portraits, Windows files,
compiler, model weights or third-party datasets. Existing artwork provenance
and licensing remain as documented in SOURCE/NOTICE.TXT; no new rights are
claimed. Character names/trademarks remain their owners' property. Consult
Meta's model license separately; no model license or game asset license is
reassigned. Branch-only preparation, no release or hackathon submission.
