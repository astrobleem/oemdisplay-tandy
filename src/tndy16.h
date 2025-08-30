/* tndy16.h — driver-local defs for our 4bpp path */
#ifndef TNDY16_H
#define TNDY16_H

#include <stdint.h>

#define TNDY_W_320   320
#define TNDY_H_200   200

/* Packed-4bpp shadow stride for 320 wide */
#define TNDY_SHADOW_STRIDE_320  (TNDY_W_320/2)   /* 160 bytes/row */

/* Logical palette size */
#define TNDY_NUM_COLORS   16

/* Global driver state */
typedef struct TNDY_STATE {
    TGA_MODE   mode;              /* current graphics mode */
    uint16_t   width, height;
    uint8_t    bpp;               /* logical bits per pixel: 4 or 2 */
    uint8_t    planes;            /* active planes: 4 (16c) or 2 (4c) */

    /* shadow framebuffer (packed) — always 4bpp packed layout for simplicity.
       For 2bpp mode we still write 4bpp values but map to low 2 bits. */
    uint8_t FAR *shadow;
    uint16_t     shadowStride;    /* bytes per row in shadow */

    /* VRAM plane geometry for current mode */
    TGAPlaneInfo planesInfo;
} TNDY_STATE;

extern TNDY_STATE g_tndy;

#endif
