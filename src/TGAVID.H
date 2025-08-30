/* tga_video.h — minimal HW layer (C/ASM boundary) */
#ifndef TGA_VIDEO_H
#define TGA_VIDEO_H

#include <windows.h>
#include "compiler_compat.h"
#include "stdint.h"
#include "stdbool.h"

/* Logical modes we’ll support */
typedef enum {
    TGA_MODE_320x200x16 = 0,   /* primary target */
    TGA_MODE_640x200x4  = 1    /* planned next */
} TGA_MODE;

/* Plane layout for the active mode */
typedef struct TGAPlaneInfo {
    /* VRAM segment for all planes (typically 0xB800) */
    uint16_t vramSeg;

    /* For each plane, byte offset to start of scanline 0 */
    uint16_t planeOfs[4];   /* plane 0..3; for 4-color modes planes[2..3] may be unused */

    /* Bytes per scanline per plane (e.g., 40 for 320-wide, 80 for 640-wide) */
    uint16_t planeStride;

    /* Number of active planes for current mode: 4 for 16-color, 2 for 4-color */
    uint8_t  activePlanes;
} TGAPlaneInfo;

/* Returns nonzero if the machine looks like Tandy/PCjr-class graphics */
int  FAR PASCAL TGA_Detect(void);

/* Set graphics mode; returns nonzero on success */
int  FAR PASCAL TGA_SetMode(TGA_MODE mode);

/* Restore text mode (80×25) */
void FAR PASCAL TGA_SetTextMode(void);

/* Fill out plane layout for the currently-set mode */
void FAR PASCAL TGA_GetPlaneInfo(TGAPlaneInfo FAR *out);

#endif
