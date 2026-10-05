UTILDOS1 - QUALIFIED DOS STATUS POLISH AND OPTIONAL GUIDES
5 October 2026. Isolated experimental kit based on repository c6ee4b0.

WHAT IS INCLUDED
- WXTSPL.EXE: named file states in CHECK, followed by the applicable APPLY,
  RESTORE or safe-launch guidance. Original hashes, transactions and guards
  are unchanged. Keep the matching WXTSPL01.RLE artwork alongside it.
- WHEEL.EXE: compact final RAW summary with counts, errors, interpretation,
  restoration/reboot guidance, and the Windows-scrolling boundary together.
  Detailed raw output and every existing I/O/consent guard remain intact.
- DOCS/HILLS.TXT: Control Panel is the recommended wallpaper setup route;
  manual WIN.INI editing is an advanced alternative. This is a guide only.
- DOCS/WINXT.TXT: a short installer workflow preceding the existing detailed
  steps and limits. This is a guide only; no installer executable changed.

USE
These are optional trial copies. Read the relevant DOCS guide first. Run
DOS utilities only from plain DOS after exiting Windows completely.
Do not overwrite a working utility or historical bundle to try this kit.
The Hills guide applies to the existing HILLS bitmap package, and the WINXT
guide applies to the existing combined WINXT installation package. Their
artwork, installation sources, drivers and installed settings are not here.

QUALIFICATION
Both exact executables were compiled with Microsoft C6 /G0 /AS /W3 /Od.
Native tests used Tandy, enforced 8086_prefetch, 640 KB, no EMS/XMS/UMB.
WXTSPL passed CHECK/APPLY/repeated APPLY/RESTORE/repeated RESTORE, unknown-file
refusal and interrupted recovery that preserved an unknown staged file.
The exact original WIN.COM returned byte-for-byte; unrelated sentinels and
source input remained unchanged. A second native build was byte-identical.
The host splash suite passed 1,048 state/mutation/idempotence/corruption cases
under ASan/UBSan, including named-state and next-command assertions.
WHEEL passed native synthetic packet /TEST and existing-driver /API checks.
Ten host ASan/UBSan mock cases checked refusal, cancellation, UART changes,
escape, full capture/restoration, and UART errors. The final summaries cover
zero candidates, 82 synthetic wheel events, and errored capture. Accepted
capture routes retain exactly 11 UART setup/restoration writes; refusal
routes perform zero writes. Detailed evidence is under EVIDENCE.

LIMITS
WHEEL's new raw-summary presentation was exercised with mocked UART data;
this kit makes no new physical serial-mouse/UART or Windows-scrolling claim.
Native /API observed zero wheel motion in its emulator observation window.
Physical Tandy/card testing and cycle-exact timing remain separate acceptance.
WXTSPL cannot guarantee FAT integrity during arbitrary power or media failure.
The two revised guides were reviewed as wording-only changes; they do not
claim a new native installer or Control Panel test. Existing cautions remain.
Historical packages, payload pins, installers and all stock OS files stay
unchanged. No Windows/DOS loader, SDK/compiler, font or guest image is bundled.

REBUILD / RECHECK
Use your own licensed C6 tree (BIN/CL.EXE, BIN/LINK4.EXE, INCLUDE and LIB).
From this kit on Linux:
 python3 QA/DOSBUILD.PY --repo TOOL_TREE --dosbox DOSBOX_X --out NEW_BUILD
Serialize DOSBox-X runs with the shared emulator lock used by your test setup.
Native runtime regression requires an owned, recognized stock WIN.COM:
 python3 QA/UTILRUN.PY --bin BIN --stock-win-com OWNED_WIN_COM
  --dosbox DOSBOX_X --out NEW_NATIVE_TEST
This runner creates disposable copies; never point it at a mounted card.
Source-specific host/build instructions are under SOURCE. The WXTSPL test
needs the existing first-party src/splash/assets/TNDYLOGO.RLE from the repo.
Use QA/TESTPUB.PY to verify this kit's exact manifest and payload allowlist.
