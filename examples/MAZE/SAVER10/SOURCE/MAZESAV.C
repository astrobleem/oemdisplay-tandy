/* MAZE /S: bounded native framebuffer saver; lifecycle adapted from Matrix.
   Verified original profiles use native presentation; all other driver
   identities use clipped GDI column presentation, never raw framebuffer writes. */
#define WINVER 0x0300
#include <windows.h>
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
static HINSTANCE instance;
static HWND saver,qa,overlay;
static HWND previousActive,previousFocus;
static int saverMode,draining,returnFocus,mouseHeld,mouseGesture;
static BYTE initialKeys[256],downKeys[256];
static DWORD armStarted,lastInput;
static char wakeReason[40];
static HCURSOR previousCursor;
static HDC screenDC,backDC;
static HBITMAP bitmap,oldBitmap;
static int screenW,screenH,colors,fast,kind,banks,bytesPerCell;
static unsigned char bios;
static int running,hidden,closing,forceGDI,testing,capture,qaMode,testStep,testFrames,activated,recovering;
static DWORD started,firstTick,drawMs,maxDraw,freeWarm,startup,restoreMs;
static unsigned long totalCells;
static POINT origin;
static char logpath[144],driver[128],why[40];
static HGLOBAL snapshot;
static unsigned char FAR *snap;
static unsigned char FAR *vram=(unsigned char FAR *)0xb8000000L;
static unsigned offsets[200];
static unsigned char packed[4][256][4];
static unsigned char dirtyFlag[MAXCELL],dirtyCol[MAXCOL*4],dirtyRow[MAXCOL*4];
static int dirtyCount,qaDrainStage;
static void logtext(char *s){HFILE f=_lopen(logpath,OF_WRITE);if(f==HFILE_ERROR)f=_lcreat(logpath,0);if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);}}
static void dump(char *name){HFILE f;char path[144];int i;if(!fast){logtext("CAPTURE skipped: unverified framebuffer\r\n");return;}lstrcpy(path,logpath);for(i=lstrlen(path)-1;i>=0&&path[i]!='\\';i--);path[i+1]=0;lstrcat(path,name);f=_lcreat(path,0);if(f!=HFILE_ERROR){_lwrite(f,(LPSTR)vram,banks==4?32768U:16384U);_lclose(f);}}
static int detect(void){HDC dc;HMODULE mod;char *base;int i;
 screenW=GetSystemMetrics(SM_CXSCREEN);screenH=GetSystemMetrics(SM_CYSCREEN);dc=GetDC(NULL);colors=GetDeviceCaps(dc,NUMCOLORS);ReleaseDC(NULL,dc);
 if(GetWinFlags()&WF_PMODE)return 0;
 mod=GetModuleHandle("DISPLAY");driver[0]=0;if(mod)GetModuleFileName(mod,driver,sizeof(driver));base=driver;for(i=0;driver[i];i++)if(driver[i]=='\\'||driver[i]==':')base=driver+i+1;
 bios=*((unsigned char FAR *)0x00400049L);banks=2;if(*((unsigned char FAR *)0x00400062L)!=0)return 0;
 if(screenH!=200)return 0;
 if(screenW==160&&colors==16&&bios==8&&!lstrcmpi(base,"TNDY160.DRV")){kind=0;return 1;}
 if(screenW==320&&colors==16&&bios==9&&!lstrcmpi(base,"TANDY88.DRV")){kind=0;banks=4;return 1;}
 if(screenW==320&&colors==4&&bios==4&&!lstrcmpi(base,"TNDY3204.DRV")){kind=1;return 1;}
 if(screenW==640&&colors==4&&bios==10&&!lstrcmpi(base,"TNDY6404.DRV")){kind=2;banks=4;return 1;}
 if(screenW==640&&colors==2&&bios==6&&!lstrcmpi(base,"TNDY6402.DRV")){kind=3;return 1;}
 return 0;}
static int ownsScreen(void){HWND w;RECT r;if(GetActiveWindow()!=saver)return 0;
 if(saverMode&&(GetCapture()!=saver||GetFocus()!=saver))return 0;
 if(fast&&(*((unsigned char FAR *)0x00400049L)!=bios||*((unsigned char FAR *)0x00400062L)!=0))return 0;
 for(w=GetWindow(saver,GW_HWNDPREV);w;w=GetWindow(w,GW_HWNDPREV))if(IsWindowVisible(w)&&!IsIconic(w)){GetWindowRect(w,&r);if(r.right>0&&r.bottom>0&&r.left<screenW&&r.top<screenH)return 0;}
 return 1;}
