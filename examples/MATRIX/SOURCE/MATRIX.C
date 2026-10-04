/* MATRIX: original digital-rain graphics, Windows 3.0 / 8086.
   No mode switch, driver patch, hook, password, or background installation. */
#define WINVER 0x0300
#ifndef MATRIX_HOST
#include <windows.h>
#endif
#define MAXCOL 80
#define ROWS 25
#define MAXCELL (MAXCOL*ROWS)
static unsigned char glyph[MAXCELL],level[MAXCELL];
static int head[MAXCOL],length[MAXCOL],period[MAXCOL],countdown[MAXCOL];
static unsigned short rng=391;
static int columns;
static unsigned long ticks,changed;
static const unsigned char font[32][8]={
 {56,68,76,84,100,68,56,0},{16,48,16,16,16,16,56,0},
 {56,68,4,8,16,32,124,0},{120,4,4,56,4,4,120,0},
 {8,24,40,72,124,8,8,0},{124,64,64,120,4,4,120,0},
 {56,64,64,120,68,68,56,0},{124,4,8,16,32,32,32,0},
 {56,68,68,56,68,68,56,0},{56,68,68,60,4,4,56,0},
 {56,68,68,124,68,68,68,0},{120,68,68,120,68,68,120,0},
 {60,64,64,64,64,64,60,0},{120,68,68,68,68,68,120,0},
 {124,64,64,120,64,64,124,0},{124,64,64,120,64,64,64,0},
 {16,16,124,16,16,0,16,0},{0,40,124,40,124,40,0,0},
 {0,8,16,32,16,8,0,0},{0,32,16,8,16,32,0,0},
 {60,32,32,32,32,32,60,0},{120,8,8,8,8,8,120,0},
 {0,68,40,16,40,68,0,0},{16,56,84,16,84,56,16,0},
 {124,16,16,84,84,16,16,0},{16,124,20,20,20,36,68,0},
 {68,68,124,4,4,4,56,0},{16,124,16,56,84,16,16,0},
 {124,4,4,124,64,64,124,0},{32,124,36,36,36,36,68,0},
 {84,84,124,16,16,16,16,0},{124,16,56,84,16,16,16,0}};
static unsigned random16(void){rng=(unsigned short)((unsigned long)rng*25173UL+13849UL);return (unsigned)rng;}
static void dirty(int col,int row);
static void cell(int c,int r,int shade,int fresh){int n;if(r<0||r>=ROWS)return;n=r*columns+c;
 if(fresh)glyph[n]=(unsigned char)(random16()>>11);
 if((int)level[n]!=shade||fresh){level[n]=(unsigned char)shade;dirty(c,r);changed++;}}
static void resetRain(int cols){int c,r,n,d;columns=cols;rng=391;ticks=changed=0;
 for(n=0;n<MAXCELL;n++){glyph[n]=0;level[n]=0;}
 for(c=0;c<columns;c++){head[c]=(int)(random16()%ROWS);length[c]=6+(random16()%10);period[c]=1+(random16()%3);countdown[c]=period[c];
  for(r=0;r<ROWS;r++){n=r*columns+c;d=head[c]-r;glyph[n]=(unsigned char)(random16()>>11);if(d>=0&&d<length[c])level[n]=(unsigned char)(d==0?3:d<length[c]/2?2:1);}}}
static void stepRain(void){int c,h,len;ticks++;
 for(c=0;c<columns;c++)if(--countdown[c]<=0){countdown[c]=period[c];h=++head[c];len=length[c];
  if(h>ROWS+len+3){head[c]=0;h=0;length[c]=6+(random16()%10);len=length[c];period[c]=1+(random16()%3);}
  cell(c,h-len,0,0);cell(c,h-len/2,1,0);cell(c,h-1,2,0);cell(c,h,3,1);}}
/* Validated fixed layouts. Kind 0=16-color packed, 1=CGA packed 2bpp,
   2=Tandy 640 pair-of-plane-bytes, 3=CGA monochrome. */
static unsigned rowOffset(int y,int banks){return (unsigned)((y&(banks-1))*8192U+(y/banks)*(banks==4?160:80));}
static void packedRow(unsigned char *out,unsigned bits,int shade,int kind,int row){
 int x,per,color;unsigned b;
 if(kind==0)color=shade==3?15:shade==2?10:shade==1?2:0;
 else if(kind==1)color=shade==3?3:shade?1:0;
 else if(kind==2)color=shade==3?3:shade?2:0;
 else color=shade?1:0;
 if(kind!=0&&shade==1)bits&=(row&1)?0xAA:0x55;
 if(kind==3&&shade==2)bits&=(row&1)?0xFF:0xDD;
 if(kind==2){out[0]=(unsigned char)((color&1)?bits:0);out[1]=(unsigned char)((color&2)?bits:0);return;}
 per=kind==0?2:kind==1?4:8;
 for(x=0;x<8;x+=per){int j;b=0;for(j=0;j<per;j++)b=(b<<(8/per))|((bits&(128U>>(x+j)))?color:0);out[x/per]=(unsigned char)b;}}
