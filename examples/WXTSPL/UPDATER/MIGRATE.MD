# Zero-SHA default startup and wave updater candidate

RC4 base 8fa96ae8ae05668f2ff993f114af82316bb00b4b. Source candidate only;
native Microsoft C 6.0 /8086 qualification is pending an allocated guest slot.
The user has physically accepted the previously delivered START launch change:
"the windowsXT splash logo boots up a lot faster now after that fix."
No numerical hardware timing was supplied. Do not replace or rerun that kit.

WAVEXT START, CHECK, APPLY and RESTORE have no SHA calls. New APPLY journals use
WAVEXT02 and four literal '-' fields to describe byte-comparison ownership;
the existing argument paths and 0/1/2 status contract are retained. APPLY emits
the physically accepted START launcher. VERIFY and SELFTEST remain explicitly
requested SHA diagnostics. START's existing bounded checks stay unchanged apart
from accepting the new journal syntax. Logo/wrapper/reservation assets unchanged.

Default transactions check plain DOS, path binding, fixed sizes/entry headers,
bounded payload expansion, launcher reconstruction, known old/new/gap rename
states, source/destination byte comparisons and copy/stage/metadata readbacks.
The loader is compared against the installed owned WIN.CNF plus expanded DAT;
the wrapper is compared against the support transport. CNF is not distributed.
Modern-side package/source SHA pins still establish the qualified transport.

Legacy WAVEXT01 and FASTSET01 digest fields are parsed, but their SHA proof is
performed only by explicit WAVEXT VERIFY. Default recovery reconstructs known
starter transformations and compares bytes. New WAVEXT02 has no historical
digest of its original starter. Coherent edits to both the original backup and
derived stage are therefore not authenticated by a digest; that is the explicit
replacement contract, not a claim that skipped hashes verified the files.
VERIFY still checks fixed payload/CNF/loader/wrapper pins and legacy WAVE01
starter digest fields. It is not a modern package or helper verification tool.

Existing active FAST01 records, immutable snapshots and digest fields are kept.
A new migration uses FASTSET02. All five target names are inspected before writes;
the old/new snapshots are checked against known reconstructed launcher formats.
FASTSET RESTORE restores exact prior launchers, staged batches and metadata.
The helper stays capable of reading both journal versions. No original backup
is deleted or overwritten, and no Windows settings/resources are edited.

FASTSET UPDATE Windows-dir support-dir new-WAVEXT-file combines update stages in
one process, with flushed progress. Kit-side WVOLD.EXE and WVFAST.EXE are byte
references for the original RC3/RC4 helper and delivered first START helper.
The installed helper must match one of these or the candidate input byte-for-byte.
HELP02 keeps OLD.EXE, NEW.EXE and a path-bound metadata record. WAVEXT.ZOL/ZNE
are recognized old/new/gap helper rename states, with resumable UPDATE. WAVEXT.PRV
from the accepted update is preserved. An interrupted pre-record journal is
refused and retained for review; it is not silently deleted or guessed away.
FASTSET APPLY/CHECK/RESTORE act on launchers only. RESTORE retains HELP02 and the
new backward-compatible helper. This is intentionally different from restoring
the old SHA-heavy helper by blind COPY. UNDO.BAT documents this behavior.

Use these sources in the next combined candidate, not a new user-facing patch.
Retire old PRECHECK/HELPERS/direct COPY update chaining. No normal VERIFY or
SELFTEST invocation. Preserve installer owner's CPSET/keyboard/PREPXT changes.
FASTPIN.H/PINFAST.PY are no longer runtime/build dependencies for FASTSET.
Native binaries must be rebuilt and qualified from the exact source pins.
