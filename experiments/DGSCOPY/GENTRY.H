#ifndef GENTRY_H
#define GENTRY_H
/* PRIVATE request layout; shadow/target/enabled/workspace are driver-owned. */
typedef struct {
 int x,y,width,height,logicalWidth,penStyle,penIndex,brushStyle,brushIndex,rop;
 int clipLeft,clipTop,clipRight,clipBottom,complexClip;
} GenRequest;
#endif
