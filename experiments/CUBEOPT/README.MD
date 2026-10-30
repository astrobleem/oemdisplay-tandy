# Cube optimization candidate

This directory preserves the native-tested math and drawing optimization as
an unreleased development candidate. `examples/CUBE/SOURCE`, `ACCEPT.JSN`,
accepted binaries and release packets retain their accepted bytes. The
existing Cube release workflow still runs its full source/runtime/receipt
and tamper gates, assembles the accepted packet and replays its source ZIP.

The earlier PR placed candidate code over that accepted source tree.
`BUILD.PY` legitimately failed its accepted source hash before the gate could
report the other changed files. Adding `CUBERECT.H` to the candidate builder
is necessary, but cannot make its old binary and receipts qualify new code.
The correction restores the accepted tree and checks this candidate
independently. No acceptance pin or gate exception has been introduced.

The ten native compiler inputs in `SOURCE` are byte-identical to the tested
`2c50ab5d1759f84927640a3e06e755534e5f08d3` snapshot. `CANDIDAT.JSN`
records separate candidate source/evidence pins and the explicit status
`PARTIAL_NATIVE_NOT_RELEASE`. It binds those inputs to the native build and
matched TR51616/TR53216 render/input, cleanup and paired scanout receipts.
`CHECK.PY` verifies that binding; `TESTCHK.PY` rejects changed or merely
repinned source, altered receipts, missing evidence and a ready label.

From the repository root, use fresh output directories:

```text
python -B experiments/CUBEOPT/SOURCE/RUNHOST.PY --out NEW-OPT-HOST
python -B experiments/CUBEOPT/CHECK.PY --out NEW-OPT-CHECK
python -B experiments/CUBEOPT/TESTCHK.PY --out NEW-OPT-TAMPER
```

The candidate native builder is `SOURCE/BUILD.PY`. It needs the explicit
external MSC6 toolchain, DOSBox-X and coordinated emulator lease described
in [Cube build guidance](../../examples/CUBE/README.MD). Candidate output
must stay in a fresh external folder. The original native wrapper and guard
used for the measurements are retained with the build receipts.

See [drawing results and limits](../../examples/CUBE/RENDER.MD) and
[current TR51616 comparison](../../examples/CUBE/EVIDENCE/RNDTR5/TR51616-VALIDATION.TXT).
The original accepted packet retains its broader native qualification;
this candidate still needs the remaining display, UI, installer and package
qualification before replacing it. CI success checks this separation and
the recorded partial results; it does not promote the candidate or publish
a release. BOR/Mesen work is independent and its resources were not used.
