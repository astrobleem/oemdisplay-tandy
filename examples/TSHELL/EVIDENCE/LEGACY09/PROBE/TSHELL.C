/* TSHELL: optional 8086 Windows 3.0 launcher. No desktop hooks. */
#define WINVER 0x0300
#include <windows.h>
#include <dos.h>
#define START 1
#define FIRSTAPP 20
#define EXITWIN 40
#define CLOSEAPP 41
static DWORD freeBefore;
static HFILE logFile;
static int probeStep;
static char firstClock[6];
static void value(char *name,DWORD v) { char line[90];wsprintf(line,"%s=%lu\r\n",(LPSTR)name,v);_lwrite(logFile,line,lstrlen(line));_lclose(logFile);logFile=_lopen("C:\\SHELLQA.LOG",OF_WRITE);_llseek(logFile,0L,2); }
void FAR PASCAL ProbeTimer(HWND,UINT,UINT,DWORD);
static HINSTANCE instance;
static HWND start;
static int shellMode, width, barHeight=22, minute=-1;
static char clockText[6]="--:--";
static char *names[]={"&Program Mgr","&Notepad","&Paintbrush","&Cookie","&About Tandy","&Slosh","&Mouth"};
static char *files[]={"PROGMAN.EXE","NOTEPAD.EXE","PBRUSH.EXE","COOKIE.EXE","TABOUT.EXE","SLOSH.EXE","MOUTH.EXE"};
static char paths[7][144];
static void findapps(void) {
 OFSTRUCT of;int i;char path[144];
 for(i=0;i<7;i++){
  paths[i][0]=0;
  /* OpenFile performs the Windows search, and returns its resolved path. */
  if(OpenFile(files[i],&of,OF_EXIST)!=HFILE_ERROR)lstrcpy(paths[i],of.szPathName);
  else {GetWindowsDirectory(path,sizeof(path));lstrcat(path,"\\");lstrcat(path,files[i]);if(OpenFile(path,&of,OF_EXIST)!=HFILE_ERROR)lstrcpy(paths[i],of.szPathName);}
 }
}
static void clockread(HWND w) {
 struct dostime_t now;RECT r;int v;
 _dos_gettime(&now);v=now.hour*60+now.minute;
 if(v==minute)return;minute=v;
 clockText[0]=(char)('0'+now.hour/10);clockText[1]=(char)('0'+now.hour%10);
 clockText[2]=':';clockText[3]=(char)('0'+now.minute/10);clockText[4]=(char)('0'+now.minute%10);
 r.left=width-45;r.top=0;r.right=width;r.bottom=barHeight;InvalidateRect(w,&r,TRUE);
}
static void launch(HWND w,int i) {
 UINT result;HWND manager;char message[80];
 if(i<0||i>=7)return;
 if(!paths[i][0]){MessageBox(w,"App not found.","Start",MB_OK|MB_ICONEXCLAMATION);return;}
 result=WinExec(paths[i],SW_SHOWNORMAL);
 if(result>=32&&i==0){manager=FindWindow("Progman",NULL);if(manager){ShowWindow(manager,SW_RESTORE);BringWindowToTop(manager);}}
 if(result<32){wsprintf(message,"Launch failed.\nError %u.",result);MessageBox(w,message,"Start",MB_OK|MB_ICONEXCLAMATION);}
}
static void popup(HWND w) {
 HMENU menu;RECT r;int i,y,h;
 SetActiveWindow(w);SetFocus(w);findapps();menu=CreatePopupMenu();if(!menu)return;
 for(i=0;i<7;i++)AppendMenu(menu,MF_STRING|(paths[i][0]?0:MF_GRAYED),FIRSTAPP+i,names[i]);
 AppendMenu(menu,MF_SEPARATOR,0,NULL);
 if(!shellMode)AppendMenu(menu,MF_STRING,CLOSEAPP,"&Close bar");
 AppendMenu(menu,MF_STRING,EXITWIN,"E&xit Windows");
 GetWindowRect(w,&r);
 /* Estimate native popup height and clamp to the physical screen. */
 h=GetSystemMetrics(SM_CYMENU);y=r.top-h*(shellMode?8:9)-h/2-4;if(y<0)y=0;
 TrackPopupMenu(menu,TPM_LEFTBUTTON,0,y,0,w,NULL);
 DestroyMenu(menu);
}
static void word(BYTE FAR **p,unsigned v){*(*p)++=(BYTE)v;*(*p)++=(BYTE)(v>>8);}
static void dword(BYTE FAR **p,DWORD v){word(p,(unsigned)v);word(p,(unsigned)(v>>16));}
BOOL FAR PASCAL ExitProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HDC dc;PAINTSTRUCT ps;RECT r,c;int ww,hh;
 if(m==WM_INITDIALOG){
  GetWindowRect(w,&r);GetClientRect(w,&c);ww=128+r.right-r.left-c.right;hh=58+r.bottom-r.top-c.bottom;
  SetWindowPos(w,NULL,(GetSystemMetrics(SM_CXSCREEN)-ww)/2,(GetSystemMetrics(SM_CYSCREEN)-hh)/2,ww,hh,SWP_NOZORDER);
  MoveWindow(GetDlgItem(w,IDOK),6,32,54,20,TRUE);MoveWindow(GetDlgItem(w,IDCANCEL),68,32,54,20,TRUE);
  SendMessage(GetDlgItem(w,IDOK),WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  SendMessage(GetDlgItem(w,IDCANCEL),WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  SetFocus(GetDlgItem(w,IDCANCEL));return FALSE;
 }
 if(m==WM_PAINT){dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));SetBkMode(dc,TRANSPARENT);TextOut(dc,8,8,"Exit Windows?",13);EndPaint(w,&ps);return TRUE;}
 if(m==WM_COMMAND&&(wp==IDOK||wp==IDCANCEL)){EndDialog(w,wp);return TRUE;}
 if(m==WM_CLOSE){EndDialog(w,IDCANCEL);return TRUE;}return FALSE;
}
static int confirmexit(HWND w) {
 HGLOBAL h;BYTE FAR *p;FARPROC proc;DWORD units=GetDialogBaseUnits();int bx=LOWORD(units),by=HIWORD(units),i,result;char *s;
 h=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,256);if(!h)return 0;p=(BYTE FAR *)GlobalLock(h);if(!p){GlobalFree(h);return 0;}
 dword(&p,WS_POPUP|WS_CAPTION|WS_SYSMENU|DS_MODALFRAME);*p++=2;
 word(&p,0);word(&p,0);word(&p,128*4/bx);word(&p,58*8/by);*p++=0;*p++=0;s="Exit";while(*s)*p++=*s++;*p++=0;
 for(i=0;i<2;i++){
  word(&p,(i?68:6)*4/bx);word(&p,32*8/by);word(&p,54*4/bx);word(&p,20*8/by);word(&p,i?IDCANCEL:IDOK);
  dword(&p,WS_CHILD|WS_VISIBLE|WS_TABSTOP|(i?BS_DEFPUSHBUTTON:BS_PUSHBUTTON));*p++=0x80;
  s=i?"&Cancel":"E&xit";while(*s)*p++=*s++;*p++=0;*p++=0;
 }
 GlobalUnlock(h);proc=MakeProcInstance((FARPROC)ExitProc,instance);if(!proc){GlobalFree(h);return 0;}
 result=DialogBoxIndirect(instance,h,w,(DLGPROC)proc);FreeProcInstance(proc);GlobalFree(h);return result==IDOK;
}
static void exitwindows(HWND w) {
 if(confirmexit(w))if(!ExitWindows(0L,0))MessageBox(w,"Exit canceled.","Start",MB_OK);
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HDC dc;PAINTSTRUCT ps;RECT r;
 switch(m){
 case WM_CREATE:
  start=CreateWindow("BUTTON","&Start",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,2,2,58,18,w,(HMENU)START,instance,NULL);
  if(!start)return -1L;
  SendMessage(start,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  clockread(w);
  if(!SetTimer(w,1,10000,NULL))lstrcpy(clockText,"NoClk");
  return 0;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);GetClientRect(w,&r);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
  SetBkMode(dc,TRANSPARENT);SetTextColor(dc,GetSysColor(COLOR_WINDOWTEXT));
  MoveTo(dc,0,0);LineTo(dc,width,0);TextOut(dc,width-43,7,clockText,5);EndPaint(w,&ps);return 0;
 case WM_TIMER:clockread(w);return 0;
 case WM_SETFOCUS:return 0;
 case WM_COMMAND:
  if(wp==START){popup(w);return 0;}
  if(wp>=FIRSTAPP&&wp<FIRSTAPP+7){launch(w,wp-FIRSTAPP);return 0;}
  if(wp==EXITWIN){exitwindows(w);return 0;}
  if(wp==CLOSEAPP&&!shellMode){DestroyWindow(w);return 0;}break;
 case WM_CLOSE:if(shellMode)exitwindows(w);else DestroyWindow(w);return 0;
 case WM_QUERYENDSESSION:return TRUE;
 case WM_ENDSESSION:if(wp)DestroyWindow(w);return 0;
 case WM_DESTROY:KillTimer(w,1);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;char ini[144],configured[80];
 freeBefore=GetFreeSpace(0);instance=inst;shellMode=(cmd[0]=='/'&&(cmd[1]=='S'||cmd[1]=='s'));
 GetWindowsDirectory(ini,sizeof(ini));lstrcat(ini,"\\SYSTEM.INI");
 GetPrivateProfileString("boot","shell","",configured,sizeof(configured),ini);
 if(!lstrcmpi(configured,"TSHELL.EXE"))shellMode=1;
 width=GetSystemMetrics(SM_CXSCREEN);
 if(prev)return 0;
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;
 wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_BTNFACE+1);wc.lpszMenuName=NULL;wc.lpszClassName="TandyStart";
 if(!RegisterClass(&wc))return 1;
 w=CreateWindow("TandyStart","Tandy Start",WS_POPUP|WS_VISIBLE,0,GetSystemMetrics(SM_CYSCREEN)-barHeight,width,barHeight,NULL,NULL,inst,NULL);
 if(!w)return 1;ShowWindow(w,SW_SHOWNORMAL);UpdateWindow(w);
 logFile=_lcreat("C:\\SHELLQA.LOG",0);
 value("FLAGS",GetWinFlags());value("WIDTH",width);value("SHELL",shellMode);value("FREE_BEFORE",freeBefore);value("FREE_AFTER",GetFreeSpace(0));
 lstrcpy(firstClock,clockText);_lwrite(logFile,clockText,5);_lwrite(logFile,"\r\n",2);
 SetTimer(w,2,1000,(TIMERPROC)MakeProcInstance((FARPROC)ProbeTimer,inst));
 while(GetMessage(&msg,NULL,0,0)){
  if(((msg.message==WM_KEYDOWN||msg.message==WM_SYSKEYDOWN)&&msg.wParam==VK_F10)||(msg.message==WM_KEYDOWN&&msg.wParam==VK_SPACE)){popup(w);continue;}
  if(msg.message==WM_SYSKEYDOWN&&msg.wParam=='S'){popup(w);continue;}
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
 return msg.wParam;
}

void FAR PASCAL ProbeTimer(HWND w,UINT m,UINT id,DWORD tick) {
 RECT r,b;HDC dc;TEXTMETRIC tm;int i;struct dostime_t now;
 probeStep++;
 if(probeStep==1){
  GetWindowRect(w,&r);GetWindowRect(start,&b);
  value("BAR_BOTTOM",r.bottom);value("BAR_HEIGHT",r.bottom-r.top);value("START_RIGHT",b.right);
  dc=GetDC(w);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));GetTextMetrics(dc,&tm);ReleaseDC(w,dc);
  value("CLOCK_WIDTH",5*tm.tmAveCharWidth);value("FONT_HEIGHT",tm.tmHeight);
  findapps();for(i=0;i<7;i++)value(files[i],paths[i][0]!=0);
  value("QUERYENDSESSION",SendMessage(w,WM_QUERYENDSESSION,0,0L));
 }
 if(probeStep>=10 && lstrcmp(firstClock,clockText)!=0){
  _dos_gettime(&now);clockread(w);
  value("CLOCK_CURRENT",minute==now.hour*60+now.minute);value("CLOCK_CHANGED",lstrcmp(firstClock,clockText)!=0);
  _lwrite(logFile,clockText,5);_lwrite(logFile,"\r\nCOMPLETE=1\r\n",14);_lclose(logFile);KillTimer(w,2);ExitWindows(0L,0);
 }
}
