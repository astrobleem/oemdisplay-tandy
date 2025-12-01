/* enable.c — Tandy 16-color Windows 3.0 driver: device bring-up
 *
 * Build model: 16-bit Windows (large memory model). 
 * External module tga_video.asm provides the real hardware work.
 */

#include "WINDOWS.H"
#include "STRING.H"
/* #include <gdidefs.h> */
#include "TGAVID.H"
#include "TNDY16.H"

/* ===== Global driver state ===== */
TNDY_STATE g_tndy;

/*
 * Stand-in for the DEVICE structure normally supplied by the
 * Windows 3.x DDK's <gdidefs.h>.  We only model the few fields used by
 * this sample so the code can be built with modern compilers.
 */
typedef struct DEVICE {
    WORD dpVersion;
    WORD dpHorzRes;
    WORD dpVertRes;
    WORD dpBitsPixel;
    WORD dpPlanes;
    WORD dpNumColors;
} DEVICE, FAR *LPDEVICE;

/* Forward decls of GDI-required exports (you’ll flesh out elsewhere) */
int  FAR PASCAL Enable(LPDEVICE lpDevice);      /* called by GDI */
void FAR PASCAL Disable(LPDEVICE lpDevice);
int  FAR PASCAL DeviceMode(LPSTR, LPSTR);   /* enumerate mode(s) for Display applet */
void FAR PASCAL ColorInfo(void);            /* fill color caps; stub for now */
int  FAR PASCAL RealizeObject(LPSTR, LPSTR, LPSTR); /* realize GDI objects */
BOOL FAR PASCAL BitBlt(
    HDC   hdcDest,
    int   xDest,
    int   yDest,
    int   width,
    int   height,
    HDC   hdcSrc,
    int   xSrc,
    int   ySrc,
    DWORD rop); /* bit block transfer */
int  FAR PASCAL Output(LPSTR, LPSTR, LPSTR, LPSTR, LPSTR, LPSTR); /* graphics output */

/* ===== Helpers ===== */
static void near set_defaults_for_mode(TGA_MODE m) {
    memset(&g_tndy, 0, sizeof(g_tndy));
    g_tndy.mode = m;

    if (m == TGA_MODE_320x200x16) {
        g_tndy.width  = TNDY_W_320;
        g_tndy.height = TNDY_H_200;
        g_tndy.bpp    = 4;
        g_tndy.planes = 4;
        g_tndy.shadowStride = TNDY_SHADOW_STRIDE_320;
    } else { /* TGA_MODE_640x200x4 (future) */
        g_tndy.width  = 640;
        g_tndy.height = 200;
        g_tndy.bpp    = 2;   /* hardware depth; our shadow remains 4bpp packed */
        g_tndy.planes = 2;
        g_tndy.shadowStride = 640/2; /* still 320 bytes if we keep 4bpp packed; see note below */
    }
}

/* Allocate shadow as packed-4bpp (2 pixels/byte) regardless of the HW mode.
   This keeps blitters identical between 16-color and 4-color paths; in 2bpp we just mask to 0..3. */
static int near alloc_shadow(void) {
    DWORD sz = (DWORD)g_tndy.shadowStride * (DWORD)g_tndy.height;
    g_tndy.shadow = (uint8_t FAR*)GlobalLock(GlobalAlloc(GHND, (DWORD)sz));
    return (g_tndy.shadow != NULL);
}

static void near free_shadow(void) {
    if (g_tndy.shadow) {
        HGLOBAL h = GlobalHandle((LPCVOID)g_tndy.shadow);
        GlobalUnlock(h);
        GlobalFree(h);
        g_tndy.shadow = NULL;
    }
}

/* ===== Driver exports expected by Win 3.0 GDI ===== */

int FAR PASCAL Enable(LPDEVICE lpDevice)