/* Four independently bounded 8-pixel columns per message. Ray DDA has at
   most 24 boundary crossings; no full-frame GDI call or busy-wait. Returning
   to GetMessage between slices lets input/activation/shutdown preempt work. */
static int disrupted(void){return 0;}
static void render(int full){int batch,y,j,top,bottom,s;RECT r;unsigned off,bits;unsigned char *p;DWORD t=GetTickCount();
 if(!running||!ownsScreen())return;
 for(batch=0;batch<(fast?4:1);batch++){
  castOne(stripe,columns,200);top=(200-(int)walls[stripe])/2;bottom=top+walls[stripe];
  if(!fast){
   SetRect(&r,0,0,8,top);FillRect(backDC,&r,GetStockObject(BLACK_BRUSH));
   SetRect(&r,0,top,8,bottom);FillRect(backDC,&r,GetStockObject(shades[stripe]==0?WHITE_BRUSH:shades[stripe]==1?LTGRAY_BRUSH:shades[stripe]==2?GRAY_BRUSH:DKGRAY_BRUSH));
   SetRect(&r,0,bottom,8,200);FillRect(backDC,&r,GetStockObject(DKGRAY_BRUSH));
   if(!ownsScreen())return;
   BitBlt(screenDC,stripe*8,0,8,200,backDC,0,0,SRCCOPY);
  }else for(y=0;y<200;y++){
   s=y<top?0:y>=bottom?1:3-(shades[stripe]>1?1:0);
   bits=255;if(y>=top&&y<bottom&&(shades[stripe]&1))bits=(y&1)?0xAA:0x55;
   if(s==1)bits=(y&1)?0xAA:0x55;
   p=packed[s][bits];off=offsets[y]+stripe*bytesPerCell;
   for(j=0;j<bytesPerCell;j++)vram[off+j]=p[j];
  }
  totalCells++;if(++stripe>=columns){stripe=0;frames++;advance();}
 }
 t=GetTickCount()-t;drawMs+=t;if(t>maxDraw)maxDraw=t;
}
static void restore(void){DWORD t;if(!screenDC)return;t=GetTickCount();
 /* Self-copy forces the known driver's canonical shadow back to VRAM.
    Never restore a stale saved bitmap over another application's output. */
 if(fast&&*((unsigned char FAR *)0x00400049L)==bios&&*((unsigned char FAR *)0x00400062L)==0)BitBlt(screenDC,0,0,1,1,screenDC,0,0,SRCCOPY);
 restoreMs=GetTickCount()-t;}
