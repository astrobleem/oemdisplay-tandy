/* TSHELL: optional 8086 Windows 3.0 launcher. Optional global idle observation in TSINPUT.DLL. */
#define WINVER 0x0300
#include <windows.h>
#include <dos.h>
#include <direct.h>
#include "PROGMENU.H"
#include "TSBOOT.H"
#include "TNOTICE.H"
#include "TSAUX.H"
#include "TSSAVER.H"
#include "TSDATE.H"
#define START 1
#define FIRSTAPP 20
#define EXITWIN 40
#define CLOSEAPP 41
#define RUNAPP 42
#define PROGRAMS 43
#define EXITSILENT 44
#define ABOUTSYS 45
#define ADJUSTTIME 46
#define MYCOMPUTER 47
#define STARTBOOT (WM_USER+3)
#define RUNEDIT 100
#define RUNMAX 126
#define BROWSE 101
#define FILELIST 102
#define FILTER 103
#define PATHBOX 104
static char runStatus[17],chosen[144],browseOld[144];
static int browseDrive,browseFilter;
static char FAR *browseDirs;
static char *masks[]={"*.EXE","*.COM","*.BAT"};
static HINSTANCE instance;
static HWND start;
static int primaryShell, shellMode, width, barHeight=22, minute=-1;
static char clockText[6]="--:--";
static char *names[]={"&Program Mgr"};
static char *files[]={"PROGMAN.EXE"};
static char paths[1][144];
static void findapps(void) {
 OFSTRUCT of;int i;char path[144];
 for(i=0;i<1;i++){
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
 if(i<0||i>=1)return;
 if(!paths[i][0])findapps();
 if(!paths[i][0]){TinyNotice(w,instance,"Start","App not found.");return;}
 result=WinExec(paths[i],SW_SHOWNORMAL);
 if(result>=32&&i==0){manager=FindWindow("Progman",NULL);if(manager){ShowWindow(manager,SW_RESTORE);BringWindowToTop(manager);}}
 if(result<32){wsprintf(message,"Launch failed.\nError %u.",result);TinyNotice(w,instance,"Start",message);}
}
/* Win3.0 string popup sizing, verified against native menu rectangles.
   SYSTEM_FONT supplies the text height; SM_CYMENU is only the menu-bar
   metric. Count the menu actually built, including a failed System popup.
   Keep native menu drawing/tracking and the Win3.0 flags=0 contract. */
static int popupheight(HWND w,HMENU menu) {
 HDC dc;HFONT old;TEXTMETRIC tm;int row,border,height,count,i;WORD flags;
 border=GetSystemMetrics(SM_CYBORDER);if(border<1)border=1;
 row=GetSystemMetrics(SM_CYMENU);
 dc=GetDC(w);
 if(dc){
  old=(HFONT)SelectObject(dc,GetStockObject(SYSTEM_FONT));
  if(GetTextMetrics(dc,&tm))row=tm.tmHeight+border;
  SelectObject(dc,old);ReleaseDC(w,dc);
 }
 height=3*border;count=GetMenuItemCount(menu);
 for(i=0;i<count;i++){
  flags=GetMenuState(menu,i,MF_BYPOSITION);
  /* A submenu's item count occupies the high byte of GetMenuState. */
  if(!(flags&MF_POPUP)&&(flags&MF_SEPARATOR))
   height+=GetSystemMetrics(SM_CYMENU)/2;
  else height+=row;
 }
 return height;
}
static void popup(HWND w) {
 HMENU menu,system;RECT r;int y;
 SetActiveWindow(w);SetFocus(w);findapps();menu=CreatePopupMenu();if(!menu)return;
 AppendMenu(menu,MF_STRING,MYCOMPUTER,"&My Computer");
 AppendMenu(menu,MF_STRING,PROGRAMS,"&Programs...");
 AppendMenu(menu,MF_STRING,RUNAPP,"&Run...");
 system=CreatePopupMenu();
 if(system){AppendMenu(system,MF_STRING,ABOUTSYS,"&About This Tandy");AppendMenu(menu,MF_POPUP,(UINT)system,"&System");}
 AppendMenu(menu,MF_STRING|(paths[0][0]?0:MF_GRAYED),FIRSTAPP,names[0]);
 AppendMenu(menu,MF_SEPARATOR,0,NULL);
 if(!shellMode)AppendMenu(menu,MF_STRING,CLOSEAPP,"&Close bar");
 AppendMenu(menu,MF_STRING,EXITWIN,"E&xit Windows...");
 AppendMenu(menu,MF_STRING,EXITSILENT,"Exit &silently...");
 GetWindowRect(w,&r);y=r.top-popupheight(w,menu);if(y<0)y=0;
 TSSaverHold(1);TrackPopupMenu(menu,TPM_LEFTBUTTON,0,y,0,w,NULL);DestroyMenu(menu);TSSaverHold(0);
}
static void clockpopup(HWND w) {
 HMENU menu;RECT r;int x,y;
 SetActiveWindow(w);SetFocus(w);
 menu=CreatePopupMenu();if(!menu)return;
 AppendMenu(menu,MF_STRING,ADJUSTTIME,"&Adjust date/time...");
 GetWindowRect(w,&r);y=r.top-GetSystemMetrics(SM_CYMENU)-4;if(y<0)y=0;
 TSSaverHold(1);
 /* Windows 3.0 requires flags=0; right-button/alignment flags are 3.1. */
 x=width-160;if(x<0)x=0;
 TrackPopupMenu(menu,0,x,y,0,w,NULL);
 DestroyMenu(menu);TSSaverHold(0);
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
static int smallDialog(HWND w,char *title,int height,FARPROC fn) {
 HGLOBAL h;BYTE FAR *p;FARPROC proc;DWORD units=GetDialogBaseUnits();int result=IDCANCEL;
 h=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,64);if(!h)return IDCANCEL;p=(BYTE FAR *)GlobalLock(h);if(!p){GlobalFree(h);return IDCANCEL;}
 dword(&p,WS_POPUP|WS_CAPTION|WS_SYSMENU|DS_MODALFRAME);*p++=0;
 word(&p,0);word(&p,0);word(&p,128*4/LOWORD(units));word(&p,height*8/HIWORD(units));*p++=0;*p++=0;
 while(*title)*p++=*title++;*p++=0;GlobalUnlock(h);
 proc=MakeProcInstance(fn,instance);if(proc){result=DialogBoxIndirect(instance,h,w,(DLGPROC)proc);FreeProcInstance(proc);}GlobalFree(h);return result;
}
static void sizeDialog(HWND w,int height) {
 RECT r,c;int ww,hh;GetWindowRect(w,&r);GetClientRect(w,&c);ww=128+r.right-r.left-c.right;hh=height+r.bottom-r.top-c.bottom;
 SetWindowPos(w,NULL,(GetSystemMetrics(SM_CXSCREEN)-ww)/2,(GetSystemMetrics(SM_CYSCREEN)-hh)/2,ww,hh,SWP_NOZORDER);
}
static int listfiles(HWND w,char *where) {
 char pattern[144],cwd[144],display[15];int n,drive;
 /* Preserve every visited drive's DOS directory, including drive-relative paths. */
 if(where[0]&&where[1]==':'){
  drive=where[0];if(drive>='a'&&drive<='z')drive-=32;drive-='A'-1;
  if(drive<1||drive>26)return 0;
  if(!browseDirs[(drive-1)*144]){
   if(!_getdcwd(drive,cwd,sizeof(cwd))){SetDlgItemText(w,PATHBOX,"Cannot read");return 0;}
   lstrcpy(browseDirs+(drive-1)*144,cwd);
  }
 }
 lstrcpy(pattern,where);n=lstrlen(pattern);
 if(n&&pattern[n-1]!='\\'&&pattern[n-1]!=':')lstrcat(pattern,"\\");
 lstrcat(pattern,masks[browseFilter]);
 if(!DlgDirList(w,pattern,FILELIST,0,DDL_DIRECTORY|DDL_DRIVES|DDL_READONLY|DDL_ARCHIVE)){SetDlgItemText(w,PATHBOX,"Cannot list");return 0;}
 if(getcwd(cwd,sizeof(cwd))){
  n=lstrlen(cwd);if(n>14){lstrcpy(display,"...");lstrcat(display,cwd+n-11);SetDlgItemText(w,PATHBOX,display);}else SetDlgItemText(w,PATHBOX,cwd);
 }
 SendDlgItemMessage(w,FILELIST,LB_SETCURSEL,0,0L);return 1;
}
BOOL FAR PASCAL BrowseProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HWND child;int i,n;char item[144],cwd[144];
 if(m==WM_INITDIALOG){
  sizeDialog(w,148);
  CreateWindow("STATIC","",WS_CHILD|WS_VISIBLE|WS_BORDER|SS_LEFT,6,4,116,16,w,(HMENU)PATHBOX,instance,NULL);
  CreateWindow("COMBOBOX","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|CBS_DROPDOWNLIST|WS_VSCROLL,6,23,116,64,w,(HMENU)FILTER,instance,NULL);
  CreateWindow("LISTBOX","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|WS_BORDER|WS_VSCROLL|LBS_NOTIFY,6,45,116,72,w,(HMENU)FILELIST,instance,NULL);
  CreateWindow("BUTTON","&Open",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_DEFPUSHBUTTON,6,124,54,20,w,(HMENU)IDOK,instance,NULL);
  CreateWindow("BUTTON","&Cancel",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,68,124,54,20,w,(HMENU)IDCANCEL,instance,NULL);
  for(i=0;i<5;i++){child=GetDlgItem(w,i==0?PATHBOX:i==1?FILTER:i==2?FILELIST:i==3?IDOK:IDCANCEL);if(!child){EndDialog(w,IDCANCEL);return TRUE;}SendMessage(child,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);}
  for(i=0;i<3;i++)SendDlgItemMessage(w,FILTER,CB_ADDSTRING,0,(LPARAM)(LPSTR)masks[i]);
  SendDlgItemMessage(w,FILTER,CB_SETCURSEL,browseFilter,0L);
  if(!listfiles(w,"")){EndDialog(w,IDCANCEL);return TRUE;}
  SetFocus(GetDlgItem(w,FILELIST));return FALSE;
 }
 if(m==WM_COMMAND&&wp==FILTER&&HIWORD(lp)==CBN_SELCHANGE){browseFilter=(int)SendDlgItemMessage(w,FILTER,CB_GETCURSEL,0,0L);listfiles(w,"");return TRUE;}
 if(m==WM_COMMAND&&(wp==IDOK||(wp==FILELIST&&HIWORD(lp)==LBN_DBLCLK))){
  if(SendDlgItemMessage(w,FILELIST,LB_GETCURSEL,0,0L)==LB_ERR)return TRUE;
  if(DlgDirSelect(w,item,FILELIST)){listfiles(w,item);SetFocus(GetDlgItem(w,FILELIST));return TRUE;}
  if(!getcwd(cwd,sizeof(cwd)))return TRUE;n=lstrlen(cwd);
  if(n+lstrlen(item)+2>sizeof(chosen))return TRUE;
  lstrcpy(chosen,cwd);if(n&&cwd[n-1]!='\\')lstrcat(chosen,"\\");lstrcat(chosen,item);EndDialog(w,IDOK);return TRUE;
 }
 if((m==WM_COMMAND&&wp==IDCANCEL)||m==WM_CLOSE){EndDialog(w,IDCANCEL);return TRUE;}
 return FALSE;
}
static int browse(HWND w) {
 int result,i,restored=1;unsigned drive;HGLOBAL h;char cwd[144];chosen[0]=0;browseFilter=0;
 if(!getcwd(browseOld,sizeof(browseOld)))return -1;
 _dos_getdrive(&drive);browseDrive=(int)drive;
 h=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,26*144);if(!h)return -1;
 browseDirs=(char FAR *)GlobalLock(h);if(!browseDirs){GlobalFree(h);return -1;}
 lstrcpy(browseDirs+(browseDrive-1)*144,browseOld);
 result=smallDialog(w,"Browse",148,(FARPROC)BrowseProc);
 for(i=0;i<26;i++)if(browseDirs[i*144]){lstrcpy(cwd,browseDirs+i*144);if(chdir(cwd))restored=0;}
 if(_chdrive(browseDrive)||chdir(browseOld))restored=0;
 GlobalUnlock(h);GlobalFree(h);browseDirs=NULL;
 if(!restored)return -2;
 return result==IDOK;
}
static void runstatus(HWND w,char *s) {
 RECT r;lstrcpy(runStatus,s);r.left=0;r.top=66;r.right=128;r.bottom=84;
 InvalidateRect(w,&r,TRUE);SetFocus(GetDlgItem(w,RUNEDIT));
}
BOOL FAR PASCAL RunProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 RECT r,c;HDC dc;PAINTSTRUCT ps;HWND edit;int ww,hh,n,i;UINT result;char cmd[128],error[17];
 if(m==WM_INITDIALOG){
  runStatus[0]=0;GetWindowRect(w,&r);GetClientRect(w,&c);
  ww=128+r.right-r.left-c.right;hh=114+r.bottom-r.top-c.bottom;
  SetWindowPos(w,NULL,(GetSystemMetrics(SM_CXSCREEN)-ww)/2,(GetSystemMetrics(SM_CYSCREEN)-hh)/2,ww,hh,SWP_NOZORDER);
  edit=CreateWindow("EDIT","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|WS_BORDER|ES_AUTOHSCROLL,6,20,116,18,w,(HMENU)RUNEDIT,instance,NULL);
  CreateWindow("BUTTON","&Run",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_DEFPUSHBUTTON,6,88,54,20,w,(HMENU)IDOK,instance,NULL);
  CreateWindow("BUTTON","&Cancel",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,68,88,54,20,w,(HMENU)IDCANCEL,instance,NULL);
  CreateWindow("BUTTON","&Browse",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,6,43,70,20,w,(HMENU)BROWSE,instance,NULL);
  SendDlgItemMessage(w,BROWSE,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  if(!edit||!GetDlgItem(w,IDOK)||!GetDlgItem(w,IDCANCEL)||!GetDlgItem(w,BROWSE)){EndDialog(w,IDCANCEL);return TRUE;}
  SendMessage(edit,EM_LIMITTEXT,RUNMAX+1,0L);
  SendMessage(edit,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  SendDlgItemMessage(w,IDOK,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  SendDlgItemMessage(w,IDCANCEL,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  SetFocus(edit);return FALSE;
 }
 if(m==WM_PAINT){dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));SetBkMode(dc,TRANSPARENT);
  TextOut(dc,4,5,"Command:126 max",15);TextOut(dc,4,67,runStatus,lstrlen(runStatus));EndPaint(w,&ps);return TRUE;}
 if(m==WM_COMMAND&&wp==BROWSE){
  edit=GetDlgItem(w,RUNEDIT);n=GetWindowTextLength(edit);if(n>RUNMAX){runstatus(w,"Max 126 chars");return TRUE;}
  GetWindowText(edit,cmd,sizeof(cmd));
  n=browse(w);if(n<0){runstatus(w,n==-2?"Restore failed":"Browse failed");return TRUE;}
  if(n){
   i=0;while(cmd[i]==' '||cmd[i]=='\t')i++;
   if(cmd[i]=='"'){i++;while(cmd[i]&&cmd[i]!='"')i++;if(cmd[i])i++;}
   else while(cmd[i]&&cmd[i]!=' '&&cmd[i]!='\t')i++;
   if(lstrlen(chosen)+lstrlen(cmd+i)>RUNMAX){runstatus(w,"Max 126 chars");return TRUE;}
   lstrcat(chosen,cmd+i);SetWindowText(edit,chosen);runstatus(w,"");
  }
  SetFocus(edit);return TRUE;
 }
 if(m==WM_COMMAND&&wp==IDOK){
  edit=GetDlgItem(w,RUNEDIT);n=GetWindowTextLength(edit);
  if(n>RUNMAX){runstatus(w,"Max 126 chars");return TRUE;}
  GetWindowText(edit,cmd,sizeof(cmd));i=0;while(cmd[i]==' '||cmd[i]=='\t')i++;
  if(!cmd[i]){runstatus(w,"Enter a command");return TRUE;}
  result=WinExec(cmd,SW_SHOWNORMAL);
  if(result<32){wsprintf(error,"Launch error %u",result);runstatus(w,error);return TRUE;}
  EndDialog(w,IDOK);return TRUE;
 }
 if((m==WM_COMMAND&&wp==IDCANCEL)||m==WM_CLOSE){EndDialog(w,IDCANCEL);return TRUE;}
 return FALSE;
}
static void runcommand(HWND w) {
 smallDialog(w,"Run",114,(FARPROC)RunProc);
}
static void exitwindows(HWND w,int silent) {
 TSSaverHold(1);if(confirmexit(w))TandyExit(w,silent);TSSaverHold(0);
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
 case WM_TIMECHANGE:minute=-1;clockread(w);return 0;
 case WM_TIMER:if(wp==BOOT_TIMER)TandyBootTick(w);else if(wp==1)clockread(w);else if(wp==SAVER_TIMER)TSSaverTick(w);return 0;
 case STARTBOOT:if(primaryShell){TandyBootBegin(w);TSSaverBegin(w,instance);}return 0;
 case WM_LBUTTONDBLCLK:
  if((int)LOWORD(lp)>=width-45&&(int)LOWORD(lp)<width&&(int)HIWORD(lp)>=0&&(int)HIWORD(lp)<barHeight){TSSaverHold(1);TandyClock(w,instance);TSSaverHold(0);}
  return 0;
 case WM_RBUTTONUP:
  if((int)LOWORD(lp)>=width-45&&(int)LOWORD(lp)<width&&(int)HIWORD(lp)>=0&&(int)HIWORD(lp)<barHeight)clockpopup(w);
  return 0;
 case WM_SETFOCUS:return 0;
 case WM_COMMAND:
  if(wp==START){popup(w);return 0;}
  if(wp>=FIRSTAPP&&wp<FIRSTAPP+1){launch(w,wp-FIRSTAPP);return 0;}
  if(wp==RUNAPP){TSSaverHold(1);runcommand(w);TSSaverHold(0);return 0;}
  if(wp==PROGRAMS){TSSaverHold(1);PmPrograms(w,instance);TSSaverHold(0);return 0;}
  if(wp==MYCOMPUTER){TSSaverHold(1);TandyFileManager(w,instance);TSSaverHold(0);return 0;}
  if(wp==ADJUSTTIME){TSSaverHold(1);TandyDateTime(w,instance);TSSaverHold(0);return 0;}
  if(wp==ABOUTSYS){TSSaverHold(1);TandySystem(w,instance);TSSaverHold(0);return 0;}
  if(wp==EXITWIN){exitwindows(w,0);return 0;}
  if(wp==EXITSILENT){exitwindows(w,1);return 0;}
  if(wp==CLOSEAPP&&!shellMode){DestroyWindow(w);return 0;}break;
 case WM_CLOSE:if(shellMode)exitwindows(w,0);else DestroyWindow(w);return 0;
 case WM_QUERYENDSESSION:TSSaverShutdown(1);return TRUE;
 case WM_ENDSESSION:TSSaverShutdown(wp!=0);if(wp){TandyBootStop(w);DestroyWindow(w);}return 0;
 case WM_DESTROY:TSSaverStop(w);TandyBootStop(w);KillTimer(w,1);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;char ini[144],configured[80];
 instance=inst;shellMode=(cmd[0]=='/'&&(cmd[1]=='S'||cmd[1]=='s'));
 GetWindowsDirectory(ini,sizeof(ini));lstrcat(ini,"\\SYSTEM.INI");
 GetPrivateProfileString("boot","shell","",configured,sizeof(configured),ini);
 if(!lstrcmpi(configured,"TSHELL.EXE")){shellMode=1;primaryShell=1;}
 width=GetSystemMetrics(SM_CXSCREEN);
 if(prev)return 0;
 wc.style=CS_DBLCLKS;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;
 wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_BTNFACE+1);wc.lpszMenuName=NULL;wc.lpszClassName="TandyStart";
 if(!RegisterClass(&wc))return 1;
 w=CreateWindow("TandyStart","Tandy Start",WS_POPUP|WS_VISIBLE,0,GetSystemMetrics(SM_CYSCREEN)-barHeight,width,barHeight,NULL,NULL,inst,NULL);
 if(!w)return 1;ShowWindow(w,SW_SHOWNORMAL);UpdateWindow(w);
 if(primaryShell)PostMessage(w,STARTBOOT,0,0L);
 while(GetMessage(&msg,NULL,0,0)){
  if(((msg.message==WM_KEYDOWN||msg.message==WM_SYSKEYDOWN)&&msg.wParam==VK_F10)||(msg.message==WM_KEYDOWN&&msg.wParam==VK_SPACE)){popup(w);continue;}
  if(msg.message==WM_SYSKEYDOWN&&msg.wParam=='S'){popup(w);continue;}
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
 return msg.wParam;
}
