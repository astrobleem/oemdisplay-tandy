# Windows XT first-party wheel and font kit

This collection contains the new COM1/IRQ4 Windows 3.0 real-mode mouse/wheel
driver and the three active XT Pixels bitmap fonts. Each component retains
its MIT notice. It is a component kit; an owned Windows 3.0 installation and
a compatible wheel client are separate dependencies.

- `mouse/WHEEL.DRV`: 8086/8088, COM1 03F8h/IRQ4, 1200 baud 7N1, two buttons,
  immediate ordinary three-byte mouse delivery and optional signed wheel
  nibble. Build from the included assembly with `python build_driver.py`
  inside `mouse`. Open Watcom 1.9 is an external build tool.
- `fonts/XTCSYS.FON`, `XTCFIX.FON`, `XTCOEM.FON`: the byte-identical active
  fonts used by the qualified private profile. The original glyph generator,
  numeric format contract and its MIT notice are included.
- `QUALIFICATION.json`: final exact identities, passed scope and limits.
  The complete private install/test archive is a separate local deliverable.

The new driver is explicitly not described as clean-room: interface and
prologue references were inspected by its integrating author. Its authored
implementation, decoder and linked objects are first-party; no DDK macros,
implementation, runtime object or SDK import library is linked into it.
See `mouse/PROVENANCE.md` for the exact distinction.

No Windows/DOS media, DDK/SDK source or headers, derived display/keyboard
driver, emulator, ROM, guest disk, WXTWHL client or paired TP is included.
The reviewed bridge/TP records did not supply an applicable explicit license
grant, so their terms have not been inferred from the wheel driver's MIT
notice. The complete own-media installer stays private.

For font regeneration, run from this kit's root into a new directory:

```text
python fonts/generator/HOST.PY BUILD.PY --out NEW-FONTS
python fonts/generator/HOST.PY TEST.PY --out NEW-FONTS
```

Python 3.8+ and Pillow are host dependencies. The generator's original
`CGASYS.FON`, `CGAFIX.FON`, `CGAOEM.FON` outputs correspond byte-for-byte to
the collision-free installed aliases `XTCSYS.FON`, `XTCFIX.FON`,
`XTCOEM.FON`. `fonts/ORIGINAL-README.MD` is the historical full-font-project
documentation; its broader packaging/native-test commands refer to that
original project, not to additional components included here.

The decoder harness build creates DOS-compatible `DTEST.EXE` and
`VECTORS.BIN`. Run `DTEST` in DOS with the vectors beside it. Its already
passed executable/vector identities are recorded; no new emulator is needed
to inspect or reproduce the host build.

No publication or physical-hardware qualification is implied by this packet.