static void stop(HWND w,char *reason){char b[320];int focusBack=saverMode&&returnFocus&&GetActiveWindow()==w;DWORD elapsed=firstTick?GetTickCount()-firstTick:0UL;if(closing)return;closing=1;running=0;draining=0;lstrcpy(why,reason);KillTimer(w,1);if(saverMode&&GetCapture()==w)ReleaseCapture();restore();
 if(hidden){SetCursor(previousCursor);ShowCursor(TRUE);hidden=0;}if(testing){wsprintf(b,"END reason=%s fast=%d width=%d colors=%d bios=%d ticks=%lu columns=%lu frames=%lu elapsed_ms=%lu draw_ms=%lu max_draw_ms=%lu startup_ms=%lu restore_ms=%lu free_warm=%lu free_end=%lu\r\n",(LPSTR)why,fast,screenW,colors,(int)bios,ticks,totalCells,frames,elapsed,drawMs,maxDraw,startup,restoreMs,freeWarm,GetFreeSpace(0));logtext(b);}
 DestroyWindow(w);
 if(focusBack&&IsWindow(previousActive)&&IsWindowVisible(previousActive)&&IsWindowEnabled(previousActive)){
  SetActiveWindow(previousActive);
  if(IsWindow(previousFocus)&&IsWindowEnabled(previousFocus)&&(previousFocus==previousActive||IsChild(previousActive,previousFocus)))SetFocus(previousFocus);
 }
}
/* /S owns only its own input queue. No global hook or password lock. */
static void beginWake(HWND w,char *reason){
 if(!saverMode){stop(w,reason);return;}
 if(closing)return;
 if(!draining){lstrcpy(wakeReason,reason);draining=1;running=0;returnFocus=1;if(testing)logtext("DRAIN begin\r\n");}
 lastInput=GetTickCount();
}
static int keysHeld(void){int i;for(i=3;i<256;i++)if(i!=VK_MBUTTON&&downKeys[i]){if(GetAsyncKeyState(i)&0x8000)return 1;downKeys[i]=0;}return 0;}
static void noteMouse(UINT m,WPARAM wp){
 mouseHeld=wp&(MK_LBUTTON|MK_RBUTTON|MK_MBUTTON);
 if(m==WM_LBUTTONDOWN||m==WM_LBUTTONDBLCLK)mouseHeld|=MK_LBUTTON;
 if(m==WM_RBUTTONDOWN||m==WM_RBUTTONDBLCLK)mouseHeld|=MK_RBUTTON;
 if(m==WM_MBUTTONDOWN||m==WM_MBUTTONDBLCLK)mouseHeld|=MK_MBUTTON;
 if(m==WM_LBUTTONUP)mouseHeld&=~MK_LBUTTON;
 if(m==WM_RBUTTONUP)mouseHeld&=~MK_RBUTTON;
 if(m==WM_MBUTTONUP)mouseHeld&=~MK_MBUTTON;
}
static int saverInput(HWND w,UINT m,WPARAM wp,LPARAM lp){int dx,dy,old;
 if(!saverMode)return 0;
 if(m>=WM_KEYFIRST&&m<=WM_KEYLAST){
  if(m==WM_KEYDOWN||m==WM_SYSKEYDOWN){if(wp<256)downKeys[wp]=1;beginWake(w,"keyboard");}
  else if(m==WM_KEYUP||m==WM_SYSKEYUP){old=wp<256?initialKeys[wp]:0;if(wp<256){downKeys[wp]=0;initialKeys[wp]=0;}
   /* Ignore only the release of a key already down when /S started,
      and only during a 250 ms startup interval. New input always wakes. */
   if(!old||GetTickCount()-armStarted>=250UL||draining)beginWake(w,"key-release");
  }else beginWake(w,"keyboard-char");
  return 1;
 }
 if(m>=WM_MOUSEFIRST&&m<=WM_MOUSELAST){
  if(m!=WM_MOUSEMOVE)mouseGesture=1;noteMouse(m,wp);dx=(int)LOWORD(lp)-origin.x;dy=(int)HIWORD(lp)-origin.y;
  if(m!=WM_MOUSEMOVE||dx||dy)beginWake(w,m==WM_MOUSEMOVE?"mouse-move":"mouse-button");
  return 1;
 }
 return 0;
}
static void drainTick(HWND w){MSG msg;DWORD quiet=mouseGesture?(DWORD)GetDoubleClickTime():110UL;if(quiet<110UL)quiet=110UL;
 if(GetActiveWindow()!=w||GetCapture()!=w||GetFocus()!=w){returnFocus=0;stop(w,"drain-ownership-lost");return;}
 if(keysHeld()||mouseHeld){lastInput=GetTickCount();return;}
 /* Hardware input wins over this low-priority timer. Remove any remaining
    own-window input without generating WM_CHAR or forwarding it elsewhere. */
 while(PeekMessage(&msg,w,WM_KEYFIRST,WM_KEYLAST,PM_REMOVE))saverInput(w,msg.message,msg.wParam,msg.lParam);
 while(PeekMessage(&msg,w,WM_MOUSEFIRST,WM_MOUSELAST,PM_REMOVE))saverInput(w,msg.message,msg.wParam,msg.lParam);
 if(keysHeld()||mouseHeld||GetTickCount()-lastInput<quiet)return;
 if(testing)logtext("DRAIN released\r\n");stop(w,wakeReason);
}
static int initDraw(HWND w){int y,s,b,x,j;unsigned value,color;
 screenDC=GetDC(w);if(!screenDC)return 0;
 if(!fast){
  backDC=CreateCompatibleDC(screenDC);if(!backDC)return 0;
  bitmap=CreateCompatibleBitmap(screenDC,8,200);if(!bitmap)return 0;
  oldBitmap=SelectObject(backDC,bitmap);if(!oldBitmap)return 0;
  if(!ownsScreen())return 0;
  PatBlt(screenDC,0,0,screenW,screenH,BLACKNESS);return 1;
 }
 bytesPerCell=kind==0?4:kind==3?1:2;
 for(y=0;y<200;y++)offsets[y]=rowOffset(y,banks);
 for(s=0;s<4;s++)for(b=0;b<256;b++){
  color=s==3?(kind==0?15:3):s==2?(kind==0?7:2):s==1?(kind==0?8:1):0;
  if(kind==2){packed[s][b][0]=(unsigned char)((color&1)?b:0);packed[s][b][1]=(unsigned char)((color&2)?b:0);}
  else if(kind==3)packed[s][b][0]=(unsigned char)(s?b:0);
  else for(x=0;x<bytesPerCell;x++){value=0;for(j=0;j<8/bytesPerCell;j++)value=(value<<(bytesPerCell==4?4:2))|((b&(128>>(x*(8/bytesPerCell)+j)))?color:0);packed[s][b][x]=(unsigned char)value;}
 }
 return 1;
}
LONG FAR PASCAL SaverProc(HWND w,UINT m,WPARAM wp,LPARAM lp){PAINTSTRUCT ps;int dx,dy,repair;
 if(saverInput(w,m,wp,lp))return 0;
 switch(m){
 case WM_CREATE:return 0;
 case WM_KILLFOCUS:if(running||draining){returnFocus=0;stop(w,"focus-lost");}return 0;
 case WM_ACTIVATE:if(wp==WA_INACTIVE&&(running||draining)){returnFocus=0;stop(w,"deactivated");}else if(wp!=WA_INACTIVE)activated=1;return 0;
 case WM_ACTIVATEAPP:if(!wp&&(running||draining)){returnFocus=0;stop(w,"task-switch");}return 0;
 case WM_CANCELMODE:if(running||draining){returnFocus=0;stop(w,"cancel-mode");}return 0;
 case WM_ERASEBKGND:return 1;
 case WM_SETCURSOR:SetCursor(NULL);return 1;
 case WM_PAINT:BeginPaint(w,&ps);EndPaint(w,&ps);if(running)render(1);return 0;
 case WM_TIMER:
  if(wp!=1)return 0;
  if(draining){drainTick(w);return 0;}
  if(!running)return 0;
  if(!ownsScreen()){stop(w,"ownership-lost");return 0;}
  if(!firstTick){firstTick=GetTickCount();freeWarm=GetFreeSpace(0);}
  repair=!ticks||disrupted();stepRain();render(repair);
  if(qaMode&&recovering){recovering=0;stop(w,"repaint-disruption");return 0;}
  if(qaMode&&++testFrames==4){PostMessage(qa,WM_USER+2,0,0);return 0;}
  if(capture&&ticks==40)dump("MAZE.RAW");
  if(testing&&!qaMode&&ticks==(fast?60:160)){stop(w,"benchmark");return 0;}return 0;
 case WM_KEYDOWN:case WM_SYSKEYDOWN:case WM_CHAR:if(running){stop(w,"keyboard");return 0;}break;
 case WM_LBUTTONDOWN:case WM_RBUTTONDOWN:case WM_MBUTTONDOWN:if(running){stop(w,"mouse-button");return 0;}break;
 case WM_MOUSEMOVE:if(running){dx=(int)LOWORD(lp)-origin.x;dy=(int)HIWORD(lp)-origin.y;if(dx>2||dx<-2||dy>2||dy<-2)stop(w,"mouse-move");}return 0;
 case WM_QUERYENDSESSION:returnFocus=0;stop(w,"shutdown");return 1;
 case WM_ENDSESSION:if(wp||saverMode){returnFocus=0;stop(w,wp?"shutdown":"shutdown-cancelled");}return 0;
 case WM_CLOSE:returnFocus=0;stop(w,"close");return 0;
 case WM_DESTROY:
  running=draining=0;KillTimer(w,1);if(saverMode&&GetCapture()==w)ReleaseCapture();if(hidden){SetCursor(previousCursor);ShowCursor(TRUE);hidden=0;}if(backDC){if(bitmap){SelectObject(backDC,oldBitmap);DeleteObject(bitmap);}DeleteDC(backDC);}backDC=NULL;bitmap=NULL;
  if(screenDC)ReleaseDC(w,screenDC);screenDC=NULL;saver=NULL;
  if(qaMode)PostMessage(qa,WM_USER+3,0,0);else PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);}
