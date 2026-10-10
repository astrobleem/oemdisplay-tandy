# Windows XT rc.6: static logo and DOS mode menu

Final emulator gates passed: native production/diagnostic builds, production
default, instrumented zero-SHA default, explicit /VERIFY and Setup 6402/TEXT.
docs/QUAL/RC6.JSON binds current artifacts to the preserved native evidence.
Host package/FAT12, exact source/runtime pins and reproducibility checks pass.
Chad authorized this release candidate; original hardware is not qualified.

Seven original MIT XT Pixels fonts remove the Windows font setup-media
dependency. Original 361-byte XTSTATIC.LGO removes the owned CGALOGO.LGO
dependency. Only matching owned CGA.GR2 (2,104 bytes) is gathered. Existing
DOS/Windows, SYSTEM/WIN.CNF, Setup, kernel and other non-font components remain
necessary. Setup creates the 7,879-byte common WIN.COM; the slow wave is unchanged.

Default preparation performs size/I/O/structural checks. Source-coupled
instrumented default measured zero SHA blocks in both phases and zero output
readback; production default separately passed byte/preimage checks. Emulator
host times were about 42 seconds for default and 139 for explicit /VERIFY.
These are not physical 8088 estimates. /VERIFY remains optional diagnostics.
No Python/compiler is needed on the vintage PC; font generation is host-side.

Run INSTALL at the floppy root, optionally supplying matching owned support
media. Confirm a fresh C:\WINXT, then C: / CD \WINXT / INSTALL. In Windows
Setup select Other display, C:\WINXT and Complete Changes; select CONFIG.SYS
option 3 (no changes). Exit Windows fully before MODES. Choose a mode or U
to undo one previous selection. Guarded WINXT/TSTART performs RECOVER before
startup. Unknown/incomplete journal state refuses startup; keep source and
sidecars. Whole-install rollback uses the printed BACKUP\B001\RESTORE YES.

Documentation pins were refreshed on the host. DOCPINS/REBIND.PY reproduces
the update from the preserved measured PREPXT base; all 59 binary pin rows
match source. Only three guide hashes/sizes and the manifest digest changed.
MZ header, relocations, executable code, paths and non-document data stay
byte-exact. The refreshed data-table binary was not rerun in a guest. Native
evidence and failed-run records retain their original exact-byte scope.

At 160 pixels wide stock dialogs can clip and menus can wrap. TEXT is opt-in
with known extended/adjacent-cell renderer corruption; Setup acceptance is
not a TEXT GUI quality claim. Windows,
compiler/emulator binaries and owned CGA.GR2 must not enter source kits.
