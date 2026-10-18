/* TP: a toilet-paper roll. Windows 3.0 real mode, 8086.
   No UART access, hooks, mouse-driver reset, or interrupt changes.
   Optional guarded PSG output is implemented in TPSOUND.C.
   The registered message is a proposed bridge contract, NOT a driver. */
#define WINVER 0x0300
#include <windows.h>
#include "ROLL.H"
#include "TPSOUND.H"
#include "WHEEL.H"
typedef WORD (FAR PASCAL *WHEELVER)(void);
typedef int (FAR PASCAL *WHEELREAD)(void);
static WHEELREAD wheelRead;
static int dragging,dragY,dragRemainder,flushPending,flushCount;
static HWND appWindow;
static int paper, source, testMode, testStage, testFailures;
static WORD wheelMessage;
static WORD tpQaMessage;
static int qaMode;
static DWORD directReads,bridgeYields,bridgeDeliveries;
static HWND wheelBridge(void) {
 HWND b=FindWindow(BRIDGE_CLASS,NULL);
 return b && GetProp(b,BRIDGE_PROP)==(HANDLE)BRIDGE_VERSION ? b : NULL;
}
static HBRUSH wall, shade, paperBrush, edge, core, metal;
static HDC frameDC;
static HBITMAP frameBitmap,frameOld;
static int frameW,frameH;
static void freeFrame(void) {
 if(frameDC){if(frameOld)SelectObject(frameDC,frameOld);DeleteDC(frameDC);}
 if(frameBitmap)DeleteObject(frameBitmap);
 frameDC=NULL;frameBitmap=frameOld=NULL;frameW=frameH=0;
}
static HDC paintTarget(HDC screen,int w,int h) {
 if(frameW!=w || frameH!=h)freeFrame();
 if(!frameDC){
  frameDC=CreateCompatibleDC(screen);
  if(frameDC)frameBitmap=CreateCompatibleBitmap(screen,w,h);
  if(!frameDC || !frameBitmap){freeFrame();return screen;}
  frameOld=SelectObject(frameDC,frameBitmap);frameW=w;frameH=h;
 }
 return frameDC;
}
static int sx, sy;
static int X(int n) { return (int)((long)n*sx/240L); }
static int Y(int n) { return (int)((long)n*sy/140L); }
static void box(HDC dc,int x,int y,int w,int h,HBRUSH b) {
 RECT r;r.left=X(x);r.top=Y(y);r.right=X(x+w);r.bottom=Y(y+h);FillRect(dc,&r,b);
}
static void oval(HDC dc,int x,int y,int w,int h,HBRUSH b) {
 HBRUSH old=SelectObject(dc,b);Ellipse(dc,X(x),Y(y),X(x+w),Y(y+h));SelectObject(dc,old);
}
static void line(HDC dc,int x,int y,int xx,int yy) {
 MoveTo(dc,X(x),Y(y));LineTo(dc,X(xx),Y(yy));
}
static void poly(HDC dc,POINT *p,int n,HBRUSH b) {
 int i;HBRUSH old=SelectObject(dc,b);
 for(i=0;i<n;i++){p[i].x=X(p[i].x);p[i].y=Y(p[i].y);}Polygon(dc,p,n);SelectObject(dc,old);
}
static void paint(HWND w,HDC dc) {
 RECT r;POINT p[4];int rad,top,bottom,k,tail;
 GetClientRect(w,&r);sx=r.right;sy=r.bottom;
 if(sx<1||sy<1)return;
 box(dc,0,0,240,140,wall);
 /* Wall bracket, spindle, and soft two-tone shadow. */
 box(dc,177,25,33,48,shade);box(dc,181,21,25,46,metal);
 oval(dc,167,47,28,12,core);
 rad=roll_radius(paper);top=56-rad;bottom=56+rad;
 oval(dc,123,top+6,69,rad*2+3,shade);
 p[0].x=43;p[0].y=top+4;p[1].x=139;p[1].y=top;
 p[2].x=151;p[2].y=bottom;p[3].x=43;p[3].y=bottom-6;
 poly(dc,p,4,paper==ROLL_MAX?core:paperBrush);
 oval(dc,110,top,65,rad*2,paper==ROLL_MAX?core:edge);
 oval(dc,121,top+6,48,rad*2-12,paper==ROLL_MAX?core:paperBrush);
 oval(dc,132,43,25,26,core);oval(dc,142,48,13,16,shade);
 oval(dc,157,47,29,13,metal);oval(dc,178,47,10,13,core);
 /* The front sheet unspools directly with detents, bounded, with no score or other game mechanics. */
 if(paper==ROLL_MAX)return;
 tail=roll_tail(paper);
 p[0].x=43;p[0].y=top+6;p[1].x=116;p[1].y=top+3;
 p[2].x=110;p[2].y=tail-3;p[3].x=37;p[3].y=tail;
 poly(dc,p,4,paperBrush);
 for(k=top+13+(paper%12);k<tail-3;k+=12){
  int j;for(j=44;j<107;j+=7)line(dc,j,k,j+3,k);
 }
 /* One gently curling lower edge. */
 line(dc,38,tail-1,109,tail-4);

}
static void stopDrag(HWND w) {
 dragging=0;dragRemainder=0;if(GetCapture()==w)ReleaseCapture();
}
static void movePaper(HWND w,int delta,int fromBridge) {
 int old=paper;paper=roll_move(paper,delta);source=fromBridge;
 if(paper!=old){if(paper==ROLL_MAX){flushPending=1;++flushCount;stopDrag(w);}
 InvalidateRect(w,NULL,FALSE);}
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 PAINTSTRUCT ps;HDC dc,target;RECT area;
 if(qaMode&&m==tpQaMessage&&lp==1L){
  if(wp==1)return paper;if(wp==2)return directReads;
  if(wp==3)return bridgeYields;if(wp==4)return bridgeDeliveries;
  return 0;
 }
 if(wheelMessage&&m==wheelMessage){
  /* Signed detents, either direction unrolls; lp must be contract version 1.
     Messages are not evidence of a hardware source. */
  if(lp==1L&&wp&&(int)wp>=-15&&(int)wp<=15 &&
     (!wheelBridge() || (GetActiveWindow()==w&&!IsIconic(w)&&!GetCapture()&&!GetSysModalWindow()))){
   ++bridgeDeliveries;movePaper(w,(int)wp,1);
  }
  return 0;
 }
 switch(m){
 case WM_CREATE:return 0;
 case WM_LBUTTONDOWN:
  if(paper<ROLL_MAX && sx && sy && (int)LOWORD(lp)>=X(35) &&
     (int)LOWORD(lp)<=X(116) && (int)HIWORD(lp)>=Y(62-roll_radius(paper)) &&
     (int)HIWORD(lp)<=Y(roll_tail(paper))) {
   dragging=1;dragY=(int)HIWORD(lp);dragRemainder=0;SetCapture(w);
  }return 0;
 case WM_MOUSEMOVE:
  if(dragging){int dy,steps,y;
   if(GetCapture()!=w){dragging=0;return 0;}
   y=(int)HIWORD(lp);dy=y-dragY;dragY=y;
   if(dy>0){dragRemainder+=dy;steps=dragRemainder/3;dragRemainder%=3;
    if(steps)movePaper(w,steps,0);}
  }return 0;
 case WM_LBUTTONUP:stopDrag(w);return 0;
 case WM_CANCELMODE:stopDrag(w);TpSoundStop(w);flushPending=0;break;
 case WM_ACTIVATE:if(!wp){stopDrag(w);TpSoundStop(w);flushPending=0;}break;
 case WM_KILLFOCUS:stopDrag(w);TpSoundStop(w);flushPending=0;break;
 case WM_CLOSE:stopDrag(w);TpSoundStop(w);flushPending=0;DestroyWindow(w);return 0;
 case WM_ERASEBKGND:return 1;
 case WM_KEYDOWN:
  if(wp==VK_DOWN){movePaper(w,1,0);return 0;}
  if(wp==VK_UP){movePaper(w,-1,0);return 0;}
  if(wp=='R'||wp==VK_HOME){stopDrag(w);TpSoundStop(w);flushPending=0;paper=source=0;InvalidateRect(w,NULL,FALSE);return 0;}
  if(wp==VK_ESCAPE){stopDrag(w);return 0;}
  break;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);GetClientRect(w,&area);
  if(area.right>0 && area.bottom>0){
   target=paintTarget(dc,area.right,area.bottom);paint(w,target);
   if(target!=dc && !BitBlt(dc,0,0,area.right,area.bottom,target,0,0,SRCCOPY))paint(w,dc);
  }
  EndPaint(w,&ps);return 0;
 case WM_TIMER:
  if(wp==1){int count,delta;
   if(wheelBridge())++bridgeYields;
   else if(wheelRead){for(count=0;count<32;count++){
    ++directReads;delta=wheelRead();if(!delta)break;
    if(GetActiveWindow()==w && !IsIconic(w))movePaper(w,delta,1);
   }}
   if(flushPending){flushPending=0;TpSoundBegin(w,TD_SND_REVEAL,GetTickCount());}
   TpSoundTick(w,GetTickCount());return 0;
  }
  if(testMode && wp==2){
   ++testStage;
   if(testStage==2){SendMessage(w,WM_KEYDOWN,VK_DOWN,0L);if(paper!=3)++testFailures;}
   if(testStage==3){int y; y=Y(60);
    SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(X(60),y));
    SendMessage(w,WM_MOUSEMOVE,MK_LBUTTON,MAKELONG(X(60),y+9));
    SendMessage(w,WM_LBUTTONUP,0,MAKELONG(X(60),y+9));
    if(paper!=12 || dragging || GetCapture()==w)++testFailures;
    SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(X(60),y));
    SendMessage(w,WM_CANCELMODE,0,0L);
    if(dragging || GetCapture()==w)++testFailures;
   }
   if(testStage==4){SendMessage(w,wheelMessage,8,1L);if(paper!=36)++testFailures;
    SendMessage(w,wheelMessage,8,2L);if(paper!=36)++testFailures;}
   if(testStage==6){int j;for(j=0;j<100;j++)SendMessage(w,WM_KEYDOWN,VK_DOWN,0L);
    if(paper!=ROLL_MAX)++testFailures;SendMessage(w,WM_KEYDOWN,VK_UP,0L);
    if(paper!=ROLL_MAX)++testFailures;}
   if(testStage==8 && (flushCount!=1 || paper!=ROLL_MAX))++testFailures;
   if(testStage==10){SendMessage(w,WM_KEYDOWN,'R',0L);if(paper)++testFailures;}
   if(testStage==12){HFILE f;char text[240];int n;TDSNDSTAT snd;
    TpSoundGetStats(&snd);
    f=_lcreat("C:\\TPTEST.LOG",0);n=wsprintf(text,"COMPLETE=1\r\nFINAL_PAPER=%d\r\nFAIL_COUNT=%d\r\nFLUSH_TRANSITIONS=%d\r\nSOUND_SUPPORTED=%u\r\nSOUND_STARTED=%lu\r\nSOUND_COMPLETED=%lu\r\nSOUND_BUSY_SKIPS=%lu\r\nWHEEL_API_PRESENT=%u\r\n",paper,testFailures,flushCount,snd.supported,snd.starts[0],snd.completions[0],snd.busySkips,wheelRead!=NULL);
    if(f!=-1){_lwrite(f,text,n);_lclose(f);}DestroyWindow(w);
   }
  }return 0;
 case WM_DESTROY:RemoveProp(w,CLIENT_PROP);freeFrame();stopDrag(w);TpSoundStop(w);KillTimer(w,1);KillTimer(w,2);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;int sw,sh,ww,hh,timerReady;
 HMODULE mouse;WHEELVER wheelVer;
 FARPROC proc;
 HBRUSH brushes[6];int i;
 if(prev||FindWindow("WindowsXTToiletPaper",NULL))return 0;
 wall=brushes[0]=CreateSolidBrush(RGB(192,192,192));
 shade=brushes[1]=CreateSolidBrush(RGB(128,128,128));
 paperBrush=brushes[2]=CreateSolidBrush(RGB(255,255,255));
 edge=brushes[3]=CreateSolidBrush(RGB(192,192,192));
 core=brushes[4]=CreateSolidBrush(RGB(128,64,0));
 metal=brushes[5]=CreateSolidBrush(RGB(192,192,192));
 for(i=0;i<6;i++)if(!brushes[i]){int j;for(j=0;j<6;j++)if(brushes[j])DeleteObject(brushes[j]);return 2;}
 wheelMessage=RegisterWindowMessage("WindowsXT.Wheel.v1");
 tpQaMessage=RegisterWindowMessage(TPQA_NAME);qaMode=cmd&&!lstrcmpi(cmd,"/QA");
 mouse=GetModuleHandle("MOUSE");wheelRead=NULL;
 wheelVer=mouse?(WHEELVER)GetProcAddress(mouse,"WheelApiVersion"):NULL;
 if(wheelVer && wheelVer()==0x0100)
  wheelRead=(WHEELREAD)GetProcAddress(mouse,"WheelReadDelta");
 testMode=cmd&&cmd[0]=='/'&&(cmd[1]=='T'||cmd[1]=='t');
 proc=MakeProcInstance((FARPROC)WndProc,inst);if(!proc){for(i=0;i<6;i++)DeleteObject(brushes[i]);return 2;}
 if(!prev){wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=(WNDPROC)proc;
 wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;
 wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=NULL;
 wc.lpszMenuName=NULL;wc.lpszClassName="WindowsXTToiletPaper";
 if(!RegisterClass(&wc)){FreeProcInstance(proc);for(i=0;i<6;i++)DeleteObject(brushes[i]);return 1;}}
 sw=GetSystemMetrics(SM_CXSCREEN);sh=GetSystemMetrics(SM_CYSCREEN);
 ww=sw<296?sw-16:280;hh=sh<192?sh-16:176;
 w=CreateWindow("WindowsXTToiletPaper",wheelRead?"TP":"TP (drag / arrows)",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_BORDER,
 (sw-ww)/2,(sh-hh)/2,ww,hh,NULL,NULL,inst,NULL);
 if(w){appWindow=w;
 if(!SetProp(w,CLIENT_PROP,(HANDLE)BRIDGE_VERSION)){DestroyWindow(w);w=NULL;}
 }
 if(w){timerReady=SetTimer(w,1,100,NULL)!=0;
 TpSoundInit(w,inst,timerReady);
 ShowWindow(w,SW_SHOWNORMAL);UpdateWindow(w);
 if(testMode&&!SetTimer(w,2,350,NULL)){DestroyWindow(w);w=NULL;}
 if(w)while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}}
 TpSoundStop(appWindow);freeFrame();for(i=0;i<6;i++)DeleteObject(brushes[i]);FreeProcInstance(proc);return w?0:2;
}
