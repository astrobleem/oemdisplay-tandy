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

Native installation/startup verification for these complete packets is
pending a compatible Yamaha emulator binary or fixture. The available
Windows headless 86Box source has a TODO for 160x200x16 scanout and a fixed
B800h mapping; it cannot qualify the PC1/B000h profile. A generic CGA screen
will not be reported as Yamaha scanout. Publication is pending approval.
