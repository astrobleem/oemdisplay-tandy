# Shared PAN controls and settings

PAN is the public application. A transient dispatcher detects the installed
driver and starts one internal owner. This directory supplies shared settings,
an adaptive dialog for 160x100 and 320x200 views, bounded queued keys and owner
routing. Only the selected owner and shared key DLL remain loaded; other
presentation engines stay on disk. No rendering runs inside the input hook.

See [the consumer guide](../../docs/PANNING.MD),
[current native acceptance](../../docs/QUAL/PAN/README.MD) and
[current packet producer](../../tools/PAN/README.MD).

## Common experience, adapter-specific presentation

| Installed display | Internal owner | Behavior |
| --- | --- | --- |
| PCjr/ColorPlus 640x400, Tandy HPXY 640x256 | XYCTL | Two-axis framebuffer viewport; software-only on PCjr/ColorPlus, software/hardware selection on HPXY |
| CGA 320x200 desktop through 160x100 | PANCTL | Two-axis software viewport with aligned steps |
| Fixed CGA 160x100 | CGACTL | Window workspace with five-pixel steps |
| Supported fixed 160/320/640x200 | XTPAN | Two-axis window workspace |
| Legacy vertical framebuffer | XTPAN | Retained vertical viewport and memory constraints |

These executable names are internal compatibility details. Consumers run PAN
and PAN /SETTINGS; native installers place the needed files automatically.
Repeated launches route to the existing owner and retain its state and unfinished
settings edits. PAN OFF removes the active owner and disables next-session pan
startup; PAN enables it again. A required nonresident CGA color fix remains
available when its window workspace is OFF.

The PCjr/ColorPlus two-axis desktop uses two 64,000-byte bands, 128,000 bytes total,
64,000 more than the preceding vertical-only profile. It retains the physical
32KB page and guarded adapter launch. Hardware mode appears only when the
installed display supports reading its actual hardware/software state.

## Shared implementation

- PANSET.H/C defines the C89 settings model, capabilities, validation,
  persistence, Apply/Cancel/Home and singleton/command routing.
- PANDLG.H/C creates the adaptive dialog with ordinary Windows 3.0 controls;
  PANDLGC.C is a compatibility include of the same implementation.
- PANOWN.C detects capabilities and selects the owner; PANSTART.C maintains
  one public PAN startup token while preserving unrelated startup entries.
- PANKEY.C and PANKCL.C provide bounded queued-key delivery, one wake-up and
  timer recovery. The owner drains commands after busy drawing.

Persistence follows the selected backend's existing INI section. Apply validates,
applies and reads back before saving; Cancel discards unapplied edits. Software
and Hardware are alternative HPXY presentation modes, never simultaneous engines.
The mode remains session-only. Dialog-only follow behavior and general
follow-active behavior remain separate capabilities shown by the actual backend.

## Verification and packaging

HOSTUI.PY covers model, persistence, capability and actual Apply glue; KEYTEST.PY
covers queue ordering, wake recovery and hook lifetime; CLTEST.PY checks DLL
lookup, fallback and cleanup. Use the managed compiler route in AGENTS.md.

The current producer is tools/PAN/PUBLISH.PY. Its source/runtime pins, native
builds, actual installed files, native installer transactions, raster checks and
independent review are bound in tools/PAN/ACCEPT.JSN and docs/QUAL/PAN/FINAL.JSN.
Six distinct application backend families passed native installation, settings,
input and clean DOS exit. Each new PCjr/ColorPlus driver passed 704,000 native
pixel comparisons with zero errors. These are emulator results, not physical
hardware qualification. Older PANUI records retain their original historical
scope; they are not the current driver or package identities.
