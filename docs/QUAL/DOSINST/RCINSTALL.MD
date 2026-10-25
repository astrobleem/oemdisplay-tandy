# DOS-native Windows XT installer qualification

The current WINXT.EXE package prepares and installs the desktop on the DOS
computer. Its native recipe includes the canonical SOUND.DRV and current
shell, alerts and clients: 49 runtime members, 369 fresh outputs and 82 update
outputs. Consumers use the [desktop setup guide](../../DESKTOP.MD).

The current qualification used PREPXR 83544 bytes, SHA256
`98f0a5b0fa42670109138e1bc7d313a1804786768e4e550861cdd0a462915b69`.
The exact delivered containers are:

| Asset | Bytes | SHA256 |
| --- | ---: | --- |
| WINXT.ZIP | 746928 | `ce7698e0595d2add6e8e8f550b144bcb5dd996c0ee49f8448373f76065f6dbff` |
| WINXT.EXE | 830472 | `292c28c67b97c3fe611ca8c5171a92581153bb6a17924adef7f8cf53f8d16ea4` |

| Current native case | Actual result |
| --- | --- |
| Fresh preparation and valid inputs | Reused a complete installed Windows/media-cache fixture; the current helper checked all 284 expanded input streams and all 369 staged outputs. Preparation 1057.7s; normal finisher and guarded desktop through 1201.3s. |
| Managed update | All 82 prepared outputs and 12 installed component identities matched. Preparation 181.6s; desktop through 328.7s. The managed sentinel and boot files were preserved. |
| Cold launch | A copy of that successfully updated installation booted with no attached floppy and Windows absent from PATH. C:\STARTXT reached the desktop in 103.9s including the graphics observation interval. |
| Corruption and retry | Byte 100 of the 545-byte cached 123.PIF was changed without changing its length. The current helper refused its CRC and removed the bad tagged-cache copy. A normal retry gathered the original file and reached a deliberate later 3270.TXT directory guard. All 9 assertions passed in 245.2s. |

The fresh and valid-input roles reference the same actual current run.
Windows Setup and media gathering were not repeated. The earlier full Setup,
disk-gathering and 367/80-output tests remain historical evidence in Git at
`57d72c8197c427899772ebc334ae67dedffaf900`; their existing logs and captures
are unchanged. No earlier receipt is relabeled as a current-helper test.

Each positive case continuously observed graphics mode 9 for at least 60s.
The final captures were visually checked as the actual Windows desktop with
XYCTL in the foreground. The interval includes graphics startup; it is not
described as 60s of independently timed settled desktop. Installed SOUND.DRV
is 9752 bytes/SHA256 `ef501c64b80559ab8cc729c32bd36647a3c041bcf08ccf50cd958bb60065eccd`.
The current TSHELL, TSINPUT, TCHIME, XPCHIME, TEXIT, TP and FIXXT identities
also match the delivered payload. There is no Windows-root SOUND.DRV shadow.

Both fresh and update preserved WIN.INI byte-for-byte. SYSTEM.INI changed
only the sound.drv value spelling to SOUND.DRV. Boot files, the update
sentinel and unrelated settings were preserved; no staging files remained.
The corruption case preserved the complete Windows tree and original media
file, repaired only the tagged cache and withheld SETUPXT.BAT. Its DOS
capture includes the fixture's B: diskette prompt after the completed batch;
the refusal/retry logs and strict filesystem readback establish its result.

All owned emulator processes stopped and released the shared lease after
each case. Independent host readbacks passed 23/21/21/18 checks respectively,
including stable identical FAT copies, exact files, source/package pins and
an independently free lease. Tests used an 8088/640 KB Tandy HX emulator,
DOS 6.22 and Windows 3.0 real mode; physical hardware and CF writes were outside
these runs.

[RC8.JSN](RC8.JSN) binds the current qualification. [FULLXT2](FULLXT2/README.MD)
contains its exact logs, captures, public receipt projections and strict
readbacks. The source reconciliation proof links native source 8320cf2,
rebase f01fcdb and final source 57d72c: the tracked expanded CGA input replaces
the former loose SZDD input while all 57 collected entries, compiled inputs,
helper, ZIP and SFX remain byte-identical. The publisher's existing exact
helper/output/container gates remain active.
