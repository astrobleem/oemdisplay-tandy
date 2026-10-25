# Current FullXT native evidence

[RC8.JSN](../RC8.JSN) contains the accepted current cases. INDEX.JSN binds
every evidence file. FRESH, UPDATE and COLD contain the actual Windows
desktop captures; NEGATIVE contains the current-helper refusal and retry.

RESULT.JSON files omit only the local emulator installation path. Each has
a public_projection field retaining the exact original private raw-record
identity. The unchanged READBACK.JSON files refer to those original raw
identities; public file identities are recorded separately in INDEX.JSN.
Test values, timings, binary hashes and cleanup claims are unchanged.

FRESH is one actual 369-output run, also used for native_valid_inputs because
it checked all 284 expanded Windows input streams. It reused an existing
complete installation/cache. This is not a new Windows Setup/media-gather
run. The previous 367/80 qualification remains in Git history at 57d72c;
its older raw files outside this directory are preserved.

SOURCEPINS.JSON contains fingerprints only. RELOPROF.JSN and RELOREAD.JSN
record the source rebase and tracked expanded-grabber reference. FINALMAP.JSN
links 8320cf2/f01fcdb/57d72c and independently checks identical compiled input,
helper and all 57 delivered entry bytes. PUBBEFOR.JSN/PUBAFTER.JSN retain the
exact manifest delta. No source-only metadata change is presented as a new
native run.

The three GUI captures show the actual Windows desktop with XYCTL in front.
They do not separately establish visibility of the primary shell window.
The 60s interval starts at continuously observed graphics mode 9 and may
include startup. The negative DOS capture includes a fixture B: prompt after
its completed batch; BAD.LOG, RETRY.LOG and the nine filesystem assertions
record the tested refusal and recovery.

Only logs, screenshots, receipt metadata and hashes are included. Images,
prepared OS trees, Windows/DOS media, toolchains and emulator bytes stay
private. No physical-machine result is claimed.