#ifndef MATRIX_HOST
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
static void dirty(int c,int r){int n=r*columns+c;if(!dirtyFlag[n]){dirtyFlag[n]=1;if(dirtyCount<MAXCOL*4){dirtyCol[dirtyCount]=(unsigned char)c;dirtyRow[dirtyCount++]=(unsigned char)r;}}}
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
static void renderCell(int c,int r){int y,n=r*columns+c,s=level[n];unsigned bits,off;unsigned char *p;int j;char ch;
 if(fast){for(y=0;y<8;y++){bits=font[glyph[n]][y];if(kind!=0&&s==1)bits&=(y&1)?0xAA:0x55;if(kind==3&&s==2)bits&=(y&1)?0xFF:0xDD;
 p=packed[s][bits];off=offsets[r*8+y]+c*bytesPerCell;for(j=0;j<bytesPerCell;j++)vram[off+j]=p[j];}}
 else{SetTextColor(backDC,s==3?RGB(255,255,255):s==2?RGB(0,255,0):s==1?RGB(0,128,0):RGB(0,0,0));ch=(char)(s?"0123456789ABCDEF+#<>[]X*TYSLZKUV!?"[glyph[n]]:' ');TextOut(backDC,c*8,r*8,&ch,1);}}
static int ownsScreen(void){HWND w;RECT r;if(GetActiveWindow()!=saver)return 0;
 if(saverMode&&GetCapture()!=saver)return 0;
 if(fast&&(*((unsigned char FAR *)0x00400049L)!=bios||*((unsigned char FAR *)0x00400062L)!=0))return 0;
 for(w=GetWindow(saver,GW_HWNDPREV);w;w=GetWindow(w,GW_HWNDPREV))if(IsWindowVisible(w)&&!IsIconic(w)){GetWindowRect(w,&r);if(r.right>0&&r.bottom>0&&r.left<screenW&&r.top<screenH)return 0;}
 return 1;}
static int disrupted(void){int r,c,n,y,j,seen=0;unsigned bits,off;unsigned char *p;
 if(!fast)return 0;
 for(r=0;r<ROWS;r++)for(c=0;c<columns;c++){n=r*columns+c;if(!level[n])continue;
  for(y=0;y<8;y++){bits=font[glyph[n]][y];if(kind!=0&&level[n]==1)bits&=(y&1)?0xAA:0x55;if(kind==3&&level[n]==2)bits&=(y&1)?0xFF:0xDD;
   p=packed[level[n]][bits];off=offsets[r*8+y]+c*bytesPerCell;for(j=0;j<bytesPerCell;j++)if(vram[off+j]!=p[j])return 1;}
  if(++seen==16)return 0;
 }return 0;}
static void render(int full){int c,r,i;DWORD t=GetTickCount();
 if(!running||!ownsScreen())return;
 if(full){for(r=0;r<ROWS;r++)for(c=0;c<columns;c++){renderCell(c,r);dirtyFlag[r*columns+c]=0;totalCells++;}}
 else for(i=0;i<dirtyCount;i++){c=dirtyCol[i];r=dirtyRow[i];renderCell(c,r);dirtyFlag[r*columns+c]=0;totalCells++;}
 dirtyCount=0;
 if(!fast)BitBlt(screenDC,0,0,columns*8,200,backDC,0,0,SRCCOPY);
 t=GetTickCount()-t;drawMs+=t;if(t>maxDraw)maxDraw=t;}
static void restore(void){DWORD t;if(!screenDC)return;t=GetTickCount();
 /* Self-copy forces the known driver's canonical shadow back to VRAM.
    Never restore a stale saved bitmap over another application's output. */
 if(fast&&*((unsigned char FAR *)0x00400049L)==bios&&*((unsigned char FAR *)0x00400062L)==0)BitBlt(screenDC,0,0,1,1,screenDC,0,0,SRCCOPY);
 restoreMs=GetTickCount()-t;}