static int startSaver(void){char b[220];int n;
 if(saverMode&&(GetCapture()||GetSysModalWindow()))return 0;
 previousActive=GetActiveWindow();previousFocus=GetFocus();draining=returnFocus=mouseHeld=mouseGesture=0;
 if(saverMode){GetKeyboardState(initialKeys);for(n=0;n<256;n++){initialKeys[n]&=0x80;downKeys[n]=(BYTE)(initialKeys[n]?1:0);}
  if(initialKeys[VK_LBUTTON])mouseHeld|=MK_LBUTTON;if(initialKeys[VK_RBUTTON])mouseHeld|=MK_RBUTTON;if(initialKeys[VK_MBUTTON])mouseHeld|=MK_MBUTTON;
  GetCursorPos(&origin);armStarted=GetTickCount();
 }
 previousCursor=SetCursor(NULL);SetCursor(previousCursor);running=hidden=closing=0;activated=0;firstTick=drawMs=maxDraw=restoreMs=totalCells=0;testFrames=0;started=GetTickCount();
 dirtyCount=0;resetRain(screenW/8);for(n=0;n<MAXCELL;n++)dirtyFlag[n]=0;
 saver=CreateWindow(saverMode?"TandyMazeSaver":"TandyMaze","Maze",WS_POPUP,0,0,screenW,screenH,NULL,NULL,instance,NULL);if(!saver)return 0;
 if(saverMode&&(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=previousActive)){stop(saver,"startup-owner-changed");return 0;}
 ShowWindow(saver,SW_SHOW);SetActiveWindow(saver);if(saverMode){if(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=saver){stop(saver,"startup-owner-changed");return 0;}SetFocus(saver);SetCapture(saver);if(GetCapture()!=saver||GetActiveWindow()!=saver){stop(saver,"activation-failed");return 0;}}UpdateWindow(saver);if(!saverMode)GetCursorPos(&origin);ScreenToClient(saver,&origin);
 if(closing||!IsWindow(saver))return 0;
 if(!ownsScreen()){returnFocus=0;stop(saver,"startup-ownership-lost");return 0;}
 if(!initDraw(saver)){stop(saver,"allocation-failed");return 0;}
 ShowCursor(FALSE);hidden=1;SetCursor(NULL);if(!draining){running=1;render(1);}startup=GetTickCount()-started;
 if(!SetTimer(saver,1,55,NULL)){stop(saver,"timer-failed");return 0;}
 if(testing){wsprintf(b,"START driver=%s fast=%d width=%d colors=%d bios=%d\r\n",(LPSTR)driver,fast,screenW,colors,(int)bios);logtext(b);}return 1;}
