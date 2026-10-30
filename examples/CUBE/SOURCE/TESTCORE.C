/* Meaningful host checks for visibility, bounds and fixed-point periodicity.
   No Windows/emulator/hardware qualification is implied. */
#include <stdio.h>
#include <stdlib.h>
#include "CUBECORE.H"
#define CHECK(c) do {if(!(c)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
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
 printf("PASS %d phases; winding, lighting, periodicity, low/high canvas bounds\n",phaseCount);
 return 0;
}
