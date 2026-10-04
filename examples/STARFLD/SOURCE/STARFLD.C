/* STARFLD: flying-through-space saver, Windows 3.0 real mode / 8086. */
#define WINVER 0x0300
#include <windows.h>
/* Integer projection; one star per cooperative 55 ms message. */
#define MAXSTARS 64
static int columns,stripe,clearRow,starCount=32,speed=2;
static unsigned long ticks,frames;
static unsigned rng=27183;
typedef struct {int x,y,z,oldx,oldy,size;} STAR;
static STAR stars[MAXSTARS];
static unsigned random16(void){rng=(unsigned)(rng*25173U+13849U);return rng;}
static void seedStar(STAR *p,int first){p->x=(int)(random16()%255U)-127;p->y=(int)(random16()%255U)-127;if(!p->x&&!p->y)p->x=1;p->z=first?64+(int)(random16()%192U):255;p->oldx=-1;p->oldy=-1;p->size=1;}
static void resetRain(int cols){int n;columns=cols;stripe=clearRow=0;ticks=frames=0;for(n=0;n<starCount;n++)seedStar(stars+n,1);}
static void stepRain(void){ticks++;}
static unsigned rowOffset(int y,int banks){return (unsigned)((y&(banks-1))*8192U+(y/banks)*(banks==4?160:80));}
static int validating,validationLost,hashCase,hashInjected;
static HINSTANCE instance;
static HWND saver,qa,overlay;
static HWND previousActive,previousFocus;
static int saverMode,draining,returnFocus,mouseHeld,mouseGesture;
static BYTE initialKeys[256],downKeys[256];
static DWORD armStarted,lastInput;
static char wakeReason[40];
static HCURSOR previousCursor,blankCursor;
static int cursorQA;
static HCURSOR peekCursor(void){HCURSOR c=SetCursor(NULL);SetCursor(c);return c;}
static void restoreOwnedCursor(void){HCURSOR c=SetCursor(NULL);SetCursor(c==blankCursor?previousCursor:c);}
static unsigned char cursorAnd[128],cursorXor[128];
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

static unsigned offsets[200];


static int dirtyCount,qaDrainStage;
static void logtext(char *s){HFILE f=_lopen(logpath,OF_WRITE);if(f==HFILE_ERROR)f=_lcreat(logpath,0);if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);}}
static void dump(char *name){logtext("CAPTURE use host screenshot: GDI path\r\n");}
static int detect(void){HDC dc;HMODULE mod;
 screenW=GetSystemMetrics(SM_CXSCREEN);screenH=GetSystemMetrics(SM_CYSCREEN);dc=GetDC(NULL);if(!dc)return 0;colors=GetDeviceCaps(dc,NUMCOLORS);ReleaseDC(NULL,dc);
 mod=GetModuleHandle("DISPLAY");driver[0]=0;if(mod)GetModuleFileName(mod,driver,sizeof(driver));return 1;
}
static int ownsScreen(void){HWND w;RECT r;if(GetActiveWindow()!=saver)return 0;
 if(saverMode&&(GetCapture()!=saver||GetFocus()!=saver))return 0;
 for(w=GetWindow(saver,GW_HWNDPREV);w;w=GetWindow(w,GW_HWNDPREV))if(IsWindowVisible(w)&&!IsIconic(w)){GetWindowRect(w,&r);if(r.right>0&&r.bottom>0&&r.left<screenW&&r.top<screenH)return 0;}
 return 1;}
