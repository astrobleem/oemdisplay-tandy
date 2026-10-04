#define MAZE_HOST
#include "MAZE.C"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
static int reference(int a,int off,int height){
 double dx=sine[(a+64)&255]/256.0,dy=sine[a]/256.0,best=1e20;
 int x,y;for(y=0;y<12;y++)for(x=0;x<12;x++)if(world[y][x]!='.'){
 double lo=0,hi=1e20,t1,t2,t;
 if(dx==0){if(px<x*256||px>(x+1)*256)continue;}else{t1=(x*256-px)/dx;t2=((x+1)*256-px)/dx;if(t1>t2){t=t1;t1=t2;t2=t;}if(t1>lo)lo=t1;if(t2<hi)hi=t2;}
 if(dy==0){if(py<y*256||py>(y+1)*256)continue;}else{t1=(y*256-py)/dy;t2=((y+1)*256-py)/dy;if(t1>t2){t=t1;t1=t2;t2=t;}if(t1>lo)lo=t1;if(t2<hi)hi=t2;}
 if(hi>=lo-0.0001&&lo<best)best=lo;
 }
 best=best*sine[(off+320)&255]/256.0;if(best<32)best=32;
 x=(int)(height*160.0/best);if(x>height)x=height;if(x<1)x=1;return x;
}
int main(void){int x,y,a,i,off,delta,maxdelta=0;long rays=0;for(y=0;y<12;y++)for(x=0;x<12;x++)if(world[y][x]=='.')for(a=0;a<256;a++){
 px=x*256+128;py=y*256+128;angle=a;cast(168);
 for(i=0;i<32;i++){off=i*46/31-23;delta=abs((int)walls[i]-reference((angle+off+256)&255,off,168));if(delta>maxdelta)maxdelta=delta;if(delta>2||walls[i]>168||shades[i]>3){printf("FAIL x%d y%d a%d ray%d d%d\n",x,y,a,i,delta);return 1;}rays++;}
 }
 px=384;py=384;angle=leg=turning=0;for(i=0;i<30000;i++){advance();if(!walkable(px,py)||angle<0||angle>255){puts("FAIL movement");return 1;}}
 cast(-1);for(i=0;i<32;i++)if(walls[i])return 1;cast(32767);for(i=0;i<32;i++)if(walls[i]>4096)return 1;
 printf("PASS rays=%ld max_height_error=%d movement_steps=30000 bounds=PASS\n",rays,maxdelta);return 0;}

