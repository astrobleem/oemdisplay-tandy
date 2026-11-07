/* First-party cube geometry. C89, 16-bit int / 32-bit long, no floating point. */
#ifndef CUBECORE_H
#define CUBECORE_H
typedef struct { int x, y; } CPOINT;
typedef struct { CPOINT point[8]; int visible[6], shade[6]; } CFRAME;
extern const unsigned char CubeFaces[6][4];
extern const unsigned char CubeEdges[12][2];
int CubeSin(unsigned angle);
void CubeFrame(unsigned phase, int cx, int cy, int sx, int sy, CFRAME *frame);
#endif
