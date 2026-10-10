XTMODE - unpublished switcher transport revision, 2026-10-10

Original C89 DOS 3.3+ / 8086 mode selector; MSC6 /AL /G0 builds passed.
Existing first-party SHELLSEL transaction primitives were adapted with their
permission notice retained. New implementation and test sources are MIT.
No Microsoft glyph bitmaps, Windows binaries, compilers or DOS images included.
GENPINS reads only original first-party driver/font/art numeric contracts.

Implemented commands: LIST, MENU path, INSTALL path source-folder, SET path mode,
CHECK path, VERIFY path, GUARD path, UNDO path, RECOVER path, ACCEPT path, FORGET
path. Path means absolute SYSTEM.INI. Modes: 32016,6404,16016,3204,6402,TEXT.
TEXT requires /TEXT or typing TEXT in the menu and retains known corruption.

INSTALL copies the 15 distinct original mode resources once with a journal,
verified rename and exact source comparison. It changes no active INI, loader
or DOS boot file. Existing wrong resources refuse. A partial copy is removed
only if its bytes match the journal's source prefix. Incomplete metadata remains
for inspection and blocks startup. READY records complete resource installation.

SET changes the driver, three fonts, common grabber and display description.
Only the controlled display.drv line is canonicalized to the form required by
the unchanged wave parser. UNDO restores its previous complete line and the
previous tuple, retaining later unrelated keyboard/mouse/shell/config bytes.
Repeated SET/INSTALL are no-ops. Undo history is one level. ACCEPT keeps the
current mode and removes completed history before Windows Setup. FORGET undoes
history and disables the copy marker before the whole pre-install rollback.

Generated WINXT and packaged TSTART perform mode recovery and GUARD before
the existing RESERVE invocation. The original wave patcher preserves that
prefix and its existing wave/static/XTCLEAN routes. MODES installs resources
and then provides the DOS menu/command. No Python is required on the vintage PC.

Default resource checks inspect lengths, module/face identities, NE resources,
FNT height/ascent/character/bitmap boundaries and glyph advances. VERIFY scans
selected first-party payload CRC32 explicitly. No default SHA scans added.
Owned CGA.GR2 and common WIN.COM retain cheap layout checks and remain private
dependencies; this does not eliminate non-font Windows dependencies.

Host verification: 335 mode checks, 1,890 resource-copy checks, actual TINST
batch emitter and unchanged WAVEXT parser checks. Native MSC6 compilation,
resource copying, six selections, UNDO/interrupted recovery, guarded startup
refusal and exact 120-file preimage rollback passed. All five cold graphics
launches passed 224 advances and native normal/dialog framebuffer comparisons.
Actual Windows WinExec DOS-app tests refused CHECK, INSTALL, SET, RECOVER,
UNDO, GUARD, VERIFY, FORGET, ACCEPT and MENU; 254 preimage files stayed exact.
The Win16 WINGUARD presentation log has a known near/far string formatting
defect; the DOS stdout/error and byte comparisons carry the readable evidence.
Its source fix is pending optional native rebuild. Production bytes unchanged.

Final emulator gates passed: corrected-catalog Setup 6402/TEXT, native
production/diagnostic builds and fresh production default, zero-SHA default
and explicit /VERIFY. Native and failed-run records remain immutable. Current
guide text and manifests are updated; DOCPINS/REBIND.PY refreshes only document
hashes/sizes in the measured helper, with exact unchanged executable code.
The refreshed data-table binary was not rerun in a guest. QUALIFICATION.JSON
binds current artifacts to the measured implementation and host data proof.
This is a private candidate; no publication or hardware claim is authorized.

The current validated common WIN.COM is 7,879 bytes: private WIN.CNF 3,456,
original XTSTATIC.LGO 361 and original WXTSPL01.RLE 4,062. CGA.GR2 remains
private support. RC5 uses an 8,398-byte common loader with private CGALOGO.LGO
880 bytes instead; changing baseline requires resource contracts, installer,
PREPXT ownership pins and native startup/rollback requalification. It is not
a packaging-only change. The existing wave bytes and seven fonts are unchanged.

WINQUERY/QUERY and WINGUARD/DOSGUARD are original test-only native probes.
Actual DOS AX1600=1600 and AX4680=0000 demonstrate the real-mode guard route;
the earlier native interrupt stubs remain separate evidence. Test binaries
never become runtime payloads. Host test programs: TESTHOST, TESTCOPY, TESTLAUN.
Supply explicit compiler, private fixture and fresh output paths. No private
Windows bytes, compiler, emulator or test binaries are included in source kits.

The final kit fixes a stale RC5 OEM catalog in the failed Setup clone. Before
any future lease, mandatory host preflight compares all six catalog rows,
every source/helper byte, owned CGA.GR2/WIN.CNF and mounted paths. A previous
25-second job incorrectly combined two compiler/linker builds; production
completed about 20 seconds into it, leaving only a few seconds for diagnostics.
This is an incomplete timed build, not evidence of a compiler error. New
production and diagnostic builds have separate 45-second bounds. Default
preparations have 60-second bounds; explicit VERIFY has a 150-second bound.
Final native builds/defaults/VERIFY and Setup 6402/TEXT passed. Diagnostic
default counted zero SHA blocks in both phases and zero output readback;
production default separately passed exact bytes/preimages. Defaults took
about 42 host seconds, explicit /VERIFY 139, under the saved emulator settings.
These are not hardware estimates. docs/QUAL/RC6.JSON binds preserved evidence.
Current document pins were refreshed on the host; executable code is unchanged.
