# Windows XT R1 public downloads

These are the exact first-party/overlay ZIPs from the qualified Oct19 R1
work. Neither contains Windows media or the full private installer.

- [WINXT-FIRST-PARTY-R1.zip](WINXT-FIRST-PARTY-R1.zip): 65,989 bytes;
  SHA256 `1631e02735289b8f7f897a9c3d53d796db8411017437950d0d8e48f9f3eeae5b`.
  MIT COM1/IRQ4 wheel driver, three active fonts, matching sources and notices.
- [WINXT-REDISTRIBUTABLE-OVERLAY-R1.zip](WINXT-REDISTRIBUTABLE-OVERLAY-R1.zip):
  49,235 bytes; SHA256
  `53b9cd81d49825ad21d91490d8e741e8b5715f4f99b57368e43a34ad1dd260ed`.
  Nine licensed destination copies, local assembly utility and dependency hashes.

**The overlay is not standalone Windows installation media.** It requires
370 separately supplied exact local files, including licensed Windows 3.0
and separately held private project dependencies. Retail Windows media alone
is insufficient. Local assembly checks all 379 completed files and preserves
the source. Never redistribute the assembled own-media directory.

Read [installation and limits](../../tools/WINR1/START-HERE.TXT) and
[rc.7 release notes](../../docs/RELEASES/RC7.MD). New users needing the existing
own-media install route can continue to use the preserved rc.6 download;
rc.7 is the newer qualified R1 redistributable component/overlay subset.