/* Only Windows GDI patches; never infer framebuffer layout from a filename. */
static void dot(STAR *p,int white){if(p->oldx>=0)PatBlt(screenDC,p->oldx,p->oldy,p->size,p->size,white?WHITENESS:BLACKNESS);}
static int disrupted(void){return 0;}
static void render(int full){int batch,x,y,n;STAR *p;DWORD t=GetTickCount();
 if(!running||!ownsScreen())return;
 if(blankCursor)SetCursor(blankCursor);
 /* Clear at most 16 scanlines per message, never a full-frame busy loop. */
 if(clearRow<200){n=200-clearRow;if(n>16)n=16;PatBlt(screenDC,0,clearRow,screenW,n,BLACKNESS);clearRow+=n;goto done;}
 for(batch=0;batch<1;batch++){
  p=stars+stripe;dot(p,0);p->z-=speed*4;
  if(p->z<24)seedStar(p,0);
  x=screenW/2+(int)((long)p->x*(screenW/2)/p->z);
  y=100+(int)((long)p->y*100L/p->z);
  if(x<0||x>=screenW-1||y<0||y>=199){seedStar(p,0);x=screenW/2+(int)((long)p->x*(screenW/2)/p->z);y=100+(int)((long)p->y*100L/p->z);}
  p->oldx=x;p->oldy=y;p->size=p->z<80?2:1;dot(p,1);totalCells++;
  if(++stripe>=starCount){stripe=0;frames++;}
 }
 done:t=GetTickCount()-t;drawMs+=t;if(t>maxDraw)maxDraw=t;
}
/* Destroying the GDI popup triggers normal background/window repaint. */
static void restore(void){restoreMs=0;}
static void stop(HWND w,char *reason){char b[320];int focusBack=saverMode&&returnFocus&&GetActiveWindow()==w;DWORD elapsed=firstTick?GetTickCount()-firstTick:0UL;if(closing)return;closing=1;running=0;draining=0;lstrcpy(why,reason);KillTimer(w,1);if(saverMode&&GetCapture()==w)ReleaseCapture();restore();
 if(hidden){restoreOwnedCursor();ShowCursor(TRUE);hidden=0;}if(testing){wsprintf(b,"END reason=%s fast=%d width=%d colors=%d bios=%d ticks=%lu columns=%lu frames=%lu elapsed_ms=%lu draw_ms=%lu max_draw_ms=%lu startup_ms=%lu restore_ms=%lu free_warm=%lu free_end=%lu\r\n",(LPSTR)why,fast,screenW,colors,(int)bios,ticks,totalCells,frames,elapsed,drawMs,maxDraw,startup,restoreMs,freeWarm,GetFreeSpace(0));logtext(b);}
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
static int validateTrial(HWND w){return 1;}
static int initDraw(HWND w){screenDC=GetDC(w);return screenDC!=NULL;}
LONG FAR PASCAL SaverProc(HWND w,UINT m,WPARAM wp,LPARAM lp){PAINTSTRUCT ps;int dx,dy,repair;
 if(saverInput(w,m,wp,lp))return 0;
 switch(m){
 case WM_CREATE:return 0;
 case WM_KILLFOCUS:if(running||draining||validating){returnFocus=0;stop(w,"focus-lost");}return 0;
 case WM_ACTIVATE:if(wp==WA_INACTIVE&&(running||draining||validating)){returnFocus=0;stop(w,"deactivated");}else if(wp!=WA_INACTIVE)activated=1;return 0;
 case WM_ACTIVATEAPP:if(!wp&&(running||draining||validating)){returnFocus=0;stop(w,"task-switch");}return 0;
 case WM_CANCELMODE:if(running||draining||validating){returnFocus=0;stop(w,"cancel-mode");}return 0;
 case WM_ERASEBKGND:return 1;
 case WM_SETCURSOR:if(!closing&&GetActiveWindow()==w&&(!saverMode||GetCapture()==w))SetCursor(blankCursor);return 1;
 case WM_PAINT:BeginPaint(w,&ps);EndPaint(w,&ps);if(running)render(1);return 0;
 case WM_TIMER:
  if(wp!=1)return 0;
  if(draining){drainTick(w);return 0;}
  if(!running)return 0;
  if(!ownsScreen()){stop(w,"ownership-lost");return 0;}
  if(!firstTick){firstTick=GetTickCount();freeWarm=GetFreeSpace(0);}
  repair=!ticks||disrupted();stepRain();render(repair);
  if(qaMode&&recovering){recovering=0;stop(w,"repaint-disruption");return 0;}
  if(qaMode&&++testFrames==(cursorQA?2:48)){PostMessage(qa,WM_USER+2,0,0);return 0;}
  if(capture&&ticks==40)dump("STARFLD.RAW");
  if(testing&&!qaMode&&ticks==60){stop(w,"benchmark");return 0;}return 0;
 case WM_KEYDOWN:case WM_SYSKEYDOWN:case WM_CHAR:if(running){stop(w,"keyboard");return 0;}break;
 case WM_LBUTTONDOWN:case WM_RBUTTONDOWN:case WM_MBUTTONDOWN:if(running){stop(w,"mouse-button");return 0;}break;
 case WM_MOUSEMOVE:if(running){dx=(int)LOWORD(lp)-origin.x;dy=(int)HIWORD(lp)-origin.y;if(dx>2||dx<-2||dy>2||dy<-2)stop(w,"mouse-move");}return 0;
 case WM_QUERYENDSESSION:returnFocus=0;stop(w,"shutdown");return 1;
 case WM_ENDSESSION:if(wp||saverMode){returnFocus=0;stop(w,wp?"shutdown":"shutdown-cancelled");}return 0;
 case WM_CLOSE:returnFocus=0;stop(w,"close");return 0;
 case WM_DESTROY:
  running=draining=0;KillTimer(w,1);if(saverMode&&GetCapture()==w)ReleaseCapture();if(hidden){restoreOwnedCursor();ShowCursor(TRUE);hidden=0;}if(backDC){if(bitmap){SelectObject(backDC,oldBitmap);DeleteObject(bitmap);}DeleteDC(backDC);}backDC=NULL;bitmap=NULL;
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
 resetRain(screenW/8);
 saver=CreateWindow(saverMode?"TandyStarfieldSaver":"TandyStarfield","Starfield",WS_POPUP,0,0,screenW,screenH,NULL,NULL,instance,NULL);if(!saver)return 0;
 if(saverMode&&(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=previousActive)){stop(saver,"startup-owner-changed");return 0;}
 ShowWindow(saver,SW_SHOW);SetActiveWindow(saver);if(saverMode){if(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=saver){stop(saver,"startup-owner-changed");return 0;}SetFocus(saver);SetCapture(saver);if(GetCapture()!=saver||GetActiveWindow()!=saver){stop(saver,"activation-failed");return 0;}}UpdateWindow(saver);if(!saverMode)GetCursorPos(&origin);ScreenToClient(saver,&origin);
 ShowCursor(FALSE);hidden=1;if(!blankCursor){for(n=0;n<128;n++){cursorAnd[n]=255;cursorXor[n]=0;}blankCursor=CreateCursor(instance,0,0,32,32,cursorAnd,cursorXor);}if(blankCursor)SetCursor(blankCursor);else SetCursor(NULL);
 if(!validateTrial(saver)){
  if(draining&&!closing){if(!SetTimer(saver,1,55,NULL)){stop(saver,"validation-timer-failed");return 0;}return 1;}
  if(!closing){returnFocus=!validationLost;stop(saver,validationLost?"validation-ownership-lost":"driver-validation-failed");}return 0;
 }
 if(closing||!IsWindow(saver))return 0;
 if(draining){if(!SetTimer(saver,1,55,NULL)){stop(saver,"validation-timer-failed");return 0;}return 1;}
 if(!ownsScreen()){returnFocus=0;stop(saver,"validation-owner-lost");return 0;}
 if(!initDraw(saver)){stop(saver,"allocation-failed");return 0;}
 if(!draining){running=1;render(1);}startup=GetTickCount()-started;
 if(!SetTimer(saver,1,55,NULL)){stop(saver,"timer-failed");return 0;}
 if(testing){wsprintf(b,"SETTINGS speed=%d stars=%d\r\n",speed,starCount);logtext(b);wsprintf(b,"START driver=%s fast=%d width=%d colors=%d bios=%d\r\n",(LPSTR)driver,fast,screenW,colors,(int)bios);logtext(b);}return 1;}
static unsigned compareScreen(int save){int y,x,n=0;HDC dc;COLORREF color;DWORD FAR *samples;unsigned bad=0;if(!snap)return 65535U;
 samples=(DWORD FAR *)snap;dc=GetDC(qa);if(!dc)return 65535U;for(y=0;y<200;y+=8)for(x=0;x<screenW;x+=8){color=GetPixel(dc,x,y);if(save)samples[n]=color;else if(samples[n]!=color)bad++;n++;}ReleaseDC(qa,dc);return bad;}
LONG FAR PASCAL QaProc(HWND w,UINT m,WPARAM wp,LPARAM lp){HDC dc;PAINTSTRUCT ps;RECT r;char b[160];unsigned bad;
 switch(m){
 case WM_ERASEBKGND:return 1;
 case WM_SETCURSOR:SetCursor(blankCursor);return 1;
 case WM_PAINT:dc=BeginPaint(w,&ps);GetClientRect(w,&r);FillRect(dc,&r,GetStockObject(WHITE_BRUSH));SetBkMode(dc,TRANSPARENT);TextOut(dc,4,4,"DESKTOP RESTORED",16);MoveTo(dc,0,80);LineTo(dc,screenW,160);EndPaint(w,&ps);return 0;
 case WM_USER+1:UpdateWindow(w);compareScreen(1);if(!startSaver()){if(qaMode==3&&hashInjected)return 0;logtext("QA start failed\r\n");DestroyWindow(w);}return 0;
 case WM_USER+4:
  if(hashCase==0){SendMessage(saver,WM_KEYDOWN,VK_RETURN,0L);SendMessage(saver,WM_KEYUP,VK_RETURN,0L);}
  else if(hashCase==1){SendMessage(saver,WM_LBUTTONDOWN,MK_LBUTTON,0L);SetTimer(w,7,440,NULL);}
  else if(hashCase==2)SetActiveWindow(w);
  else if(hashCase==3)SetCapture(w);
  else if(hashCase==4||hashCase==8)SendMessage(saver,WM_CLOSE,0,0L);
  else if(hashCase==5)SendMessage(saver,WM_QUERYENDSESSION,0,0L);
  else if(hashCase==6)SendMessage(saver,WM_ENDSESSION,TRUE,0L);
  else if(hashCase==7)SendMessage(saver,WM_CANCELMODE,0,0L);
  return 0;
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
  else if(testStep==13&&cursorQA){SetCursor(LoadCursor(NULL,IDC_CROSS));SetActiveWindow(w);}
  else if(testStep==13){SendMessage(saver,WM_MOUSEMOVE,0,MAKELONG(origin.x,origin.y));logtext(draining?"SYNTHETIC FAIL\r\n":"SYNTHETIC PASS\r\n");SendMessage(saver,WM_KEYUP,VK_F1,0L);}
  else if(testStep==14){if(cursorQA)SetCursor(LoadCursor(NULL,IDC_CROSS));SetCapture(w);}
  else if(testStep==15){if(cursorQA)SetCursor(LoadCursor(NULL,IDC_CROSS));SetFocus(w);}
  return 0;
 case WM_TIMER:
  if(wp==7){KillTimer(w,7);logtext(IsWindow(saver)&&draining&&GetCapture()==saver?"HASH HELD PASS\r\n":"HASH HELD FAIL\r\n");SendMessage(saver,WM_LBUTTONUP,0,0L);return 0;}
  if(wp==5){KillTimer(w,5);logtext("INPUT OBSERVATION DONE\r\n");DestroyWindow(w);return 0;}
  if(wp==3){KillTimer(w,3);logtext(IsWindow(saver)&&draining&&GetCapture()==saver?"HELD MOUSE PASS\r\n":"HELD MOUSE FAIL\r\n");
   if(!qaDrainStage++){SendMessage(saver,WM_LBUTTONUP,0,0L);SendMessage(saver,WM_LBUTTONDOWN,MK_LBUTTON,0L);SetTimer(w,3,440,NULL);}
   else SendMessage(saver,WM_LBUTTONUP,0,0L);
  }return 0;
 case WM_USER+3:if(cursorQA){wsprintf(b,"CURSOR step=%d preserved=%d\r\n",testStep,peekCursor()==LoadCursor(NULL,IDC_CROSS));logtext(b);SetCursor(NULL);}if(qaMode==3&&hashCase==3){logtext(GetCapture()==w?"HASH CAPTURE PASS\r\n":"HASH CAPTURE FAIL\r\n");if(GetCapture()==w)ReleaseCapture();}if(saverMode&&testStep==14){logtext(GetCapture()==w?"CAPTURE THEFT PASS\r\n":"CAPTURE THEFT FAIL\r\n");if(GetCapture()==w)ReleaseCapture();}if(overlay){DestroyWindow(overlay);overlay=NULL;}UpdateWindow(w);bad=compareScreen(0);wsprintf(b,"QA step=%d changed_units=%u active_ok=%d raw=%d capture_released=%d\r\n",testStep,bad,GetActiveWindow()==w,fast,GetCapture()==NULL);logtext(b);
  if(qaMode==3){wsprintf(b,"HASH ABORT case=%d raw_columns=%lu\r\n",hashCase,totalCells);logtext(b);logtext("QA DONE\r\n");DestroyWindow(w);return 0;}
  if(qaMode==2){SetTimer(w,5,1500,NULL);return 0;}
  if(++testStep<(saverMode?16:11))PostMessage(w,WM_USER+1,0,0L);else{dump("RESTORE.RAW");logtext("QA DONE\r\n");DestroyWindow(w);}return 0;
 case WM_KEYDOWN:case WM_KEYUP:case WM_SYSKEYDOWN:case WM_SYSKEYUP:case WM_CHAR:case WM_LBUTTONDOWN:case WM_LBUTTONUP:case WM_LBUTTONDBLCLK:logtext("INPUT LEAK\r\n");return 0;
 case WM_DESTROY:if(snap)GlobalUnlock(snapshot);if(snapshot)GlobalFree(snapshot);ShowCursor(TRUE);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;MSG msg;int i,n;HFILE f;char ini[144];
 instance=inst;saverMode=cmd[0]=='/'&&(cmd[1]=='S'||cmd[1]=='s'||cmd[1]=='A'||cmd[1]=='a'||cmd[1]=='B'||cmd[1]=='b'||cmd[1]=='I'||cmd[1]=='i'||cmd[1]=='L'||cmd[1]=='l');
 if(saverMode&&(prev||FindWindow("TandyStarfield",NULL)||FindWindow("TandyStarfieldSaver",NULL)))return 8;
 testing=cmd[0]=='/'&&(cmd[1]=='T'||cmd[1]=='t'||cmd[1]=='C'||cmd[1]=='c'||cmd[1]=='Q'||cmd[1]=='q');capture=cmd[0]=='/'&&(cmd[1]=='C'||cmd[1]=='c');qaMode=cmd[0]=='/'&&(cmd[1]=='Q'||cmd[1]=='q');forceGDI=cmd[0]=='/'&&(cmd[1]=='G'||cmd[1]=='g');if(cmd[0]=='/'&&(cmd[1]=='F'||cmd[1]=='f')){testing=1;forceGDI=1;}
 if(cmd[0]=='/'&&(cmd[1]=='A'||cmd[1]=='a')){testing=qaMode=1;}
 if(cmd[0]=='/'&&(cmd[1]=='B'||cmd[1]=='b')){testing=capture=1;}
 if(cmd[0]=='/'&&(cmd[1]=='I'||cmd[1]=='i')){testing=1;qaMode=2;}
 if(cmd[0]=='/'&&(cmd[1]=='L'||cmd[1]=='l')){testing=1;qaMode=3;hashCase=cmd[2]>='0'&&cmd[2]<='8'?cmd[2]-'0':0;}
 if(cmd[0]=='/'&&(cmd[1]=='O'||cmd[1]=='o')){saverMode=testing=qaMode=cursorQA=1;testStep=13;}
 GetModuleFileName(inst,logpath,sizeof(logpath));n=lstrlen(logpath);for(i=n-1;i>=0&&logpath[i]!='\\'&&logpath[i]!=':';i--);logpath[i+1]=0;lstrcat(logpath,"STARFLD.LOG");
 GetWindowsDirectory(ini,sizeof(ini));lstrcat(ini,"\\TSHELL.INI");
 speed=GetPrivateProfileInt("Starfield","Speed",2,ini);if(speed<1||speed>3)speed=2;
 starCount=GetPrivateProfileInt("Starfield","Stars",32,ini);if(starCount!=16&&starCount!=32&&starCount!=64)starCount=32;
 /* Overrides are whole tokens only; invalid values leave valid INI defaults. */
 for(i=0;cmd[i];i++)if((i==0||cmd[i-1]==' ')&&cmd[i]=='/'&&(cmd[i+1]=='V'||cmd[i+1]=='v'||cmd[i+1]=='N'||cmd[i+1]=='n')){
  int key=cmd[i+1],value=0,j=i+2;while(cmd[j]>='0'&&cmd[j]<='9'){if(value<1000)value=value*10+cmd[j]-'0';j++;}
  if(j>i+2&&(!cmd[j]||cmd[j]==' ')){if((key=='V'||key=='v')&&value>=1&&value<=3)speed=value;if((key=='N'||key=='n')&&(value==16||value==32||value==64))starCount=value;}
 }
 if(testing){f=_lcreat(logpath,0);if(f!=HFILE_ERROR)_lclose(f);}
 if(!detect())return 9;fast=0; /* GDI-only: no raw framebuffer assumption on any driver. */
 if(screenH!=200||screenW<160||screenW>640){MessageBox(NULL,"Needs a 160, 320 or 640 by 200 display.","Starfield",MB_OK);return 1;}
 if(qaMode&&!fast&&!saverMode){logtext("QA requires verified native fast path\r\n");return 2;}
 if(!prev){wc.style=0;wc.lpfnWndProc=SaverProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="TandyStarfieldSaver";
 wc.lpszClassName="TandyStarfieldSaver";if(!RegisterClass(&wc))return 4;
 wc.lpszClassName="TandyStarfield";if(!RegisterClass(&wc))return 4;
 wc.lpfnWndProc=QaProc;wc.lpszClassName="StarQA";if(!RegisterClass(&wc))return 4;}
 if(qaMode){snapshot=GlobalAlloc(GMEM_MOVEABLE,32768UL);if(!snapshot)return 5;snap=(unsigned char FAR *)GlobalLock(snapshot);if(!snap){GlobalFree(snapshot);return 5;}ShowCursor(FALSE);qa=CreateWindow("StarQA","Maze QA",WS_POPUP,0,0,screenW,screenH,NULL,NULL,inst,NULL);if(!qa){ShowCursor(TRUE);GlobalUnlock(snapshot);GlobalFree(snapshot);return 6;}ShowWindow(qa,SW_SHOW);UpdateWindow(qa);PostMessage(qa,WM_USER+1,0,0L);}
 else if(!startSaver())return 7;
 while(GetMessage(&msg,NULL,0,0)){if(!saverMode)TranslateMessage(&msg);DispatchMessage(&msg);}if(blankCursor){restoreOwnedCursor();DestroyCursor(blankCursor);}if(testing)logtext("QUIT clean\r\n");return msg.wParam;}
