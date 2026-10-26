# Choose your display driver

Use [current downloads](DOWNLOADS.MD) for one current packet per hardware or
display profile. These drivers target Windows 3.0 real mode.

[Panning settings](PANNING.MD) describes each display's available viewport or
window workspace and its Home recovery control.

| Hardware or profile | Driver and install guide | Required distinction |
| --- | --- | --- |
| Tandy 1000 EX/HX, panning desktop | [Windows XT](DRIVERS.MD) | 640 KB; DISPLAY and DISPWIN reserve video memory automatically. |
| Tandy EX/HX, fixed-resolution desktop | [Fixed profiles](FIXED.MD) | Use the packet's guarded WINXT launcher in every mode. |
| Tandy 1000 SL/2 Video II | [Video II](tga2/INSTALL.TXT) | Not EX/HX. INSTALL and T2WIN reserve video memory automatically. |
| IBM PCjr | [PCjr software panning](SOFTPAN/RELEASE.MD) | 320x400 desktop through a 320x200 view; fixed 320x200 choice included. Its 32 KB page must already be reserved; JRGUARD checks Setup and every JRSTART launch. |
| Amstrad PC1512 | [PC1512](PC1512.MD) | Built-in PC1512 video, not PC1640. |
| Plantronics ColorPlus | [ColorPlus software panning](SOFTPAN/RELEASE.MD) | 320x400 desktop through a 320x200 view; fixed 320x200 choice included. Dedicated ColorPlus card memory; ordinary CGA is different. |
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