{
    /* 1) Detect hardware early; bail out cleanly if not present */
    if (!TGA_Detect()) {
        /* Let GDI fall back to VGA/CGA if present */
        return 0;
    }

    /* 2) Choose mode (default 320x200x16); allow override from WIN.INI [TNDY16] */
    {
        int iniMode = GetProfileInt("TNDY16", "Mode", 0); /* 0=320x200x16, 1=640x200x4 */
        TGA_MODE m = (iniMode == 1) ? TGA_MODE_640x200x4 : TGA_MODE_320x200x16;
        set_defaults_for_mode(m);
    }

    /* 3) Set graphics mode via HW layer */
    if (!TGA_SetMode(g_tndy.mode)) {
        return 0; /* fail -> GDI chooses another driver */
    }

    /* 4) Query plane geometry (segment, per-plane offsets, stride) */
    TGA_GetPlaneInfo(&g_tndy.planesInfo);

    /* 5) Allocate shadow (packed-4bpp) */
    if (!alloc_shadow()) {
        TGA_SetTextMode();
        return 0;
    }

    /* 6) Clear shadow & screen (simple paint) */
    _fmemset(g_tndy.shadow, 0, (size_t)g_tndy.shadowStride * g_tndy.height);
    /* You’ll call your “flush shadow to VRAM” here once that module exists */

    /* 7) Fill out minimal device fields (size, resolution, planes, colors).
       Structure layout varies by DDK; copy these into your sample’s DEVICES/DEVCAPS. */
    if (lpDevice) {
        lpDevice->dpVersion   = 0x0300;            /* Windows 3.0 */
        lpDevice->dpHorzRes   = g_tndy.width;
        lpDevice->dpVertRes   = g_tndy.height;
        lpDevice->dpBitsPixel = 4;                 /* logical packed view */
        lpDevice->dpPlanes    = 1;                 /* GDI sees a single packed plane */
        lpDevice->dpNumColors = (g_tndy.bpp==4)?16:4;
        /* plus any other fields your sample struct expects */
    }

    return 1; /* success */
}

void FAR PASCAL Disable(LPDEVICE lpDevice)
{
    /* Free resources and restore text mode */
    (void)lpDevice;
    free_shadow();
    TGA_SetTextMode();
}

/* Optional: used by Control Panel “Display” to list modes */
int FAR PASCAL DeviceMode(LPSTR lpDevName, LPSTR lpOut)
{
    /* Minimal stub: we export two strings (future-proof):
       "320x200 16-color (Tandy)" and "640x200 4-color (Tandy)".
       Actual INF/OEMSETUP wiring decides selection; keep this simple now. */
    (void)lpDevName; (void)lpOut;
    return 0; /* not implemented (OK for initial bring-up) */
}

void FAR PASCAL ColorInfo(void)
{
    /* Fill GDI color mapping if your DDK sample asks for it; otherwise leave as-is.
       We’ll implement proper RealizePalette elsewhere. */
}
int FAR PASCAL RealizeObject(LPSTR lpDevObj, LPSTR lpPhysObj, LPSTR lpBrush)
{
    /* Stub implementation for object realization (brushes, pens, etc.) */
    (void)lpDevObj; (void)lpPhysObj; (void)lpBrush;
    return 0; /* fail - not implemented yet */
}

BOOL FAR PASCAL BitBlt(HDC hdcDest, int xDest, int yDest, int width, int height,
                       HDC hdcSrc, int xSrc, int ySrc, DWORD rop)
{
    /* Stub implementation for bit block transfer operations */
    (void)hdcDest; (void)xDest; (void)yDest; (void)width; (void)height;
    (void)hdcSrc; (void)xSrc; (void)ySrc; (void)rop;
    return FALSE; /* fail - not implemented yet */
}

int FAR PASCAL Output(LPSTR lpDstDev, LPSTR lpStyle, LPSTR lpCount, LPSTR lpPoints, LPSTR lpPhysPen, LPSTR lpDrawMode)
{
    /* Stub implementation for graphics output (lines, polygons, etc.) */
    (void)lpDstDev; (void)lpStyle; (void)lpCount; (void)lpPoints; (void)lpPhysPen; (void)lpDrawMode;
    return 0; /* fail - not implemented yet */
}
