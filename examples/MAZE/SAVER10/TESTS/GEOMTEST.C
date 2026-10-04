#define MAXCOL 80
#define ROWS 25
#define MAXCELL (MAXCOL*ROWS)
static int columns,stripe;
static unsigned long ticks,changed;
#define RAYS 80
#define MAPSIZE 12
static const char world[MAPSIZE][MAPSIZE+1]={
 "############",
 "#..........#",
 "#.##.###.#.#",
 "#.#......#.#",
 "#.#.####.#.#",
 "#...#..#...#",
 "#.#.#..#.#.#",
 "#.#.####.#.#",
 "#.#......#.#",
 "#.###.##.#.#",
 "#..........#",
 "############"};
static const int sine[256]={0,6,13,19,25,31,38,44,50,56,62,68,74,80,86,92,98,104,109,115,121,126,132,137,142,147,152,157,162,167,172,177,181,185,190,194,198,202,206,209,213,216,220,223,226,229,231,234,237,239,241,243,245,247,248,250,251,252,253,254,255,255,256,256,256,256,256,255,255,254,253,252,251,250,248,247,245,243,241,239,237,234,231,229,226,223,220,216,213,209,206,202,198,194,190,185,181,177,172,167,162,157,152,147,142,137,132,126,121,115,109,104,98,92,86,80,74,68,62,56,50,44,38,31,25,19,13,6,0,-6,-13,-19,-25,-31,-38,-44,-50,-56,-62,-68,-74,-80,-86,-92,-98,-104,-109,-115,-121,-126,-132,-137,-142,-147,-152,-157,-162,-167,-172,-177,-181,-185,-190,-194,-198,-202,-206,-209,-213,-216,-220,-223,-226,-229,-231,-234,-237,-239,-241,-243,-245,-247,-248,-250,-251,-252,-253,-254,-255,-255,-256,-256,-256,-256,-256,-255,-255,-254,-253,-252,-251,-250,-248,-247,-245,-243,-241,-239,-237,-234,-231,-229,-226,-223,-220,-216,-213,-209,-206,-202,-198,-194,-190,-185,-181,-177,-172,-167,-162,-157,-152,-147,-142,-137,-132,-126,-121,-115,-109,-104,-98,-92,-86,-80,-74,-68,-62,-56,-50,-44,-38,-31,-25,-19,-13,-6};
static int px=384,py=384,angle=0,leg=0,turning=0;
static unsigned walls[RAYS];
static unsigned char shades[RAYS];
static unsigned long frames,paints;
static int solid(int x,int y){return x<0||y<0||x>=MAPSIZE*256||y>=MAPSIZE*256||world[y>>8][x>>8]!='.';}
static int walkable(int x,int y){return !solid(x-48,y-48)&&!solid(x+48,y-48)&&!solid(x-48,y+48)&&!solid(x+48,y+48);}
static void advance(void){
 static const int tx[4]={2688,2688,384,384},ty[4]={384,2688,2688,384};
 int nx,ny;
 if(turning){angle=(angle+4)&255;if(angle==((leg*64)&255))turning=0;return;}
 nx=px+sine[(angle+64)&255]*24/256;ny=py+sine[angle]*24/256;
 if((angle==0&&nx>=tx[leg])||(angle==64&&ny>=ty[leg])||(angle==128&&nx<=tx[leg])||(angle==192&&ny<=ty[leg])){
  px=tx[leg];py=ty[leg];leg=(leg+1)&3;turning=1;return;
 }
 if(walkable(nx,ny)){px=nx;py=ny;}else{leg=(leg+1)&3;turning=1;}
}
static void castOne(int i,int rays,int height){
 int a,dx,dy,sx,sy,mx,my,n,side,off,h;
 unsigned long xx,yy,dist,perp;
 unsigned ax,ay,ex,ey;
 if(height<0)height=0;if(height>4096)height=4096;
 {
  off=(i*46/(rays-1))-23;a=(angle+off+256)&255;
  dx=sine[(a+64)&255];dy=sine[a];ax=dx<0?-dx:dx;ay=dy<0?-dy:dy;
  mx=px>>8;my=py>>8;sx=dx<0?-1:1;sy=dy<0?-1:1;
  ex=dx<0?(px&255):256-(px&255);ey=dy<0?(py&255):256-(py&255);
  xx=dx==0?0x3fffffffUL:(unsigned long)ex*ay;
  yy=dy==0?0x3fffffffUL:(unsigned long)ey*ax;
  dist=256;side=0;
  for(n=0;n<24;n++){
   if(xx<yy||(xx==yy&&(mx+sx<0||mx+sx>=MAPSIZE||world[my][mx+sx]!='.'))){dist=ex;ex+=256;xx+=(unsigned long)ay*256UL;mx+=sx;side=0;}else{dist=ey;ey+=256;yy+=(unsigned long)ax*256UL;my+=sy;side=1;}
   if(mx<0||my<0||mx>=MAPSIZE||my>=MAPSIZE||world[my][mx]!='.')break;
  }
  perp=dist*(unsigned)sine[(off+320)&255]/(side?ay:ax);
  if(perp<32)perp=32;
  h=(int)((unsigned long)height*160UL/perp);if(h>height)h=height;if(h<1&&height)h=1;
  walls[i]=(unsigned)h;shades[i]=(unsigned char)(side+(perp>768?2:0));
 }
}

static void resetRain(int cols){columns=cols;stripe=0;px=py=384;angle=leg=turning=0;ticks=changed=frames=paints=0;}
static void stepRain(void){ticks++;}
static unsigned rowOffset(int y,int banks){return (unsigned)((y&(banks-1))*8192U+(y/banks)*(banks==4?160:80));}
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
int main(void){int raysize,x,y,a,i,off,delta,maxdelta=0;long rays=0;for(raysize=20;raysize<=80;raysize*=2)for(y=0;y<12;y++)for(x=0;x<12;x++)if(world[y][x]=='.')for(a=0;a<256;a++){
 px=x*256+128;py=y*256+128;angle=a;for(i=0;i<raysize;i++)castOne(i,raysize,168);
 for(i=0;i<raysize;i++){off=i*46/(raysize-1)-23;delta=abs((int)walls[i]-reference((angle+off+256)&255,off,168));if(delta>maxdelta)maxdelta=delta;if(delta>2||walls[i]>168||shades[i]>3){printf("FAIL x%d y%d a%d ray%d d%d\n",x,y,a,i,delta);return 1;}rays++;}
 }
 px=384;py=384;angle=leg=turning=0;for(i=0;i<30000;i++){advance();if(!walkable(px,py)||angle<0||angle>255){puts("FAIL movement");return 1;}}
 for(i=0;i<80;i++)castOne(i,80,-1);for(i=0;i<32;i++)if(walls[i])return 1;for(i=0;i<80;i++)castOne(i,80,32767);for(i=0;i<32;i++)if(walls[i]>4096)return 1;
 printf("PASS rays=%ld max_height_error=%d movement_steps=30000 bounds=PASS\n",rays,maxdelta);return 0;}

