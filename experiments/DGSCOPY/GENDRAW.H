#ifndef GENDRAW_H
#define GENDRAW_H
#include "GENFAR.H"
typedef struct {
 unsigned char _far *shadow;
 int deviceWidth,deviceHeight,colors,target,enabled;
 int x,y,width,height,logicalWidth,penStyle,penIndex,brushStyle,brushIndex,rop;
 int clipLeft,clipTop,clipRight,clipBottom,complexClip;
} GenDraw;
/* INTERNAL ONLY. Caller binds a genuine 320x200 four-plane shadow and owns
 * validated writable disjoint storage, excluding active stack/code regions.
 * -1=unsupported BEFORE shadow writes; 0=post-preflight fatal; 1=complete.
 * No VRAM presentation is performed. Do not expose raw shadow pointers to apps.
 */
int _far _pascal GenDrawKernel(const GenDraw _far *ctx,int _far *work,GenWalk _far *walk,GenPair _far *pair);
#endif
