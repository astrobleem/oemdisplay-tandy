/* Pure C89 command folding; engines decide limits, step and alignment. */
#ifndef PANTGT_H
#define PANTGT_H
#include "PANCMD.H"
typedef struct {
 int x,y,maxX,maxY,stepX,stepY,alignX,alignY,moved,home;
} PANTARGET;
void PanTargetInit(PANTARGET *,int,int,int,int,int,int,int,int);
int PanTargetCommand(PANTARGET *,int,int,int);
#endif
