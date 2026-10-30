/* Meaningful host checks for visibility, bounds and fixed-point periodicity.
   No Windows/emulator/hardware qualification is implied. */
#include <stdio.h>
#include <stdlib.h>
#include "CUBECORE.H"
#define CHECK(c) do {if(!(c)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
/* Frozen pre-optimization algorithm from 832daf29, CUBECORE.C SHA-256
   e73cc486cdf1bb33d26da5b8ec69a7b7c6062a981d96602751018f6505864986.
   Separate arithmetic/order preserves a discriminating rounding oracle. */
static int mul(int a, int b) { return (int)(((long)a * b) / 256L); }
void ReferenceFrame(unsigned phase, int cx, int cy, int sx, int sy, CFRAME *f)
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

static int equalFrame(unsigned phase, int cx, int cy, int sx, int sy)
{
 CFRAME f,g; int i;
 CubeFrame(phase,cx,cy,sx,sy,&f);
 ReferenceFrame(phase,cx,cy,sx,sy,&g);
 for(i=0;i<8;++i)if(f.point[i].x!=g.point[i].x ||
                         f.point[i].y!=g.point[i].y)return 0;
 for(i=0;i<6;++i)if(f.visible[i]!=g.visible[i] ||
                         f.shade[i]!=g.shade[i])return 0;
 return 1;
}
int main(void)
{
 CFRAME f,g;unsigned p;int i,j,count,sx,sy,phaseCount=0;
 CHECK(CubeSin(0)==0&&CubeSin(64)==256&&CubeSin(128)==0&&CubeSin(192)==-256);
 for(p=0;p<256;p++)CHECK(CubeSin(p)==-CubeSin(p+128));
 for(p=0;p<512;p++){
  CubeFrame(p,112,64,168,96,&f);CubeFrame(p+512,112,64,168,96,&g);count=0;
  for(i=0;i<8;i++){
   CHECK(f.point[i].x>=0&&f.point[i].x<224&&f.point[i].y>=0&&f.point[i].y<128);
   CHECK(f.point[i].x==g.point[i].x&&f.point[i].y==g.point[i].y);
  }
  for(i=0;i<6;i++){
   CHECK(f.shade[i]>=3&&f.shade[i]<=16);count+=f.visible[i];
   CHECK(f.visible[i]==g.visible[i]&&f.shade[i]==g.shade[i]);
   if(f.visible[i]){
    long area=0;
    for(j=0;j<4;j++){
     CPOINT a=f.point[CubeFaces[i][j]],b=f.point[CubeFaces[i][(j+1)%4]];
     area+=(long)a.x*b.y-(long)a.y*b.x;
    }
    CHECK(area<=0); /* Every visible polygon keeps the outward winding. */
   }
  }
  CHECK(count>=1&&count<=3);phaseCount++;
 }
 /* The reduced copy rectangle must contain every rotated vertex. */
 for(sx=24;sx<=168;sx+=12)for(sy=24;sy<=96;sy+=12)for(p=0;p<512;p++){
  int width=sx+4,height=sy*6/5+4;
  CubeFrame(p,width/2,height/2,sx,sy,&f);
  for(i=0;i<8;i++)CHECK(f.point[i].x>0&&f.point[i].x<width-1&&f.point[i].y>0&&f.point[i].y<height-1);
 }
 /* Smallest 160x100 canvas as well as higher modes use the same bounded core. */
 for(p=0;p<512;p++){
  CubeFrame(p,76,46,100,60,&f);
  for(i=0;i<8;i++)CHECK(f.point[i].x>=0&&f.point[i].x<152&&f.point[i].y>=0&&f.point[i].y<92);
 }
 /* Scales are independent: exhaust every integer value on each axis.
    Include tiny/zero scales and near-16-bit-limit positive/negative centers.
    No cache state may survive a scale/center/phase change (resize/restart).
    All original signed intermediates fit 16-bit int / 32-bit long here. */
 for(p=0;p<512;p++){
  for(sx=0;sx<=168;sx++)CHECK(equalFrame(p,-32000,32000,sx,96));
  for(sy=0;sy<=96;sy++)CHECK(equalFrame(p,32000,-32000,168,sy));
 }
 /* Exercise every 16-bit phase, including the native unsigned wrap. */
 for(p=0;p<65535U;p++)CHECK(equalFrame(p,112,64,168,96));
 CHECK(equalFrame(65535U,112,64,168,96));
 CHECK(equalFrame(0,2,2,2,2));
 printf("PASS exact reference equivalence: 136192 scale/phase + 65536 unsigned-phase cases\n");
 printf("PASS %d phases; winding, lighting, periodicity, low/high canvas bounds\n",phaseCount);
 return 0;
}
