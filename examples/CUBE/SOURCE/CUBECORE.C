#include "CUBECORE.H"
/* A quarter-wave Q8 table: only 130 bytes, all eight vertices reuse four
   products per frame. Orthographic projection needs no per-vertex division. */
static const int sine[65] = {
 0,6,13,19,25,31,38,44,50,56,62,68,74,80,86,92,
 98,104,109,115,121,126,132,137,142,147,152,157,162,167,172,177,
 181,185,190,194,198,202,206,209,213,216,220,223,226,229,231,234,
 237,239,241,243,245,247,248,250,251,252,253,254,255,255,256,256,256
};
/* Vertex bits are the x/y/z signs. Face winding is outward. */
const unsigned char CubeFaces[6][4] = {
 {0,4,6,2}, {1,3,7,5}, {0,1,5,4},
 {2,6,7,3}, {0,2,3,1}, {4,5,7,6}
};
const unsigned char CubeEdges[12][2] = {
 {0,1},{2,3},{4,5},{6,7},{0,2},{1,3},
 {4,6},{5,7},{0,4},{1,5},{2,6},{3,7}
};
int CubeSin(unsigned a)
{
 int n, sign;
 a &= 255U; sign = a >= 128U ? -1 : 1; n = a & 127U;
 if (n > 64) n = 128 - n;
 return sign * sine[n];
}
static int mul(int a, int b) { return (int)(((long)a * b) / 256L); }
void CubeFrame(unsigned phase, int cx, int cy, int sx, int sy, CFRAME *f)
{
 int ax, az, by, bz, zx, zy, zz, n, x, y, nx, ny, nz, light;
 ax = CubeSin(phase + 64U); zx = CubeSin(phase);
 by = CubeSin((phase >> 1) + 85U); bz = CubeSin((phase >> 1) + 21U);
 az = -mul(by, zx); zy = -mul(bz, ax); zz = mul(by, ax);
 /* x basis=(ax, bz*zx, az), y basis=(0,by,bz), z=(zx,zy,zz). */
 n = mul(bz, zx);
 for (x = 0; x < 8; ++x) {
  y = (x & 1 ? n : -n) + (x & 2 ? by : -by) + (x & 4 ? zy : -zy);
  f->point[x].y = cy + (int)((long)y * sy / 768L);
  y = (x & 1 ? ax : -ax) + (x & 4 ? zx : -zx);
  f->point[x].x = cx + (int)((long)y * sx / 768L);
 }
 for (x = 0; x < 6; ++x) {
  if (x < 2) { nx = ax; ny = n; nz = az; }
  else if (x < 4) { nx = 0; ny = by; nz = bz; }
  else { nx = zx; ny = zy; nz = zz; }
  if (!(x & 1)) { nx = -nx; ny = -ny; nz = -nz; }
  f->visible[x] = nz < -2;
  /* White light above/left and in front. Ambient keeps every face legible. */
  light = (int)((-80L * nx - 128L * ny - 208L * nz) / 256L);
  if (light < 0) light = 0;
  light = 3 + light / 20;
  f->shade[x] = light > 16 ? 16 : light;
 }
}
