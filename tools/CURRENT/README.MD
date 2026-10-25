# One current Windows XT release

The consumer entry point is `windows-xt`, titled **Windows XT**. Its main
download is `WINXT.ZIP`: `SETUP.EXE`, `README.TXT` and the expanded `WINXT`
folder. The full installer and ordinary Windows Setup use the same files.
Raw SFX alternatives and older software milestones are not current choices.

`BUNDLE.PY` assembles the exact native-qualified main packet and the current
hardware/app ZIPs. TANDYLAB keeps every original application byte and replaces
its optional incomplete toolkit with the same qualified expanded driver source. It calls the native producer, preserving its full-install
qualification gate, and checks the alternate-folder ordinary OEM receipt.
It does not run a compiler, installer or emulator or perform network writes.

```text
python -B tools/CURRENT/BUNDLE.PY --commit <catalog-source-sha> --core <qualified-native-output> --sound <qualified-sound-packets> --out <new-current-folder>
```

The three sound packets are byte-pinned in PRODUCTS.JSN and are also tracked
under `artifacts/win30` at OEMSound commit
`a50637ee6d685f7194ba9a99bc7d8cc593049a3f`. Their anonymous Git raw source
paths remain usable after historical release presentation changes.

`BUILDIN.ZIP` is a developer source-input archive. It preserves the original
Video II packet and two original sound-app packets needed by source rebuilds.
It does not belong in the consumer install tree. The original input names,
bytes and component notices are retained; consumers do not gather them.

Publish only the verified assembled artifacts to the current release. Switch
consumer links and publisher destinations, verify anonymous downloads, then
set superseded releases to draft. Preserve their tags, assets and identities.
GitHub still shows drafts to repository maintainers and retains Git tags;
only the anonymous public release list is consolidated.

The retired softpan auto-publisher must remain disabled. Its source/payload
and oracle verification continue in Actions, without moving the old tag.
