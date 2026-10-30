#include <assert.h>
#include <stdio.h>
#include "CUBECORE.H"
#include "CUBERECT.H"
static unsigned long cases;
static void check(unsigned phase,int sx,int sy)
{
 CFRAME a,b;CBOX old,current,dirty,unused;int w=sx+4,h=sy*6/5+4,n;
 CubeFrame((phase+133U)&511U,w/2,h/2,sx,sy,&a);
 CubeFrame(phase,w/2,h/2,sx,sy,&b);
 CubeDirtyBounds(&a,w,h,&unused,0,&old,&dirty);
 CubeDirtyBounds(&b,w,h,&old,1,&current,&dirty);
 assert(dirty.left>=0&&dirty.top>=0&&dirty.right<=w&&dirty.bottom<=h);
 assert(dirty.left<dirty.right&&dirty.top<dirty.bottom);
 /* Opposite rectangle corners establish coverage of every old/new cell. */
 assert(old.left>=dirty.left&&old.top>=dirty.top);
 assert(old.right<=dirty.right&&old.bottom<=dirty.bottom);
 assert(current.left>=dirty.left&&current.top>=dirty.top);
 assert(current.right<=dirty.right&&current.bottom<=dirty.bottom);
 for(n=0;n<8;n++){
  assert(b.point[n].x>=current.left&&b.point[n].x<current.right);
  assert(b.point[n].y>=current.top&&b.point[n].y<current.bottom);
 }
 cases++;
}
int main(void)
{
 unsigned phase;int scale;
 for(phase=0;phase<512;phase++){
  for(scale=0;scale<=168;scale++)check(phase,scale,96);
  for(scale=0;scale<=96;scale++)check(phase,168,scale);
 }
 printf("PASS %lu bounds cases: vertex coverage, old/new erase/copy coverage, clipped transfer and arbitrary phase jumps\n",cases);
 return 0;
}
