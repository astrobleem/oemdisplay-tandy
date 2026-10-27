# Unified panning acceptance

The reviewed runtime source checkpoint is
`38497b48303faaea50b9472d7ae19e341bfaa135`. Accepted bytes and the closed packet
inventories are in [FINAL.JSN](FINAL.JSN); [REVIEW.JSN](REVIEW.JSN) records the
independent code/package review. These are native emulator results, not physical
hardware or physical-mouse testing. Input used headless scan codes and native
Windows control APIs.

| Family | Final native scope | Result |
| --- | --- | --- |
| PCjr vertical viewport | Guarded auto-install, shared settings, Apply/Cancel, pan/Home, OFF/ON, DOS return | PCJRR.JSN |
| Fixed 320x200 workspace | One owner, real Clock movement/Home, repeat settings, persisted opt-in/OFF/ON, exit | FIXEDR.JSN |
| CGAPAN | Native Setup, stale-owner rejection, seven busy Paintbrush chords, End edge, compact settings, 20 rounded 24, exit | CGAPANR.JSN |
| CGA100 fixed | Compact shared settings, five-pixel Clock movement/Home, exit | CGA100R.JSN |
| HPXY with TSHELL | Real radio controls, software/hardware 8x4 pan, preserved unapplied edits, Apply 200/Cancel 500, normal exit with input/wheel/clipboard helpers | HPXYR.JSN |
| Canonical full setup | Native FRESH381/UPDATE93 preparation, normal repair/Computer registration, guarded STARTXT, installed-byte preservation and normal Windows exit | SETUPR.JSN |

[EVIDENCE.ZIP](EVIDENCE.ZIP) contains raw native logs/states/captures and owned
emulator lease receipts. It excludes OS images, OS binaries, ROMs, prepared guest
trees and compilers. Exact installed observations and final native installer
transactions are bound separately: a guard-only DOS rebuild does not relabel an
older UI run as a test of its new installer bytes. Unchanged drivers reuse their
accepted proof; the composer also checks every preserved driver/app/support byte.

The successful canonical installation phase is retained separately from its
failed radio-notification probe. The corrected continuation uses actual button
key-down/up, verifies radio state, and starts through normal STARTXT without
another repair. It passes all settings/Cancel/shutdown checks. Failed receipts
remain failed and are retained with their actual cleanup outcome.

Integration fixes include the full-repair path alias, a bounded INI startup line,
exact current grabber-metadata compatibility in CPSET, and idempotent validation
of a correctly located TGCLIP token in either startup order. All preserve the
accepted display/grabber bytes and unrelated settings. Current source/receipts
have explicit byte-preserving Git attributes for clean-checkout reproduction.

[COSTS.JSN](COSTS.JSN) records sizes and native memory observations. XTPAN plus
the shared DLL uses 26,336 resident bytes on the PCjr and fixed-workspace fixtures.
Together they occupy 29,444 disk bytes versus 29,199 previously. PANCFG is transient;
there is one appropriate owner, with no extra resident broker. DLL fixed code/data
are 1,301/288 bytes. Ordinary CGA320/640 retains its early color fix and exit.

[GATES.JSN](GATES.JSN) covers changed inputs, missing native coverage, mismatched
results and incomplete installer observations. [CATALOG.JSN](CATALOG.JSN) checks
all 17 ancillary inputs and documentation overlays; the full BUNDLE producer also
revalidates the gated core before emitting the 23 current assets.

No push, PR, merge or release update was performed for this work.
