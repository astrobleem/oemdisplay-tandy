#include "TDROP.H"
static HINSTANCE inst;
static BOOL dragging,autoTest;
static int received;
static char status[32]="Drag file below";
static char path[128]="C:\\DROP.TXT";
static char one[]="C:\\DROP.TXT\0";
static char list[]="C:\\DROP.TXT\0C:\\SECOND.TXT\0";
static void logline(LPCSTR s) { HFILE f;
#ifdef RECEIVER
 f=_lopen("C:\\DROPRX.LOG",OF_WRITE);
#else
 f=_lopen("C:\\DROPTX.LOG",OF_WRITE);
#endif
 if(f==HFILE_ERROR){
#ifdef RECEIVER
 f=_lcreat("C:\\DROPRX.LOG",0);
#else
 f=_lcreat("C:\\DROPTX.LOG",0);
#endif
 }if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lwrite(f,"\r\n",2);_lclose(f);}}
static void note(HWND w,char *s){lstrcpy(status,s);InvalidateRect(w,NULL,TRUE);logline(s);}
static void cancel(HWND w) {if(dragging){dragging=FALSE;if(GetCapture()==w)ReleaseCapture();note(w,"Cancelled");}}
static BOOL senddrop(HWND target,POINT screen,BOOL two) {
 HGLOBAL h;RECT r;POINT p=screen;BOOL nc;
 if(!target)return FALSE;GetClientRect(target,&r);ScreenToClient(target,&p);nc=!PtInRect(&r,p);
 h=TDPack(two?list:one,two?sizeof(list):sizeof(one),p,nc);
 if(!h)return FALSE;
 if(!TDPost(target,h)){TDDragFinish(h);return FALSE;}return TRUE;
}
static void units(HWND w){HGLOBAL h;POINT p,q;char b[128];LPSTR raw;DWORD before;int i;BOOL good=TRUE;
 p.x=-2;p.y=7;
 h=TDPack(list,sizeof(list),p,FALSE);
 good=good && h && TDValid(h) && TDDragQueryFile(h,0xffff,NULL,0)==2;
 good=good && TDDragQueryFile(h,0,b,sizeof(b))==11 && !lstrcmp(b,"C:\\DROP.TXT");
 good=good && TDDragQueryFile(h,1,b,4)==3 && !lstrcmp(b,"C:\\");
 good=good && TDDragQueryPoint(h,&q) && q.x==-2 && q.y==7;
 good=good && !TDPost(NULL,h);TDDragFinish(h);
 h=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,16L);raw=GlobalLock(h);raw[0]=8;raw[8]='x';GlobalUnlock(h);good=good && !TDValid(h);TDDragFinish(h);
 h=TDPack(list,sizeof(list),p,TRUE);good=good && !TDDragQueryPoint(h,&q);TDDragFinish(h);
 before=GetFreeSpace(0);for(i=0;i<100;i++){h=TDPack(list,sizeof(list),p,FALSE);if(!h){good=FALSE;break;}TDDragFinish(h);}good=good && GetFreeSpace(0)>=before;
 logline(good?"UNIT PASS":"UNIT FAIL");
 logline((GetWinFlags()&WF_PMODE)?"FAIL protected mode":"PASS real mode");
 {LONG old=GetWindowLong(w,GWL_EXSTYLE);SetWindowLong(w,GWL_EXSTYLE,old|0x10L);logline((GetWindowLong(w,GWL_EXSTYLE)&0x10L)?"STYLE bit retained":"STYLE bit rejected");SetWindowLong(w,GWL_EXSTYLE,old);}
 {HMODULE m=GetModuleHandle("SHELL");logline(m?"SHELL present":"SHELL not loaded");if(m){logline(GetProcAddress(m,MAKEINTRESOURCE(9))?"SHELL ordinal9 present":"SHELL ordinal9 absent");logline(GetProcAddress(m,"DragAcceptFiles")?"SHELL name present":"SHELL name absent");}}
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){PAINTSTRUCT ps;HDC dc;POINT p;HWND target;MSG msg;UINT n;char b[128];
 switch(m){case WM_CREATE:
#ifdef RECEIVER
 TDDragAcceptFiles(w,TRUE);lstrcpy(status,"Drop files here");
#endif
 if(autoTest)SetTimer(w,1,500,NULL);return 0;
 case WM_PAINT:dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));TextOut(dc,2,2,status,lstrlen(status));TextOut(dc,2,17,path,lstrlen(path));EndPaint(w,&ps);return 0;
#ifndef RECEIVER
 case WM_LBUTTONDOWN:SetFocus(w);dragging=TRUE;SetCapture(w);note(w,"Drag to receiver");return 0;
 case WM_LBUTTONUP:if(dragging){dragging=FALSE;ReleaseCapture();GetCursorPos(&p);target=TDTarget(p);note(w,senddrop(target,p,(GetKeyState(VK_SHIFT)&0x8000)!=0)?"Posted":"No target");}return 0;
 case WM_MOUSEMOVE:if(dragging && GetCapture()!=w)cancel(w);return 0;