static unsigned compareScreen(int save){int y,x,n=0;HDC dc;COLORREF color;DWORD FAR *samples;unsigned off,bad=0;if(!snap)return 65535U;
 if(!fast){samples=(DWORD FAR *)snap;dc=GetDC(qa);if(!dc)return 65535U;for(y=0;y<200;y+=8)for(x=0;x<screenW;x+=8){color=GetPixel(dc,x,y);if(save)samples[n]=color;else if(samples[n]!=color)bad++;n++;}ReleaseDC(qa,dc);return bad;}
 for(y=0;y<200;y++){off=rowOffset(y,banks);for(x=0;x<(banks==4?160:80);x++)if(save)snap[off+x]=vram[off+x];else if(snap[off+x]!=vram[off+x])bad++;}return bad;}
LONG FAR PASCAL QaProc(HWND w,UINT m,WPARAM wp,LPARAM lp){HDC dc;PAINTSTRUCT ps;RECT r;char b[160];unsigned bad;
 switch(m){
 case WM_ERASEBKGND:return 1;
 case WM_SETCURSOR:SetCursor(NULL);return 1;
 case WM_PAINT:dc=BeginPaint(w,&ps);GetClientRect(w,&r);FillRect(dc,&r,GetStockObject(WHITE_BRUSH));SetBkMode(dc,TRANSPARENT);TextOut(dc,4,4,"DESKTOP RESTORED",16);MoveTo(dc,0,80);LineTo(dc,screenW,160);EndPaint(w,&ps);return 0;
 case WM_USER+1:UpdateWindow(w);compareScreen(1);if(!startSaver()){logtext("QA start failed\r\n");DestroyWindow(w);}return 0;
 case WM_USER+2:
  if(qaMode==2)return 0;
  if(testStep==0){SendMessage(saver,WM_KEYDOWN,VK_ESCAPE,0L);if(saverMode){SendMessage(saver,WM_CHAR,27,0L);SendMessage(saver,WM_KEYUP,VK_ESCAPE,0L);}}
  else if(testStep==1){SendMessage(saver,WM_LBUTTONDOWN,MK_LBUTTON,0L);if(saverMode)SendMessage(saver,WM_LBUTTONUP,0,0L);}
  else if(testStep==2)SendMessage(saver,WM_MOUSEMOVE,0,MAKELONG((origin.x+(saverMode?1:20))%screenW,(origin.y+(saverMode?0:20))%200));
  else if(testStep==3)SetActiveWindow(w);
  else if(testStep==4)SendMessage(saver,WM_CLOSE,0,0L);
  else if(testStep==5){SendMessage(saver,WM_SYSKEYDOWN,VK_MENU,0L);if(saverMode){SendMessage(saver,WM_SYSCHAR,'x',0L);SendMessage(saver,WM_SYSKEYUP,VK_MENU,0L);}}
  else if(testStep==6)SendMessage(saver,WM_CANCELMODE,0,0L);
  else if(testStep==7)SendMessage(saver,WM_QUERYENDSESSION,0,0L);
  else if(testStep==8)SendMessage(saver,WM_ACTIVATEAPP,0,0L);
  else if(testStep==9){recovering=1;dc=GetDC(NULL);BitBlt(dc,0,0,1,1,dc,0,0,SRCCOPY);ReleaseDC(NULL,dc);}
  else if(testStep==10){overlay=CreateWindow("STATIC","",WS_POPUP|SS_BLACKRECT,8,8,8,8,NULL,NULL,instance,NULL);ShowWindow(overlay,SW_SHOWNOACTIVATE);}
  else if(testStep==11){SendMessage(saver,WM_KEYDOWN,VK_RETURN,0L);SendMessage(saver,WM_ENDSESSION,FALSE,0L);}
  else if(testStep==12){qaDrainStage=0;SendMessage(saver,WM_LBUTTONDOWN,MK_LBUTTON,0L);SetTimer(w,3,440,NULL);}
  else if(testStep==13){SendMessage(saver,WM_MOUSEMOVE,0,MAKELONG(origin.x,origin.y));logtext(draining?"SYNTHETIC FAIL\r\n":"SYNTHETIC PASS\r\n");SendMessage(saver,WM_KEYUP,VK_F1,0L);}
  else if(testStep==14)SetCapture(w);
  else if(testStep==15)SetFocus(w);
  return 0;
 case WM_TIMER:
  if(wp==5){KillTimer(w,5);logtext("INPUT OBSERVATION DONE\r\n");DestroyWindow(w);return 0;}
  if(wp==3){KillTimer(w,3);logtext(IsWindow(saver)&&draining&&GetCapture()==saver?"HELD MOUSE PASS\r\n":"HELD MOUSE FAIL\r\n");
   if(!qaDrainStage++){SendMessage(saver,WM_LBUTTONUP,0,0L);SendMessage(saver,WM_LBUTTONDOWN,MK_LBUTTON,0L);SetTimer(w,3,440,NULL);}
   else SendMessage(saver,WM_LBUTTONUP,0,0L);
  }return 0;
 case WM_USER+3:if(saverMode&&testStep==14){logtext(GetCapture()==w?"CAPTURE THEFT PASS\r\n":"CAPTURE THEFT FAIL\r\n");if(GetCapture()==w)ReleaseCapture();}if(overlay){DestroyWindow(overlay);overlay=NULL;}UpdateWindow(w);bad=compareScreen(0);wsprintf(b,"QA step=%d changed_units=%u active_ok=%d raw=%d capture_released=%d\r\n",testStep,bad,GetActiveWindow()==w,fast,GetCapture()==NULL);logtext(b);
  if(qaMode==2){SetTimer(w,5,1500,NULL);return 0;}
  if(++testStep<(saverMode?16:11))PostMessage(w,WM_USER+1,0,0L);else{dump("RESTORE.RAW");logtext("QA DONE\r\n");DestroyWindow(w);}return 0;
 case WM_KEYDOWN:case WM_KEYUP:case WM_SYSKEYDOWN:case WM_SYSKEYUP:case WM_CHAR:case WM_LBUTTONDOWN:case WM_LBUTTONUP:case WM_LBUTTONDBLCLK:logtext("INPUT LEAK\r\n");return 0;
 case WM_DESTROY:if(snap)GlobalUnlock(snapshot);if(snapshot)GlobalFree(snapshot);ShowCursor(TRUE);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);}
