"""Host geometry and incremental XOR/state test. GDI is stubbed, not raster proof."""
from pathlib import Path
import argparse,json,subprocess,tempfile
HERE=Path(__file__).resolve().parent
def check():
 source=(HERE/'ORBITS.C').read_text();setup=source[source.index('#define MAXSTARS'):source.index('static unsigned rowOffset')];render=source[source.index('static int rotatedOval('):source.index('/* Destroying the GDI popup')]
 header=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define _far
#define FAR
#include "OVALFX.H"
typedef struct {int x,y;} POINT;
typedef int HPEN;typedef int HBRUSH;typedef unsigned long DWORD;
#define NULL_BRUSH 99
#define R2_XORPEN 7
#define BLACKNESS 0
static int screenW,screenH,running=1,screenDC=1,blankCursor,saver;
static int stopped,failDraw,failClear,failSelect,failRop;
static DWORD drawMs,maxDraw,totalCells,clockValue;
static int selected=44,brush=45,rop2=13,drawCalls;
static unsigned char actual[4096],want[4096];
static int ownsScreen(void){return 1;}
static void SetCursor(int c){}
static DWORD GetTickCount(void){return clockValue++;}
static int GetStockObject(int o){return o;}
static int SelectObject(int dc,int object){int old;
 if(failSelect&&!--failSelect)return 0;
 if(object==NULL_BRUSH||object==45){old=brush;brush=object;}
 else{old=selected;selected=object;}return old;}
static int SetROP2(int dc,int v){int old=rop2;if(failRop){failRop=0;return 0;}rop2=v;return old;}
static void stop(int w,char *reason){running=0;stopped++;}
static int PatBlt(int dc,int x,int y,int w,int h,int op){if(failClear){failClear=0;return 0;}assert(x==0&&w==screenW&&y>=0&&h>0&&h<=16&&y+h<=screenH);if(!y)memset(actual,0,sizeof(actual));return 1;}
/* Hash geometry into a sparse XOR footprint, avoiding any raster equivalence claim. */
static unsigned mix(unsigned a,unsigned b){return (a*33U+b)&4095U;}
static void mark(unsigned char *out,unsigned key,int color){int i;for(i=0;i<7;i++){key=mix(key,173U+i);out[key]^=(unsigned char)color;}}
static unsigned ellipseKey(int l,int t,int r,int b){return mix(mix(mix((unsigned)l,t),r),b);}
static unsigned polyKey(POINT *p,int count){int n;unsigned key=7;for(n=0;n<count;n++)key=mix(mix(key,p[n].x),p[n].y);return key;}
static int Ellipse(int dc,int l,int t,int r,int b){if(failDraw&&!--failDraw)return 0;assert(brush==NULL_BRUSH&&rop2==R2_XORPEN&&l<r&&t<b);mark(actual,ellipseKey(l,t,r,b),selected);drawCalls++;return 1;}
static int Polyline(int dc,POINT *p,int count){if(failDraw&&!--failDraw)return 0;assert(brush==NULL_BRUSH&&rop2==R2_XORPEN&&count==33&&p[0].x==p[32].x&&p[0].y==p[32].y);mark(actual,polyKey(p,count),selected);drawCalls++;return 1;}
'''
 tests=r'''
static void expected(void){int i,n;POINT points[33];FXOval *o;memset(want,0,sizeof(want));for(i=0;i<slotCount;i++)if(stars[i].visible){o=&stars[i].oval;if(!o->angle)mark(want,ellipseKey(o->cx-o->rx,o->cy-o->ry,o->cx+o->rx,o->cy+o->ry),ringPens[o->color]);else{for(n=0;n<=32;n++)fxVertex(o,n,&points[n].x,&points[n].y);mark(want,polyKey(points,33),ringPens[o->color]);}}}
int main(void){int widths[]={160,320,640},heights[]={100,200,400,480};int wi,hi,count,e,p,i,n,x,y,before,steps;FXOval shape;long shapes=0,updates=0;
 for(wi=0;wi<3;wi++)for(hi=0;hi<4;hi++)for(count=2;count<=16;count*=2)for(e=0;e<5;e++)for(p=0;p<64;p++)for(i=0;i<fxCount(e,count);i++){
 fxShape(e,p,i,fxCount(e,count),widths[wi],heights[hi],&shape);assert(shape.rx>=2&&shape.ry>=((e==4&&i<3)?1:2)&&shape.color>=0&&shape.color<8&&shape.angle>=0&&shape.angle<64);
 for(n=0;n<=32;n++){fxVertex(&shape,n,&x,&y);assert(x>=0&&x<widths[wi]&&y>=0&&y<heights[hi]);}shapes++;
 }
 for(wi=0;wi<3;wi++)for(hi=0;hi<4;hi++)for(count=2;count<=16;count*=2)for(e=0;e<5;e++){
 screenW=widths[wi];screenH=heights[hi];starCount=count;effect=e;autoEffect=0;totalCells=0;resetRain(screenW/8);for(i=0;i<8;i++)ringPens[i]=i+1;memset(actual,99,sizeof(actual));
 while(clearRow<screenH)render(0);
 for(steps=0;steps<128;steps++){before=drawCalls;render(0);assert(slotCount==fxCount(activeEffect,starCount)&&slotCount<=MAXSTARS);assert(frames==totalCells/(unsigned)starCount);assert(drawCalls-before<=2&&selected==44&&brush==45&&rop2==13);expected();assert(memcmp(actual,want,sizeof(actual))==0);updates++;}
 }
 /* Every complete scene transition clears before redrawing; no XOR ghosts. */
 autoEffect=1;starCount=2;effect=0;totalCells=0;resetRain(screenW/8);while(clearRow<screenH)render(0);for(steps=0;steps<3000;steps++){render(0);if(clearRow>=screenH){expected();assert(memcmp(actual,want,sizeof(actual))==0);}}
 /* Failure handling preserves preselected objects and ROP before closing. */
 for(i=0;i<6;i++){running=1;stopped=0;resetRain(screenW/8);clearRow=screenH;
 if(i==0)failSelect=1;if(i==1)failSelect=2;if(i==2)failRop=1;if(i==3)failDraw=1;if(i==4){render(0);stripe=0;failDraw=1;}if(i==5){clearRow=0;failClear=1;}render(0);assert(stopped==1&&!running&&selected==44&&brush==45&&rop2==13);}
 printf("PASS shapes=%ld updates=%ld transitions=5 failures=6\n",shapes,updates);return 0;}
'''
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);src=root/'check.c';src.write_text(header+setup+render+tests);exe=root/'check'
  subprocess.run(['gcc','-std=c89','-O1','-fsanitize=undefined,address','-fno-sanitize-recover=all','-I'+str(HERE),str(src),'-o',str(exe)],check=True);r=subprocess.run([str(exe)],capture_output=True,text=True)
  if r.returncode:raise ValueError(r.stdout+r.stderr)
 return {'pass':True,'result':r.stdout.strip(),'scope':'host32-bit int/64-bit long with sanitizers, GDI sparse footprint stubs; no C6/native raster/lifecycle/mode proof'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();r=check();a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
