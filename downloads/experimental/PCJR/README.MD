# IBM PCjr clean Setup — experimental download

**[Download PCJRSET.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/PCJR/PCJRSET.ZIP)** · [Full install/recovery guide](../../../src/pcjr/INSTALL/INSTALL.TXT)

Windows 3.0 real mode, 320×200 in 16 colors, with an existing PCjr memory
expansion and a DOS-reserved video page. This 2026-10-18 packet publishes the
merged clean-install folder: pinned TNDYJR driver, guard/launcher, PCjr-safe
grabber, original XT Pixels fonts and static startup logo. It supports fresh
Windows Setup and changing an existing installation. You supply DOS and
Windows 3.0 media; no Python runs on the PCjr.

## Install

Extract the complete `PCJREXP` folder to **`C:\PCJREXP`**. That fixed path is
required by Setup and the launcher. From plain DOS:

```bat
C:\PCJREXP\JRGUARD
```

Continue only after **OK**. The guard checks that segments 1800h–1FFFh
(the 32 KB video page) are already excluded from DOS allocation. **It does
not reserve RAM.** A refusal means stop before Setup or Windows.

Follow the included `PCJREXP/INSTALL.TXT`: run your own Windows 3.0 Setup,
keep `C:\WINDOWS`, choose Other display, enter `C:\PCJREXP`, and select
**EXPERIMENTAL IBM PCjr 320x200 16 colors**. Choose the PC/XT 84-key keyboard
and appropriate mouse setting. At the end, return to DOS so the guard runs.
The guide covers media staging, narrow dialogs and existing-install changes.

Every Windows start uses:

```bat
C:\PCJREXP\JRWIN
```

JRWIN calls JRGUARD and launches `C:\WINDOWS\WIN.COM /R` only after success.
To undo the display choice, exit Windows, run JRGUARD successfully and use
Windows Setup to restore
your previous display, as described in INSTALL.TXT. PCjr-only DOS video
modes 8, 9 and 0Ah cannot switch away with Alt+Tab; finish them to return.

<details>
<summary>Source, optional checksums and test records</summary>

Installation text and its manifests were refreshed; driver/helper bytes and
saved test records are unchanged. No native rebuild or new runtime claim is made.

All driver, guard, launcher, grabber, font and logo bytes match the recorded
clean-install emulator packet. The [26/26 session](../../../docs/pcjr/INSTALL/SESSION.JSN),
[existing-install conversion](../../../docs/pcjr/INSTALL/CONVERT.JSN) and
[grabber matrix](../../../docs/pcjr/INSTALL/GRJRGRAB.JSN) passed in DOSBox-X.
No fresh Windows boot was run for publication. Physical PCjr memory
expansion, keyboard, mouse/serial input and timing remain unqualified.

The ZIP is **114,921 bytes**, SHA-256
`a5280c3cd1dde76c603e2d0f4f0dc56986aba2a2e5d4bf5a6299cd2321a19cd2`.
`PCJREXP/SHA256.SUM` covers every member. `BUILD.JSN` records exact source,
payloads, fresh builds and inherited emulator qualification. The original packet builds were reproducible; this refresh changes only
installation text and manifests. The merged JRPACK builder's
original runtime pins and all existing release assets remain unchanged.

[Machine and evidence guide](../../../docs/PCJR.MD) ·
[Build/packaging recipe](../../../tools/EXPPUB/README.MD) ·
[Qualification record](../../../tools/EXPPUB/QUALIFY.JSN).
The fonts and static logo are original MIT work. JRGRAB.GR2 is a patched
DDK-derived PCjr grabber, not the retail CGA.GR2; derivative notices remain
applicable. No Windows/DOS media, Microsoft fonts, retail grabber, ROM,
compiler, emulator or credentials are included. The older released PCJR.ZIP
is preserved unchanged; use this separate packet for clean Setup.

</details>