int PASCAL SaverMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;MSG msg;int i,n;HFILE f;
 instance=inst;saverMode=cmd[0]=='/'&&(cmd[1]=='S'||cmd[1]=='s'||cmd[1]=='A'||cmd[1]=='a'||cmd[1]=='B'||cmd[1]=='b'||cmd[1]=='I'||cmd[1]=='i');
 if(saverMode&&(prev||FindWindow("TandyMaze",NULL)||FindWindow("TandyMazeSaver",NULL)))return 8;
 testing=cmd[0]=='/'&&(cmd[1]=='T'||cmd[1]=='t'||cmd[1]=='C'||cmd[1]=='c'||cmd[1]=='Q'||cmd[1]=='q');capture=cmd[0]=='/'&&(cmd[1]=='C'||cmd[1]=='c');qaMode=cmd[0]=='/'&&(cmd[1]=='Q'||cmd[1]=='q');forceGDI=cmd[0]=='/'&&(cmd[1]=='G'||cmd[1]=='g');if(cmd[0]=='/'&&(cmd[1]=='F'||cmd[1]=='f')){testing=1;forceGDI=1;}
 if(cmd[0]=='/'&&(cmd[1]=='A'||cmd[1]=='a')){testing=qaMode=1;}
 if(cmd[0]=='/'&&(cmd[1]=='B'||cmd[1]=='b')){testing=capture=1;}
 if(cmd[0]=='/'&&(cmd[1]=='I'||cmd[1]=='i')){testing=1;qaMode=2;}
 GetModuleFileName(inst,logpath,sizeof(logpath));n=lstrlen(logpath);for(i=n-1;i>=0&&logpath[i]!='\\'&&logpath[i]!=':';i--);logpath[i+1]=0;lstrcat(logpath,"MAZE.LOG");
 if(testing){f=_lcreat(logpath,0);if(f!=HFILE_ERROR)_lclose(f);}
 fast=detect();if(forceGDI)fast=0;
 if(screenH!=200||(screenW!=160&&screenW!=320&&screenW!=640)){MessageBox(NULL,"Needs a 160, 320 or 640 by 200 display.","Maze",MB_OK);return 1;}
 if(qaMode&&!fast&&!saverMode){logtext("QA requires verified native fast path\r\n");return 2;}
 if(!prev){wc.style=0;wc.lpfnWndProc=SaverProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="TandyMazeSaver";
 wc.lpszClassName="TandyMazeSaver";if(!RegisterClass(&wc))return 4;
 wc.lpfnWndProc=QaProc;wc.lpszClassName="MazeQA";if(!RegisterClass(&wc))return 4;}
 if(qaMode){snapshot=GlobalAlloc(GMEM_MOVEABLE,32768UL);if(!snapshot)return 5;snap=(unsigned char FAR *)GlobalLock(snapshot);if(!snap){GlobalFree(snapshot);return 5;}ShowCursor(FALSE);qa=CreateWindow("MazeQA","Maze QA",WS_POPUP,0,0,screenW,screenH,NULL,NULL,inst,NULL);if(!qa){ShowCursor(TRUE);GlobalUnlock(snapshot);GlobalFree(snapshot);return 6;}ShowWindow(qa,SW_SHOW);UpdateWindow(qa);PostMessage(qa,WM_USER+1,0,0L);}
 else if(!startSaver())return 7;
 while(GetMessage(&msg,NULL,0,0)){if(!saverMode)TranslateMessage(&msg);DispatchMessage(&msg);}if(testing)logtext("QUIT clean\r\n");return msg.wParam;}
