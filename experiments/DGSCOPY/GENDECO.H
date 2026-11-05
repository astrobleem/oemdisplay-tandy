#ifndef GENDECO_H
#define GENDECO_H
#include "GENTRY.H"
typedef struct {
 int style,count;
 const unsigned char _far *device;
 const unsigned char _far *points;
 const unsigned char _far *pen;
 const unsigned char _far *brush;
 const unsigned char _far *mode;
 const unsigned char _far *clip;
} GenObjects;
/* INTERNAL decoder only: source ownership/frame/code/shadow exclusion belongs
 * to the driver wrapper. Tagged pen ABI must be qualified before any admission.
 * Return1 writes30 native request bytes; -1 leaves output unchanged. No drawing.
 */
int _far _pascal GenDecode(const GenObjects _far *input,GenRequest _far *output);
#endif
