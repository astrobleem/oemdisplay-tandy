/* SLOSH: Windows 3.0 real mode, 8086 integer spring surface. */
#define WINVER 0x0300
#include <windows.h>
#include "WATER.H"
typedef struct { DWORD ms; int event,x,left,right; } RECORD;
static RECORD records[512];static int count,started;
static void record(HWND w,int e){ RECT r; if(e==3)started=1; if(started&&count<512){GetWindowRect(w,&r);records[count].ms=GetTickCount();records[count].event=e;records[count].x=r.left;records[count].left=height[0];records[count].right=height[SAMPLES-1];count++;} }
static void saveprobe(void){ HFILE f; f=_lcreat("C:\\SLTRACE.BIN",0);if(f!=HFILE_ERROR){_lwrite(f,(LPSTR)records,count*sizeof(RECORD));_lclose(f);} }
static HBRUSH water;
static int dragging, offsetX, offsetY, lastX, speed, ready;
static DWORD lastTick;
static void freepaint(void) { if(water){DeleteObject(water);water=NULL;} }
static void stopdrag(HWND w) { if(dragging){dragging=0;if(GetCapture()==w)ReleaseCapture();} }
static int dragtarget(HWND w,RECT *r) {
 POINT p;int x,y,sw,sh,ww,hh;
 if(!dragging)return 0;
 if(GetCapture()!=w){dragging=0;return 0;}
 GetCursorPos(&p);ww=r->right-r->left;hh=r->bottom-r->top;
 sw=GetSystemMetrics(SM_CXSCREEN);sh=GetSystemMetrics(SM_CYSCREEN);
 x=bound(p.x-offsetX,0,sw-ww);y=bound(p.y-offsetY,0,sh-hh);
 if(x==r->left&&y==r->top)return 0;
 r->left=x;r->top=y;r->right=x+ww;r->bottom=y+hh;return 1;
}
static void tick(HWND w) {
 RECT r; DWORD now,dt; int dx,v,a,i,p,lo=0,hi=0,base,moving;
 GetWindowRect(w,&r);now=GetTickCount();
 if(!ready){lastX=r.left;lastTick=now;ready=1;}
 moving=dragtarget(w,&r);dt=now-lastTick;
 /* No accumulated catch-up; at most one bounded step per delivered timer. */
 dx=bound(r.left-lastX,-120,120);
 if(dt>250L)speed=0;
 if(dt<32L)dt=32L;if(dt>200L)dt=200L;
 v=bound((int)((long)dx*55L/(long)dt),-24,24);
 a=bound(v-speed,-24,24);speed=v;lastX=r.left;lastTick=now;
 for(i=0;i<SAMPLES;i++){p=height[i]/16;if(p<lo)lo=p;if(p>hi)hi=p;}
 step(a);
 /* Paint the NEW surface during a move, not an old surface then another paint. */
 if(moving)MoveWindow(w,r.left,r.top,r.right-r.left,r.bottom-r.top,TRUE);
 else if(dirty){
  for(i=0;i<SAMPLES;i++){p=height[i]/16;if(p<lo)lo=p;if(p>hi)hi=p;}
  GetClientRect(w,&r);base=r.bottom*3/5;
  r.top=bound(base+lo,0,r.bottom);r.bottom=bound(base+hi+1,r.top,r.bottom);
  InvalidateRect(w,&r,FALSE);
 }
 record(w,dragging?1:2);
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 PAINTSTRUCT ps;HDC dc;RECT r,col;POINT p;int i,x,y,base,h,last;
 switch(m){
 case WM_CREATE:
  water=CreateSolidBrush(RGB(0,0,128));
  if(!water||!SetTimer(w,1,55,NULL))return -1L;
  return 0;
 case WM_NCLBUTTONDOWN:
  if(wp==HTCAPTION){
   SetActiveWindow(w);GetCursorPos(&p);GetWindowRect(w,&r);
   record(w,3);offsetX=p.x-r.left;offsetY=p.y-r.top;dragging=1;SetCapture(w);return 0;
  }break;
 case WM_LBUTTONUP:if(dragging){record(w,4);tick(w);stopdrag(w);record(w,5);return 0;}break;
 /* Mouse messages outrank WM_TIMER in Win3. Rate-limit input-driven steps
    too, so a busy mouse queue cannot starve live movement. */
 case WM_MOUSEMOVE:if(dragging&&(DWORD)(GetTickCount()-lastTick)>=55L)tick(w);return 0;
 case WM_CANCELMODE:stopdrag(w);break;
 case WM_ACTIVATE:if(!wp)stopdrag(w);break;
 case WM_KEYDOWN:if(wp==VK_ESCAPE&&dragging){stopdrag(w);return 0;}break;
 case WM_TIMER:if(wp==1&&(!ready||(DWORD)(GetTickCount()-lastTick)>=55L))tick(w);return 0;
 case WM_ERASEBKGND:return 1;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);GetClientRect(w,&r);
  h=r.bottom;base=h*3/5;
  if(r.right>0&&h>0){
   col.left=0;col.bottom=h;last=bound(base+height[0]/16,2,h-3);
   /* Coalesce adjacent equal-height samples: flat water is one FillRect.
      Solid rectangular fills use the existing driver's cheap brush path. */
   for(i=1;i<=SAMPLES;i++){
    x=(int)((long)i*r.right/SAMPLES);
    y=i<SAMPLES?bound(base+height[i]/16,2,h-3):-1;
    if(y!=last){
     col.right=x;col.top=0;col.bottom=last;FillRect(dc,&col,GetStockObject(WHITE_BRUSH));
     col.top=last;col.bottom=h;FillRect(dc,&col,water);col.left=x;last=y;
    }
   }
  }
  EndPaint(w,&ps);return 0;
 case WM_DESTROY:
  saveprobe();
  stopdrag(w);KillTimer(w,1);freepaint();
  PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;int sw,sh,ww,hh;
 if(!prev){wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;
  wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;
  wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=NULL;
  wc.lpszMenuName=NULL;wc.lpszClassName="TandySlosh";if(!RegisterClass(&wc))return 1;}
 sw=GetSystemMetrics(SM_CXSCREEN);sh=GetSystemMetrics(SM_CYSCREEN);
 ww=sw<240?112:192;hh=sh<160?100:132;
 w=CreateWindow("TandySlosh","Slosh",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_BORDER,
  (sw-ww)/2,(sh-hh)/2,ww,hh,NULL,NULL,inst,NULL);
 if(!w){freepaint();return 2;}
 ShowWindow(w,SW_SHOWNORMAL);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 return msg.wParam;
}
