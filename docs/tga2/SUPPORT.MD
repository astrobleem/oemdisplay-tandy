# Video II support integration

The candidate packet includes the existing original `XTCSYS.FON`,
`XTCFIX.FON` and `XTCOEM.FON` fonts, the expanded `CGA.GR2` grabber, and the
existing `XTSTATIC.LGO` / `WXTSPL01.RLE` startup pair. Its driver and DOS
helper executables retain the accepted r2 bytes. `PREPINF` now only checks
packet completeness; installation does not require it.

The former CGA font names came from the inherited 640x200 Setup profile.
The `200,96,48` tuple remains unchanged. Original fonts with matching
metrics already existed in `distributions/WINXT`; this change selects and
packages them rather than gathering stock fonts from Windows.

## Local packet reproduction

This host-only step uses the accepted r2 ZIP for its unchanged executables,
the existing repository support assets, and root `CGA.GR2`. It accepts the
uploaded mode-A SZDD file or its exact expanded bytes. Malformed input or
different runtime/support bytes are refused before creating output.

```text
python -B src/tga2/T2PACK.PY --accepted PATH/TNDYV2.ZIP --out NEW-DIRECTORY
python -B src/tga2/T2PACK.PY --verify NEW-DIRECTORY/TNDYV2.ZIP
```

`T2PINS.JSN` binds accepted executable/support bytes and the historical
input notice. The current packet uses the corrected notice from source.
`T2PTEST.PY` covers closed membership, deterministic output, original fonts
and logos, bounded SZDD handling, changed input refusal and metadata drift.
The host packet record deliberately makes no native-test assertion.

## Native result

[T2SUP.JSN](T2SUP.JSN) binds the exact candidate and integration sources.
On an isolated SL/2 clone, Windows 3.0 maintenance Setup selected all three
XTC fonts and the grabber from the packet. Their installed bytes matched.
Setup built `WIN.COM` with both bundled startup assets, and guarded
`WIN /R` reached the [Video II desktop](T2SUP.PNG) in BIOS mode 0Ah, settled
for 40 seconds. T2RESV succeeded before Setup and before Windows.

The installed stock fonts and grabber had been removed from the private
fixture before Setup; the new fonts/logos were not preinstalled. The source
image remained unchanged. The owned emulator stopped and released its
shared lease. This checks support integration and startup, while the
existing rendering qualification remains separate. Physical hardware and
Windows 3.1 were not tested.

The old Setup/staging receipts remain bound to exact r2 INF, batch and
notice snapshots under `src/tga2/HISTORY`; they are not claims about this
new support selection. `T2ITEST.PY` checks both scopes.

Publication of this candidate is pending approval. Existing release assets
have not been replaced and the current download URL still names r2.
