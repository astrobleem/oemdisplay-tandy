# DOS-native Windows XT installer qualification

WINXT.EXE performs fresh or update preparation on the 8088 DOS computer,
then reserves video memory and hands control to the existing guarded
Windows installer. It supplies the grabber, fonts, artwork and project
helpers. Windows itself comes from its installed directory or original disks.
There is no consumer Python step, host conversion or support-file collection.
The current instructions are in [desktop setup](../../DESKTOP.MD).

The native recipe produces the same 367 fresh / 80 update files as the
developer reference, with the qualified launcher/finisher corrections and
current guide text. All three CGA.GR2 destinations use the bundled module.
The supplied SZDD module expands to the existing qualified 2,104-byte grabber.
The HPXY and keyboard rendering/input driver binaries are unchanged.

| Current native check | Observed result |
| --- | --- |
| Fresh media gathering | Cancellation after the first disk retained its verified cache; resume gathered the remaining files on DOS. Expanded and mode-A SZDD input were exercised. |
| Fresh preparation | 367 files match the current reference exactly; 1,122.5 seconds including boot/controller from the complete cache. |
| Setup continuation | A bounded controller stop during graphical Setup was classified incomplete. Normal C:\SETUPXT recovery completed Setup and the finisher without repeating preparation; 608.3 seconds through a 60-second settled final GUI. |
| Managed update | Both Windows grabber copies were absent. A damaged managed TP payload and changed guide files were repaired; all 80 files match, unrelated sentinel/INI and boot files preserved, no staging temporary files left. Preparation 136.9 seconds; 272.9 seconds through settled GUI. |
| Cold normal launch | C:\STARTXT with Windows absent from PATH completed its checks/reservation and reached the visible GUI; 97.5 seconds through the 60-second settle. |

An unchanged cold-staging update fixture measured 307.1 seconds before the
byte-oriented CRC shift and 235.2 seconds after: 71.9 seconds / 23.4% less
preparation time. The 136.9-second managed repair is a separate reuse case.
The actual CRC implementation also matches zlib on 17 vectors. The native
preparer uses indexed ZIP lookup and skips a second write/readback pass for
already verified matching outputs.

The guarded DOS wrapper now executes C:\WINDOWS\XTTEST.COM by absolute
path. Its accepted 1,071-byte result rebuilds exactly from the source under
tools/DOSINST; the frozen wave package's source and binary stay unchanged.
The finisher compares the entire wrapper because its changed middle bytes
are invisible to the old first/last sample check.

[RC8.JSN](RC8.JSN) binds the package, selected boot values, installed files,
raw logs and captures. RCFHASH.JSN / RCUHASH.JSN contain only output identities,
including private OS-file hashes, not OS contents. The final archive differs
from the native test containers only in README.TXT; all 52 other
members, including its helper, are identical. The publisher rejects incomplete/error-bearing
receipts and changed package bytes. The original premature controller result
was retained privately and explicitly adjudicated incomplete, never accepted
as an install pass.

Tests used an 8088 / 640 KB Tandy HX emulator with DOS 6.22 and Windows 3.0
real mode. No physical-machine qualification or CF access is claimed.