#endif
 case WM_KEYDOWN:if(wp==VK_ESCAPE){cancel(w);return 0;}break;
 case WM_CANCELMODE:cancel(w);return 0;
 case WM_ACTIVATE:if(!wp)cancel(w);break;
 case WM_DROPFILES:
 if(TDValid((HGLOBAL)wp)){n=TDDragQueryFile((HGLOBAL)wp,0xffff,NULL,0);TDDragQueryFile((HGLOBAL)wp,0,path,sizeof(path));logline("RECEIVED");logline(path);if(n==2){TDDragQueryFile((HGLOBAL)wp,1,b,sizeof(b));logline(b);}received+=n;note(w,"Received path(s)");}else logline("Rejected malformed");TDDragFinish((HGLOBAL)wp);return 0;
 case WM_TIMER:KillTimer(w,1);units(w);
#ifndef RECEIVER
 SendMessage(w,WM_LBUTTONDOWN,0,0L);
 SendMessage(w,WM_KEYDOWN,VK_ESCAPE,0L);
 logline(!dragging && GetCapture()!=w?"ESCAPE PASS":"ESCAPE FAIL");
 SendMessage(w,WM_LBUTTONDOWN,0,0L);
 SendMessage(w,WM_CANCELMODE,0,0L);
 logline(!dragging && GetCapture()!=w?"CANCELMODE PASS":"CANCELMODE FAIL");
 {HWND closed;HGLOBAL h;POINT pt;BOOL ok;int i;MSG pending;
  pt.x=0;pt.y=0;closed=CreateWindow("STATIC","",WS_POPUP,0,0,10,10,NULL,NULL,inst,NULL);
  TDDragAcceptFiles(closed,TRUE);DestroyWindow(closed);h=TDPack(list,sizeof(list),pt,FALSE);
  ok=!TDPost(closed,h) && TDValid(h);TDDragFinish(h);logline(ok?"CLOSED TARGET PASS":"CLOSED TARGET FAIL");
  TDDragAcceptFiles(w,TRUE);for(i=0;i<256;i++)if(!PostMessage(w,WM_USER,0,0L))break;
  h=TDPack(list,sizeof(list),pt,FALSE);ok=!TDPost(w,h) && TDValid(h);TDDragFinish(h);
  while(PeekMessage(&pending,w,WM_USER,WM_USER,PM_REMOVE));
  TDDragAcceptFiles(w,FALSE);logline(ok && i<256?"QUEUE FAILURE PASS":"QUEUE FAILURE FAIL");
 }
#endif
#ifdef RECEIVER
 if(autoTest==1){autoTest=2;WinExec("C:\\DROPTX.EXE /A",SW_SHOWNORMAL);SetTimer(w,1,15000,NULL);}else {logline(received==2?"CROSS TASK PASS":"CROSS TASK FAIL");PostMessage(w,WM_CLOSE,0,0L);}
#else
 target=FindWindow("TandyDropRx",NULL);p.x=8;p.y=8;if(target)ClientToScreen(target,&p);logline(senddrop(target,p,TRUE)?"CROSS TASK POST PASS":"CROSS TASK POST FAIL");PostMessage(w,WM_CLOSE,0,0L);
#endif
 return 0;
 case WM_DESTROY:cancel(w);TDDragAcceptFiles(w,FALSE);while(PeekMessage(&msg,w,WM_DROPFILES,WM_DROPFILES,PM_REMOVE))TDDragFinish((HGLOBAL)msg.wParam);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE h,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS c;HWND w;MSG msg;int y;char *cls,*title;
 inst=h;autoTest=cmd && (cmd[0]=='/' || cmd[0]=='-');
#ifdef RECEIVER
 cls="TandyDropRx";title="Drop receiver";y=95;
#else
 cls="TandyDropTx";title="File sender";y=4;
#endif
 if(!prev){c.style=0;c.lpfnWndProc=WndProc;c.cbClsExtra=c.cbWndExtra=0;c.hInstance=h;c.hIcon=NULL;c.hCursor=LoadCursor(NULL,IDC_ARROW);c.hbrBackground=GetStockObject(WHITE_BRUSH);c.lpszMenuName=NULL;c.lpszClassName=cls;if(!RegisterClass(&c))return 1;}
 w=CreateWindow(cls,title,WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU,0,y,158,75,NULL,NULL,h,NULL);if(!w)return 2;ShowWindow(w,show);UpdateWindow(w);
#ifdef RECEIVER
 if(!autoTest)WinExec("C:\\DROPTX.EXE",SW_SHOWNORMAL);
#endif
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
#ifdef RECEIVER
 if(autoTest)ExitWindows(0L,0);
#endif
 return msg.wParam;}