static void stop(HWND w,char *reason){char b[280];int focusBack=saverMode&&returnFocus&&GetActiveWindow()==w;DWORD elapsed=firstTick?GetTickCount()-firstTick:0UL;if(closing)return;closing=1;running=0;draining=0;lstrcpy(why,reason);KillTimer(w,1);if(saverMode&&GetCapture()==w)ReleaseCapture();restore();
 if(hidden){SetCursor(previousCursor);ShowCursor(TRUE);hidden=0;}if(testing){wsprintf(b,"END reason=%s fast=%d width=%d colors=%d bios=%d ticks=%lu cells=%lu elapsed_ms=%lu draw_ms=%lu max_draw_ms=%lu startup_ms=%lu restore_ms=%lu free_warm=%lu free_end=%lu\r\n",(LPSTR)why,fast,screenW,colors,(int)bios,ticks,totalCells,elapsed,drawMs,maxDraw,startup,restoreMs,freeWarm,GetFreeSpace(0));logtext(b);}
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
 if(GetActiveWindow()!=w||GetCapture()!=w){returnFocus=0;stop(w,"drain-ownership-lost");return;}
 if(keysHeld()||mouseHeld){lastInput=GetTickCount();return;}
 /* Hardware input wins over this low-priority timer. Remove any remaining
    own-window input without generating WM_CHAR or forwarding it elsewhere. */
 while(PeekMessage(&msg,w,WM_KEYFIRST,WM_KEYLAST,PM_REMOVE))saverInput(w,msg.message,msg.wParam,msg.lParam);
 while(PeekMessage(&msg,w,WM_MOUSEFIRST,WM_MOUSELAST,PM_REMOVE))saverInput(w,msg.message,msg.wParam,msg.lParam);
 if(keysHeld()||mouseHeld||GetTickCount()-lastInput<quiet)return;
 if(testing)logtext("DRAIN released\r\n");stop(w,wakeReason);
}
static int initDraw(HWND w){int y,s,b;screenDC=GetDC(w);if(!screenDC)return 0;bytesPerCell=kind==0?4:kind==3?1:2;
 if(fast){for(y=0;y<200;y++)offsets[y]=rowOffset(y,banks);for(s=0;s<4;s++)for(b=0;b<256;b++)packedRow(packed[s][b],b,s,kind,-1);/* no fade here; applied at cell row */
  /* packedRow's dither path is bypassed by building equivalent solid levels. */
  for(s=1;s<3;s++)if(kind!=0)for(b=0;b<256;b++){
   if(kind==1){int x,j;unsigned v;for(x=0;x<2;x++){v=0;for(j=0;j<4;j++)v=(v<<2)|((b&(128>>(x*4+j)))?1:0);packed[s][b][x]=(unsigned char)v;}}
   else if(kind==2){packed[s][b][0]=0;packed[s][b][1]=(unsigned char)b;}
   else packed[s][b][0]=(unsigned char)b;
  }
 }else{backDC=CreateCompatibleDC(screenDC);if(!backDC)return 0;bitmap=CreateCompatibleBitmap(screenDC,columns*8,200);if(!bitmap)return 0;oldBitmap=SelectObject(backDC,bitmap);SelectObject(backDC,GetStockObject(SYSTEM_FIXED_FONT));SetBkColor(backDC,RGB(0,0,0));PatBlt(backDC,0,0,columns*8,200,BLACKNESS);}
 return 1;}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){PAINTSTRUCT ps;int dx,dy,repair;
 if(saverInput(w,m,wp,lp))return 0;
 switch(m){
 case WM_CREATE:return 0;
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
  if(qaMode&&recovering){logtext(disrupted()?"QA repair=FAIL\r\n":"QA repair=PASS\r\n");recovering=0;stop(w,"repaint-recovery");return 0;}
  if(qaMode&&++testFrames==4){PostMessage(qa,WM_USER+2,0,0);return 0;}
  if(capture&&ticks==40)dump("MATRIX.RAW");
  if(testing&&!qaMode&&ticks==60){stop(w,"benchmark");return 0;}return 0;
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
 saver=CreateWindow(saverMode?"TandyMatrixSaver":"TandyMatrix","Matrix",WS_POPUP,0,0,screenW,screenH,NULL,NULL,instance,NULL);if(!saver)return 0;
 if(saverMode&&(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=previousActive)){stop(saver,"startup-owner-changed");return 0;}
 ShowWindow(saver,SW_SHOW);SetActiveWindow(saver);if(saverMode){if(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=saver){stop(saver,"startup-owner-changed");return 0;}SetFocus(saver);SetCapture(saver);if(GetCapture()!=saver||GetActiveWindow()!=saver){stop(saver,"activation-failed");return 0;}}UpdateWindow(saver);if(!saverMode)GetCursorPos(&origin);ScreenToClient(saver,&origin);
 if(!initDraw(saver)){stop(saver,"allocation-failed");return 0;}
 ShowCursor(FALSE);hidden=1;SetCursor(NULL);if(!draining){running=1;render(1);}startup=GetTickCount()-started;
 if(!SetTimer(saver,1,110,NULL)){stop(saver,"timer-failed");return 0;}
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
  return 0;
 case WM_TIMER:
  if(wp==3){KillTimer(w,3);logtext(IsWindow(saver)&&draining&&GetCapture()==saver?"HELD MOUSE PASS\r\n":"HELD MOUSE FAIL\r\n");
   if(!qaDrainStage++){SendMessage(saver,WM_LBUTTONUP,0,0L);SendMessage(saver,WM_LBUTTONDOWN,MK_LBUTTON,0L);SetTimer(w,3,440,NULL);}
   else SendMessage(saver,WM_LBUTTONUP,0,0L);
  }return 0;
 case WM_USER+3:if(saverMode&&testStep==14){logtext(GetCapture()==w?"CAPTURE THEFT PASS\r\n":"CAPTURE THEFT FAIL\r\n");if(GetCapture()==w)ReleaseCapture();}if(overlay){DestroyWindow(overlay);overlay=NULL;}UpdateWindow(w);bad=compareScreen(0);wsprintf(b,"QA step=%d changed_units=%u active_ok=%d raw=%d capture_released=%d\r\n",testStep,bad,GetActiveWindow()==w,fast,GetCapture()==NULL);logtext(b);
  if(++testStep<(saverMode?15:11))PostMessage(w,WM_USER+1,0,0L);else{dump("RESTORE.RAW");logtext("QA DONE\r\n");DestroyWindow(w);}return 0;
 case WM_DESTROY:if(snap)GlobalUnlock(snapshot);if(snapshot)GlobalFree(snapshot);ShowCursor(TRUE);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;MSG msg;int i,n;HFILE f;
 instance=inst;saverMode=cmd[0]=='/'&&(cmd[1]=='S'||cmd[1]=='s'||cmd[1]=='A'||cmd[1]=='a');
 if(saverMode&&(prev||FindWindow("TandyMatrix",NULL)||FindWindow("TandyMatrixSaver",NULL)))return 8;
 testing=cmd[0]=='/'&&(cmd[1]=='T'||cmd[1]=='t'||cmd[1]=='C'||cmd[1]=='c'||cmd[1]=='Q'||cmd[1]=='q');capture=cmd[0]=='/'&&(cmd[1]=='C'||cmd[1]=='c');qaMode=cmd[0]=='/'&&(cmd[1]=='Q'||cmd[1]=='q');forceGDI=cmd[0]=='/'&&(cmd[1]=='G'||cmd[1]=='g');if(cmd[0]=='/'&&(cmd[1]=='F'||cmd[1]=='f')){testing=1;forceGDI=1;}
 if(cmd[0]=='/'&&(cmd[1]=='A'||cmd[1]=='a')){testing=qaMode=1;}
 GetModuleFileName(inst,logpath,sizeof(logpath));n=lstrlen(logpath);for(i=n-1;i>=0&&logpath[i]!='\\'&&logpath[i]!=':';i--);logpath[i+1]=0;lstrcat(logpath,"MATRIX.LOG");
 if(testing){f=_lcreat(logpath,0);if(f!=HFILE_ERROR)_lclose(f);}
 fast=detect();if(forceGDI)fast=0;
 if(screenH!=200||screenW<160||screenW>640){MessageBox(NULL,"Needs a 160, 320 or 640 by 200 display.","Matrix",MB_OK);return 1;}
 if(qaMode&&!fast&&!saverMode){logtext("QA requires verified native fast path\r\n");return 2;}
 if(!prev){wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="TandyMatrix";if(!RegisterClass(&wc))return 3;
 wc.lpszClassName="TandyMatrixSaver";if(!RegisterClass(&wc))return 4;
 wc.lpfnWndProc=QaProc;wc.lpszClassName="MatrixQA";if(!RegisterClass(&wc))return 4;}
 if(qaMode){snapshot=GlobalAlloc(GMEM_MOVEABLE,32768UL);if(!snapshot)return 5;snap=(unsigned char FAR *)GlobalLock(snapshot);if(!snap){GlobalFree(snapshot);return 5;}ShowCursor(FALSE);qa=CreateWindow("MatrixQA","Matrix QA",WS_POPUP,0,0,screenW,screenH,NULL,NULL,inst,NULL);if(!qa){ShowCursor(TRUE);GlobalUnlock(snapshot);GlobalFree(snapshot);return 6;}ShowWindow(qa,SW_SHOW);UpdateWindow(qa);PostMessage(qa,WM_USER+1,0,0L);}
 else if(!startSaver())return 7;
 while(GetMessage(&msg,NULL,0,0)){if(!saverMode)TranslateMessage(&msg);DispatchMessage(&msg);}if(testing)logtext("QUIT clean\r\n");return msg.wParam;}
#endif
