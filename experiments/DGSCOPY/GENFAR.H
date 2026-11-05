#ifndef GENFAR_H
#define GENFAR_H
#include "GENSPAN.H"
typedef struct {int width,height,a,b,transposed,y,outerK,innerK;} GenWalk;
typedef struct {int top,mirror,left,right,innerLeft,innerRight;} GenPair;
/* Internal API: disjoint validated work[320], walk, pair/output objects. */
int _far _pascal GenFarPrepare(int width,int height,int _far *work,GenWalk _far *walk);
/* 1=row pair ready, 0=done, -1=bad private state (not a GDI fallback request). */
int _far _pascal GenFarNext(GenWalk _far *walk,int _far *work,GenPair _far *pair);
int _far _pascal GenFarMake(int width,int height,int _far *work,GenSpan _far *out);
#endif
