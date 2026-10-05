# Shared WINXT installation and recovery

The completed own-media package has one flat WINXT support folder. Native
Windows Setup copies active drivers/fonts into the ordinary Windows directory.
The installer and optional shell keep their backups under WINXT/BACKUP.
No TDISPLAY, TANDY88 or TSTART root support directory is created.

Six genuine MS-DOS6.22 fresh installs passed INSTALL -> unmodified Windows
DOS Setup -> TSSETUP -> fresh primary WINXT launch -> native Windows exit.
All fonts/drivers match their source hashes. Five graphics profiles use the
qualified temporary TSHELL14 path; experimental text keeps original Program
Manager. All restore their post-Setup INI after exit. See SIX-MODE-RESULTS.json.

The same installed experimental profile then switched through native Setup
to TR56402 and original CGASYS, cold-launched TSHELL, exited, restored every
saved file, and cold-launched original stock-CGA Program Manager. Original
SYSTEM.INI, WIN.INI and WIN.COM remained exact after another native exit.
The shell-ready marker is preserved as OFF; active selector sidecars are gone.
See SWITCH-RESTORE.json. Boot/input-readiness and stale-log synchronization
corrections were test-harness changes only; product bytes did not change.

The installer passes75 safety cases and16 genuine DOS cases, including real
pending SHELLSEL transactions before full rollback and subsequent guarded
launch. Source and compiler log are included; no compiler or OS media is.
The optional shell's path/installer/source evidence is maintained separately.

## Experimental text

TXTMODE.DRV is the unchanged existing experiment, not a TR5-optimized driver.
Actual BIOS03/80-column Windows and native Notepad typing worked, but visible
character and geometry corruption remain. Full DOS-app/grabber switching and
physical hardware remain unverified. See runtime TEXTMODE.TXT and SHOTS/TEXTBAD.PNG.
The intentional 0200,96,48 font key selects separately derived TXTSYS.FON;
do not normalize away its leading zero. All six font selections passed actual
Setup. Original graphics CGASYS is not overwritten. Public STAGE.PY privately
reproduces the derived font from two hash-pinned owner-supplied fonts.

## Public staging and licensing

The public distribution excludes eight Microsoft support files and the derived
TXTSYS.FON. Supply your own pinned Windows3.0 files to distributions/WINXT/STAGE.PY.
It reproduces the exact tested46-file flat runtime from expanded or SZDD inputs.
Do not publicly mirror completed own-media packages. Existing project/DDK
provenance is unchanged; no new grant over Microsoft software is asserted.
No guest disk images, OS binaries, fonts, grabber or stock logo-loader bytes
are included in this source overlay. Selected authentic screenshots are under
SHOTS with hashes/provenance. Detailed private fixture records are not paths
or dependencies in this public tree. QAMET.C/DEF document the read-only observer.
