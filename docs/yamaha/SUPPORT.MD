# Yamaha support integration

The current source packets are `downloads/experimental/yamaha/PC1.ZIP` and
`YAMAHA.ZIP`. Each includes its unchanged accepted driver, the original
XTCSYS/XTCFIX/XTCOEM fonts, expanded CGA.GR2, XTSTATIC.LGO and WXTSPL01.RLE.
Their Setup records select those assets and need no external support files.

`tools/YAMPACK/PACK.PY` reproduces the packets from the accepted driver
archives and existing support assets. It verifies exact driver/support
identities, bounded SZDD input and closed packet membership. It creates a
new output directory and never runs an installer or writes installed Windows.

```text
python -B tools/YAMPACK/PACK.PY --profile pc1 --out NEW-PC1
python -B tools/YAMPACK/PACK.PY --profile b800 --out NEW-YAMAHA
python -B tools/YAMPACK/TEST.PY
```

The host record explicitly makes no native-test assertion. The two profiles
have different memory apertures; neither the driver nor Setup detects them.
Historical Candidate03 source and qualification records remain intact.

## Native result

[SUPPORT.JSN](SUPPORT.JSN) binds both exact packets and integration sources.
Native Windows 3.0 maintenance Setup selected the correct driver and three
XTC font aliases for each profile. Installed font/grabber/driver bytes matched
both packets exactly, and WIN.COM contained XTSTATIC.LGO and WXTSPL01.RLE.
The selected fonts and grabber were absent from Windows before Setup.

Each Setup output was extracted to a private folder and started in the same
installed DOSBox-X binary recorded by the compact evidence. The existing
read-only metrics probe reported real mode, 160x200 and the expected original
System/OEM metrics; both runs returned to DOS without loader errors. The only
instrumentation was selecting the metrics probe as the shell after retaining
the unmodified Setup output. No compact fonts or driver patches were applied.

This is software/API startup validation. It does not qualify Yamaha scanout,
physical PC1 hardware or RGB/SCART output. The original B800 scanout evidence
remains a separate historical result; it was not rerun or relabeled here.

The recovered paths, emulator/probe identities, native selected aliases and
installed bytes are in the receipt. Source images remained unchanged. All
owned test processes stopped and released the shared lease.
