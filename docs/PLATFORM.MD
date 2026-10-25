# Choose your display driver

Use [current downloads](DOWNLOADS.MD) for one current packet per hardware or
display profile. These drivers target Windows 3.0 real mode.

| Hardware or profile | Driver and install guide | Required distinction |
| --- | --- | --- |
| Tandy 1000 EX/HX, panning desktop | [XRSYNC](RELEASES/XRSYNC.MD) | 640 KB; RUNSYNC reserves video memory before Windows. |
| Tandy EX/HX, fixed-resolution desktop | [Fixed profiles](FIXED.MD) | Use the packet's guarded WINXT launcher in every mode. |
| Tandy 1000 SL/2 Video II | [Video II](tga2/INSTALL.TXT) | Not EX/HX. T2RESV must succeed before Setup and every launch. |
| IBM PCjr | [PCjr Setup](../downloads/experimental/PCJR/README.MD) | Its 32 KB page must already be reserved; JRGUARD checks it, JRWIN checks every launch. |
| Amstrad PC1512 | [PC1512](../experiments/DISPLAY3/PC1512.TXT) | Built-in PC1512 video, not PC1640. |
| Plantronics ColorPlus | [ColorPlus](../experiments/DISPLAY3/PCP3216.TXT) | Dedicated ColorPlus card memory; ordinary CGA is different. |
| Olivetti PC1 / Yamaha B000h | [PC1](../experiments/YAMAHA/README.MD) | PC1YAMA.DRV; not the standalone B800h profile. |
| Standalone Yamaha B800h | [Yamaha](../experiments/YAMAHA/README.MD) | YAM160.DRV; not the PC1 B000h profile. |
| CGA-compatible color text | [TEXT80 / C25](../downloads/experimental/TEXT80/README.MD) | Existing Windows installation; VGA 80x50 requires VGA. |

CGA-compatible adapters, including Graphics Gremlin's CGA output, can also
use Windows 3.0's stock CGA driver. A VGA connector does not add VGA modes.

## Limits

PC1512's cursor-state case remains unresolved. Physical ColorPlus clones and
related Video II models are unqualified. PC1/B000h and standalone Yamaha/B800h have native Setup and software/API
startup checks. Those checks do not qualify physical PC1 output; the older
B800 scanout evidence remains separate. At 160 pixels, dialogs
can clip. TEXT80 graphics are block approximations and scrolling is slow.

The install guides retain the model-specific prerequisites. [Screenshots
and recorded test scope](SHOWCASE.MD) are available separately.
