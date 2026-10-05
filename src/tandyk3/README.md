# Tandy keyboard driver test candidate 01

Windows 3.0 real-mode keyboard support for the original US Tandy 1000 EX-style keyboard. This is a new DDK-based adaptation, not the incompatible Windows 2 TANDYKBD binary.

## Status

- **Physical raw scan test:** 17 press/release pairs matched the expected arrows, Hold, Break, keypad keys, plus/minus, Enter, Home, F11/F12 and Escape.
- **Emulator:** 74 native Windows tests passed, including scan/virtual-key/character mapping, modifier release ordering, repeats, Print and clean DOS return. A separate assembled normalization harness passed 4,320 transitions.
- **Installer:** 274 host assertions plus sanitizer checks and native 8086 install/rollback/refusal tests passed. Packaged source rebuilds matched the shipped binaries.
- **Still unverified on physical hardware:** Windows key translation, modifier combinations, typematic behavior and Hold-to-Start. Do not describe this as hardware-confirmed Windows support.

This targets Windows 3.0 real mode, not protected/enhanced Windows or an AT/PS2 replacement keyboard. Fixed US/CP437 tables are used. DOSBox-X's Tandy machine does not prove the original keyboard's electrical behavior.

## Files

- `TNDYK3.DRV`: DDK-derived keyboard-driver test candidate, 7,640 bytes
- `RAWKEY.EXE`: plain-DOS port-60h capture utility
- `WINKEY.EXE`: Windows event/API probe; its scan fields are normalized OS codes
- `K3SET.EXE`: conservative DOS 3.3+ install/restore utility
- `SOURCE/`: first-party adaptation, rebuild tooling and probes; no original DDK/compiler
- `K3SRC/`: installer source and tests

The optional kit can live under `C:\WINXT\KEYBOARD`. The shared display/shell
installer does not automatically select this keyboard driver.

## Safe test sequence

Make an offline backup and keep a bootable DOS recovery disk. Exit Windows completely. On another unverified machine, run RAWKEY first and press each key once, unmodified, in this order:

Up, Left, Down, Right, Hold, Break, keypad 7, 4, 8, 2, keypad +, keypad -, keypad Enter, Home, F11, F12, Escape.

After checking the raw codes, run these from the directory containing K3SET.EXE and the exact TNDYK3.DRV, substituting the actual Windows directory:

    K3SET CHECK C:\WINDOWS\SYSTEM.INI
    K3SET APPLY C:\WINDOWS\SYSTEM.INI
    K3SET CHECK C:\WINDOWS\SYSTEM.INI

Stop on any refusal. Read INSTALL.TXT for limits, backups and interruption recovery. The installer selects only `[boot] keyboard.drv`, preserves unrelated settings, and leaves the original driver in place. It does not install the shell, video or sound components.

Start Windows with `/R`, run WINKEY.EXE from the extracted directory using File > Run, and follow TEST.TXT. To roll back after exiting Windows completely:

    K3SET RESTORE C:\WINDOWS\SYSTEM.INI

## Mapping

Dedicated arrows stay directional with NumLock on/off. Shift+keypad 7/4/8/2 supplies backslash/bar/tilde/grave. Hold produces VK_SCROLL; Ctrl+Hold and Break produce VK_CANCEL. The initial Ctrl classification stays latched until release, avoiding mismatched key-up events. Hold-to-Start belongs to the separate shell component.

## Rebuild and attribution

See SOURCE/BUILDING.TXT and INSTALL.TXT. Existing licensed DDK/compiler inputs and DOSBox-X are required; hashes reject mismatched DDK sample inputs. No tools are downloaded by these scripts. Probe and installer build scripts require explicit `--tools` and `--dosbox` paths. For native installer tests, run TESTS.PY, build the resulting K3SRC/qa copy with BUILD.PY, then invoke `NATIVE.PY --dosbox /path/to/dosbox-x`.

The included runtime is the exact tested candidate; K3SET refuses a different identity. Rebuilding still requires appropriately licensed original inputs. No additional rights to Microsoft materials are granted.

TNDYK3.DRV is derived from Microsoft's Windows DDK keyboard sample. Original Microsoft source and tools are not included. See NOTICE.TXT before redistribution. Runtime identities are recorded in MANIFEST.JSON.
