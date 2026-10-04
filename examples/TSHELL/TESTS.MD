# Tandy Start 09 verification

## Exact current runtime

- TSHELL.EXE: 35,907 bytes; SHA-256
  ad3c8394b3391939f19e2a1cf282d89701fe46397a4ce5c4c7a312f37c6babe6
- DOS/SHELLSEL.EXE: 25,953 bytes; SHA-256
  6aa652c9fc77e2e05944b46c055157e97b88a10b963135a4aecf5a01fa71c2fd
- TSINPUT.DLL: 3,082 bytes; SHA-256
  cbb4a851a7f4489945e42c758bb2519415f85270dabe105781acfb056d0521f8
- ../MATRIX/MATRIX.EXE: 14,157 bytes; SHA-256
  0987936c3b80eb9fc5718f3022996514f6885adbdf83cd05128d01bc19de17c8

Only TSHELL.C changes from 08. The DOS helper, exact post-WIN batch block,
input observer and Matrix companion remain unchanged. The repository's base
TSHELL.INI remains unchanged; ADDON.INI settings are opt-in.

## Fresh 09 native checks

Four final Windows 3.0 real-mode cases passed: primary shell and secondary
bar at 160x200x16 and 640x200 monochrome. All 34 observed Start openings have
zero logical gap and no overlap at bar row 178. Actual SDL input exercises
first/last rows, F10/Space/Alt+S, System submenu, Escape/outside dismissal,
repeated openings and secondary Close bar. Each case returns to DOS.

Primary groups/PROGMAN.INI stay unchanged. Secondary outputs match the old08
Program Manager baseline exactly; Program Manager itself reencodes fixture
icons for the display driver. This is not attributed to a TSHELL write.

Two warning-free period MSC6 /G0 /Gw /AS builds reproduce identical runtime
bytes. The scoped ISA audit covers 11,300 reachable instructions with no
post-8088 suspects; imported code and unresolved indirect paths are excluded.
[Full 09 scope and environment](TESTS09.TXT). These tests do not certify every
display/font combination, arbitrary menu item height, or physical hardware.

## Fresh publication support checks

Run the commands in README.MD with Python 3/GCC. The publication overlay was
checked against the current repository's unchanged host-test support:

- Twelve group-parser categories including bounded mutations.
- Twenty-three startup/exit/option/failure cases.
- Saver deadline/activity/block/wrap and idle ownership/hook/cleanup cases.
- TSINPUT.DLL fixed/preloaded code and single shared data, expected exports,
  no local heap, and USER/KERNEL-only import contract.
- 210 selector assertions including seven SELECT and seven RECOVER mutation
  checkpoints, 26 nested interruptions and preservation/refusal behavior.
- Eleven FINISH presentation gates and 21 BIOS mode/page/output simulations;
  transaction source and configured SET paths are unchanged from fixtures.
- 306,822 date-core parser/calendar/fake-clock checks under ASan/UBSan.
  Leak inspection is disabled; these tests do not allocate. No actual host
  or DOS clock setter is called by the host date-core tests.

These portable checks are separate from the native popup test and do not
qualify the whole Windows runtime. Legacy RUNHOST.PY retains its historical
06 label while testing the shared components. No CI pass is implied.

## Historical qualification and physical limits

[Retained 08 scope](TESTS08.MD) records My Computer, date/time, shutdown
recovery/error/veto and success-only FINISH qualification. Those complete
native suites were not rerun on 09. [Retained 06 scope](TESTS06.MD) records
idle saver and earlier controls. Historical MILESTONE.ZIP, MANIFEST.JSON and
EVIDENCE remain unchanged and are not current builds.

The user reported automatic saver operation working on a physical Tandy on
2026-10-04; its exact runtime hash was not read back. This does not establish
09 placement or all idle-hook edge cases. Physical timing, arbitrary
third-party apps, forced termination and all corruption scenarios remain
unqualified. Current native checks use isolated emulation, 640 KB, no
XMS/EMS/UMB, and enforced 8086-prefetch semantics.
