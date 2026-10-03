#define WINVER 0x0300
#include <windows.h>
#include "WATER.H"
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){
 int i,t,flip=0,fail=0,a=0;HFILE f;
 step(24);if(height[0]>=0||height[39]<=0)fail++;
 for(t=0;t<500;t++){step(0);if(height[0]>0)flip=1;}if(!flip)fail++;
 for(i=0;i<40;i++)if(height[i]||velocity[i])fail++;
 step(-24);if(height[0]<=0||height[39]>=0)fail++;
 for(t=0;t<4000;t++){a=(a+31)%49;step(a-24);for(i=0;i<40;i++)if(height[i]<-512||height[i]>512||velocity[i]<-128||velocity[i]>128)fail++;}
 for(t=0;t<500;t++)step(0);for(i=0;i<40;i++)if(height[i]||velocity[i])fail++;
 f=_lcreat("C:\\SLOSHUT.LOG",0);if(f!=HFILE_ERROR){if(fail)_lwrite(f,"FAIL",4);else _lwrite(f,"PASS: direction both ways, rebound, zero settle, 4000 stress ticks",64);_lclose(f);}return fail;
}
