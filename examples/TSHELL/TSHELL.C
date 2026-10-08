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
#include "TSNAMES.H"
#include "TSHOLD.H"
#define START 1
#define FIRSTAPP 20
#define EXITWIN 40
#define CLOSEAPP 41
#define RUNAPP 42
#define PROGRAMS 43
#define ABOUTSYS 45
#define ADJUSTTIME 46
#define MYCOMPUTER 47
#define SAVERSETUP 48
#define SYSTEMMENU 49
#define STARTBOOT (WM_USER+3)
#define OPENSYSTEM (WM_USER+4)
#define RUNEDIT 100
#define RUNMAX 126
#define BROWSE 101
#define FILELIST 102
#define FILTER 103
#define PATHBOX 104
#define NATIVELIST 105
#define SHORTBOX 106
#define NAMES_TIMER 19
#define BROWSEHEIGHT 166
static char runStatus[17],chosen[144],browseOld[144],browseListed[144];
static int browseDrive,browseFilter,browseBusy,browseValid;
static int browseDrawDepth;
static HWND browseDrawList;
static char FAR *browseDirs;
static char *masks[]={"*.EXE","*.COM","*.BAT"};
static HINSTANCE instance;
static HWND start;
static int primaryShell, shellMode, width, barHeight=22, minute=-1;
static int systemQueued;
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
 TSSaverHold(1);BringWindowToTop(w);SetActiveWindow(w);SetFocus(w);findapps();menu=CreatePopupMenu();
 if(!menu){TandyHoldMenuDone(1);TSSaverHold(0);return;}
 AppendMenu(menu,MF_STRING,MYCOMPUTER,"&My Computer");
 AppendMenu(menu,MF_STRING,PROGRAMS,"&Programs...");
 AppendMenu(menu,MF_STRING,RUNAPP,"&Run...");
 /* At 160 pixels USER overlaps a cascading child on its parent; a mouse
    click can close both without choosing anything. Open this level as a
    separate popup after the Start menu has finished tracking. */
 if(width<320)AppendMenu(menu,MF_STRING,SYSTEMMENU,"&System...");
 else {
  system=CreatePopupMenu();
  if(system){AppendMenu(system,MF_STRING,ABOUTSYS,"&About This Tandy");AppendMenu(system,MF_STRING,SAVERSETUP,"Screen &saver...");AppendMenu(menu,MF_POPUP,(UINT)system,"&System");}
 }
 AppendMenu(menu,MF_STRING|(paths[0][0]?0:MF_GRAYED),FIRSTAPP,names[0]);
 AppendMenu(menu,MF_SEPARATOR,0,NULL);
 if(!shellMode)AppendMenu(menu,MF_STRING,CLOSEAPP,"&Close bar");
 AppendMenu(menu,MF_STRING,EXITWIN,"E&xit Windows...");
 GetWindowRect(w,&r);y=r.top-popupheight(w,menu);if(y<0)y=0;
 TrackPopupMenu(menu,TPM_LEFTBUTTON,0,y,0,w,NULL);DestroyMenu(menu);TandyHoldMenuDone(!systemQueued);TSSaverHold(0);
}
static void systempopup(HWND w) {
 HMENU menu;RECT r;int y;
 TSSaverHold(1);menu=CreatePopupMenu();if(!menu){TandyHoldMenuDone(1);TSSaverHold(0);return;}
 AppendMenu(menu,MF_STRING,ABOUTSYS,"&About This Tandy");
 AppendMenu(menu,MF_STRING,SAVERSETUP,"Screen &saver...");
 GetWindowRect(w,&r);y=r.top-popupheight(w,menu);if(y<0)y=0;
 SetActiveWindow(w);SetFocus(w);
 TrackPopupMenu(menu,0,0,y,0,w,NULL);
 DestroyMenu(menu);TandyHoldMenuDone(1);TSSaverHold(0);
}
static void clockpopup(HWND w) {
 HMENU menu;RECT r;int x,y;
 TSSaverHold(1);SetActiveWindow(w);SetFocus(w);
 menu=CreatePopupMenu();if(!menu){TSSaverHold(0);return;}
 AppendMenu(menu,MF_STRING,ADJUSTTIME,"&Adjust date/time...");
 GetWindowRect(w,&r);y=r.top-GetSystemMetrics(SM_CYMENU)-4;if(y<0)y=0;
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
  SendMessage(w,DM_SETDEFID,IDCANCEL,0L);
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
  s=i?"&Cancel":"&Exit";while(*s)*p++=*s++;*p++=0;*p++=0;
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
/* Native DlgDirList rows remain authoritative. The visible list never sorts,
   and display text is never passed to DOS, DlgDirSelect, or WinExec. */
/* Only synchronous list mutations are batched. Painting is restored before
   returning to Windows, including every error path and each async scan turn. */
static void browsepaint(HWND w,int hold) {
 HWND list;
 if(hold){
  if(!browseDrawDepth++){
   browseDrawList=GetDlgItem(w,FILELIST);
   if(browseDrawList)SendMessage(browseDrawList,WM_SETREDRAW,FALSE,0L);
  }
 }else if(browseDrawDepth && !--browseDrawDepth){
  list=browseDrawList;browseDrawList=NULL;
  if(list && IsWindow(list) && GetDlgItem(w,FILELIST)==list){
   SendMessage(list,WM_SETREDRAW,TRUE,0L);
   InvalidateRect(list,NULL,TRUE);
  }
 }
}
static int browsealiases(HWND w) {
 char item[144];int i,n;HWND native,visible;
 native=GetDlgItem(w,NATIVELIST);visible=GetDlgItem(w,FILELIST);
 SendMessage(visible,LB_RESETCONTENT,0,0L);
 n=(int)SendMessage(native,LB_GETCOUNT,0,0L);
 if(n==LB_ERR)return 0;
 for(i=0;i<n;i++){
  if(SendMessage(native,LB_GETTEXTLEN,i,0L)>=sizeof(item))return 0;
  if(SendMessage(native,LB_GETTEXT,i,(LPARAM)(LPSTR)item)==LB_ERR)return 0;
  if((int)SendMessage(visible,LB_ADDSTRING,0,(LPARAM)(LPSTR)item)<0)return 0;
 }
 return 1;
}
static void browseselect(HWND w) {
 char item[144];int i;
 item[0]=0;i=(int)SendDlgItemMessage(w,FILELIST,LB_GETCURSEL,0,0L);
 if(i!=LB_ERR){
  SendDlgItemMessage(w,NATIVELIST,LB_SETCURSEL,i,0L);
  if(SendDlgItemMessage(w,NATIVELIST,LB_GETTEXTLEN,i,0L)<sizeof(item))
   SendDlgItemMessage(w,NATIVELIST,LB_GETTEXT,i,(LPARAM)(LPSTR)item);
 }
 SetDlgItemText(w,SHORTBOX,item);
}
static void browseextent(HWND w) {
 char item[TSNAMES_TEXT];int i,n,width=0,extent;HDC dc;HFONT old;HWND list;
 list=GetDlgItem(w,FILELIST);dc=GetDC(list);if(!dc)return;
 old=(HFONT)SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
 n=(int)SendMessage(list,LB_GETCOUNT,0,0L);
 for(i=0;i<n;i++){
  if(SendMessage(list,LB_GETTEXTLEN,i,0L)>=sizeof(item))continue;
  SendMessage(list,LB_GETTEXT,i,(LPARAM)(LPSTR)item);
  extent=(int)LOWORD(GetTextExtent(dc,item,lstrlen(item)))+4;
  if(extent>width)width=extent;
 }
 SelectObject(dc,old);ReleaseDC(list,dc);
 /* Windows 3.0 may hide/reset this bar while rebuilding its rows. */
 SendMessage(list,LB_SETHORIZONTALEXTENT,width,0L);
 ShowScrollBar(list,SB_HORZ,TRUE);
}
static void browsereadywork(HWND w,int failed) {
 int i,n,length;
 KillTimer(w,NAMES_TIMER);TSNamesEnd();browseBusy=0;browseValid=0;
 n=(int)SendDlgItemMessage(w,NATIVELIST,LB_GETCOUNT,0,0L);
 if(n==LB_ERR||n!=(int)SendDlgItemMessage(w,FILELIST,LB_GETCOUNT,0,0L))failed=1;
 for(i=0;!failed&&i<n;i++){
  length=(int)SendDlgItemMessage(w,FILELIST,LB_GETTEXTLEN,i,0L);
  if(length<0||length>=TSNAMES_TEXT)failed=1;
 }
 if(failed&&!browsealiases(w)){
  SendDlgItemMessage(w,FILELIST,LB_RESETCONTENT,0,0L);
  SetDlgItemText(w,SHORTBOX,"");EnableWindow(GetDlgItem(w,FILTER),TRUE);
  EnableWindow(GetDlgItem(w,IDOK),FALSE);
  SetDlgItemText(w,PATHBOX,"Cannot list");return;
 }
 SendDlgItemMessage(w,FILELIST,LB_SETCURSEL,0,0L);
 EnableWindow(GetDlgItem(w,FILELIST),TRUE);
 EnableWindow(GetDlgItem(w,FILTER),TRUE);
 EnableWindow(GetDlgItem(w,IDOK),TRUE);
 SendMessage(w,DM_SETDEFID,IDOK,0L);
 browseValid=1;browseextent(w);browseselect(w);
}
static void browseready(HWND w,int failed) {
 browsepaint(w,1);browsereadywork(w,failed);browsepaint(w,0);
}
static int listfileswork(HWND w,char *where) {
 char pattern[144],cwd[144],display[15];int n,drive,result;
 if(browseBusy)return 0;
 /* Invalidate first: failed DlgDirList may already change native rows/CWD. */
 browseValid=0;browseListed[0]=0;
 EnableWindow(GetDlgItem(w,IDOK),FALSE);
 /* A disabled Open cannot consume Enter while Cancel is focused. */
 SendMessage(w,DM_SETDEFID,IDCANCEL,0L);
 SendDlgItemMessage(w,FILELIST,LB_RESETCONTENT,0,0L);
 SetDlgItemText(w,SHORTBOX,"");
 /* Snapshot the current drive even after an unexpected CWD/drive change.
    A later relative directory selection must not escape Cancel restoration. */
 if(!getcwd(cwd,sizeof(cwd))){SetDlgItemText(w,PATHBOX,"Cannot read");return 0;}
 drive=cwd[0];if(drive>='a'&&drive<='z')drive-=32;drive-='A'-1;
 if(drive<1||drive>26||cwd[1]!=':'){SetDlgItemText(w,PATHBOX,"Cannot read");return 0;}
 if(!browseDirs[(drive-1)*144])lstrcpy(browseDirs+(drive-1)*144,cwd);
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
 if(!DlgDirList(w,pattern,NATIVELIST,0,DDL_DIRECTORY|DDL_DRIVES|DDL_READONLY|DDL_ARCHIVE)){SetDlgItemText(w,PATHBOX,"Cannot list");return 0;}
 if(!browsealiases(w)){SetDlgItemText(w,PATHBOX,"Cannot list");EnableWindow(GetDlgItem(w,IDOK),FALSE);return 0;}
 if(!getcwd(cwd,sizeof(cwd))){SetDlgItemText(w,PATHBOX,"Cannot read");return 0;}
 lstrcpy(browseListed,cwd);
 {
  n=lstrlen(cwd);if(n>14){lstrcpy(display,"...");lstrcat(display,cwd+n-11);SetDlgItemText(w,PATHBOX,display);}else SetDlgItemText(w,PATHBOX,cwd);
 }
 /* Lists above the bounded enrichment budget remain ordinary usable DOS lists. */
 n=(int)SendDlgItemMessage(w,NATIVELIST,LB_GETCOUNT,0,0L);
 result=0;
 if(cwd[0]&&n<=TSNAMES_LIMIT)
  result=TSNamesBegin(cwd,GetDlgItem(w,NATIVELIST),GetDlgItem(w,FILELIST));
 if(result>0){
  SendDlgItemMessage(w,FILELIST,LB_SETCURSEL,0,0L);browseselect(w);browseextent(w);
  browseBusy=1;EnableWindow(GetDlgItem(w,FILELIST),FALSE);
  EnableWindow(GetDlgItem(w,FILTER),FALSE);EnableWindow(GetDlgItem(w,IDOK),FALSE);
  SetFocus(GetDlgItem(w,IDCANCEL));
  if(!SetTimer(w,NAMES_TIMER,55,NULL))browseready(w,1);
 }else browseready(w,result<0);
 return 1;
}
static int listfiles(HWND w,char *where) {
 int result;browsepaint(w,1);result=listfileswork(w,where);browsepaint(w,0);return result;
}
/* A finished raw scan is only a candidate. Re-enumerate through DOS while
   the mapping is invalid; the bridge compares every exact saved row. */
static void browsefinishwork(HWND w,int result) {
 char pattern[144],cwd[144];int n;
 if(result!=TSNAMES_READY){browseready(w,result<0);return;}
 KillTimer(w,NAMES_TIMER);browseValid=0;
 if(!getcwd(cwd,sizeof(cwd))||lstrcmpi(cwd,browseListed)){
  TSNamesEnd();browseBusy=0;listfiles(w,"");return;
 }
 lstrcpy(pattern,browseListed);n=lstrlen(pattern);
 if(n&&pattern[n-1]!='\\')lstrcat(pattern,"\\");
 lstrcat(pattern,masks[browseFilter]);
 if(!DlgDirList(w,pattern,NATIVELIST,0,DDL_DIRECTORY|DDL_DRIVES|DDL_READONLY|DDL_ARCHIVE) ||
    !getcwd(cwd,sizeof(cwd))||lstrcmpi(cwd,browseListed)||!browsealiases(w)){
  TSNamesEnd();browseBusy=0;browseListed[0]=0;
  SendDlgItemMessage(w,FILELIST,LB_RESETCONTENT,0,0L);
  SetDlgItemText(w,SHORTBOX,"");SetDlgItemText(w,PATHBOX,"Cannot list");
  EnableWindow(GetDlgItem(w,FILTER),TRUE);EnableWindow(GetDlgItem(w,IDOK),FALSE);return;
 }
 n=TSNamesCommit();
 if(n==-2){
  TSNamesEnd();browseBusy=0;browseListed[0]=0;
  SendDlgItemMessage(w,FILELIST,LB_RESETCONTENT,0,0L);
  SetDlgItemText(w,SHORTBOX,"");SetDlgItemText(w,PATHBOX,"Cannot list");
  EnableWindow(GetDlgItem(w,FILTER),TRUE);EnableWindow(GetDlgItem(w,IDOK),FALSE);return;
 }
 /* Changed enumeration leaves the freshly rebuilt aliases usable. */
 browseready(w,0);
}
static void browsefinish(HWND w,int result) {
 browsepaint(w,1);browsefinishwork(w,result);browsepaint(w,0);
}
BOOL FAR PASCAL BrowseProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HWND child;int i,n;char item[144],cwd[144];
 /* Win3 default Enter can report IDOK even when Cancel has focus. */
 if(m==WM_COMMAND&&wp==IDOK&&!lp&&GetFocus()==GetDlgItem(w,IDCANCEL))wp=IDCANCEL;
 if(m==WM_INITDIALOG){
  browseBusy=0;browseValid=0;browseListed[0]=0;TSNamesEnd();sizeDialog(w,BROWSEHEIGHT);
  CreateWindow("STATIC","",WS_CHILD|WS_VISIBLE|WS_BORDER|SS_LEFT,6,4,116,16,w,(HMENU)PATHBOX,instance,NULL);
  CreateWindow("COMBOBOX","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|CBS_DROPDOWNLIST|WS_VSCROLL,6,23,116,64,w,(HMENU)FILTER,instance,NULL);
  CreateWindow("LISTBOX","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|WS_BORDER|WS_VSCROLL|WS_HSCROLL|LBS_NOTIFY,6,45,116,72,w,(HMENU)FILELIST,instance,NULL);
  CreateWindow("LISTBOX","",WS_CHILD,0,0,0,0,w,(HMENU)NATIVELIST,instance,NULL);
  CreateWindow("STATIC","",WS_CHILD|WS_VISIBLE|WS_BORDER|SS_LEFT,6,122,116,16,w,(HMENU)SHORTBOX,instance,NULL);
  CreateWindow("BUTTON","&Open",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_DEFPUSHBUTTON,6,142,54,20,w,(HMENU)IDOK,instance,NULL);
  CreateWindow("BUTTON","&Cancel",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,68,142,54,20,w,(HMENU)IDCANCEL,instance,NULL);
  for(i=0;i<7;i++){child=GetDlgItem(w,i==0?PATHBOX:i==1?FILTER:i==2?FILELIST:i==3?IDOK:i==4?IDCANCEL:i==5?NATIVELIST:SHORTBOX);if(!child){EndDialog(w,IDCANCEL);return TRUE;}SendMessage(child,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);}
  for(i=0;i<3;i++)SendDlgItemMessage(w,FILTER,CB_ADDSTRING,0,(LPARAM)(LPSTR)masks[i]);
  SendDlgItemMessage(w,FILTER,CB_SETCURSEL,browseFilter,0L);
  if(!listfiles(w,"")){EndDialog(w,IDCANCEL);return TRUE;}
  SetFocus(GetDlgItem(w,browseBusy?IDCANCEL:FILELIST));return FALSE;
 }
 if(m==WM_TIMER&&wp==NAMES_TIMER){
  if(browseBusy){n=TSNamesStep();if(n!=1){browsefinish(w,n);if(!browseBusy)SetFocus(GetDlgItem(w,FILELIST));}}
  return TRUE;
 }
 if((m==WM_COMMAND&&wp==IDCANCEL)||m==WM_CLOSE){
  KillTimer(w,NAMES_TIMER);TSNamesEnd();browseBusy=0;EndDialog(w,IDCANCEL);return TRUE;
 }
 if(m==WM_DESTROY){KillTimer(w,NAMES_TIMER);TSNamesEnd();browseBusy=0;return TRUE;}
 if(m==WM_QUERYENDSESSION){if(browseBusy)browseready(w,1);return TRUE;}
 if(m==WM_ENDSESSION&&wp){KillTimer(w,NAMES_TIMER);TSNamesEnd();browseBusy=0;EndDialog(w,IDCANCEL);return TRUE;}
 if(m==WM_COMMAND&&browseBusy)return TRUE;
 if(m==WM_COMMAND&&wp==FILELIST&&HIWORD(lp)==LBN_SELCHANGE){browseselect(w);return TRUE;}
 if(m==WM_COMMAND&&wp==FILTER&&HIWORD(lp)==CBN_SELCHANGE){browseFilter=(int)SendDlgItemMessage(w,FILTER,CB_GETCURSEL,0,0L);listfiles(w,"");return TRUE;}
 if(m==WM_COMMAND&&(wp==IDOK||(wp==FILELIST&&HIWORD(lp)==LBN_DBLCLK))){
  if(!browseValid)return TRUE;
  if(!getcwd(cwd,sizeof(cwd))||lstrcmpi(cwd,browseListed)){listfiles(w,"");return TRUE;}
  i=(int)SendDlgItemMessage(w,FILELIST,LB_GETCURSEL,0,0L);if(i==LB_ERR)return TRUE;
  /* Copy only the index. DlgDirSelect sees the original native DOS row. */
  SendDlgItemMessage(w,NATIVELIST,LB_SETCURSEL,i,0L);
  if(DlgDirSelect(w,item,NATIVELIST)){listfiles(w,item);if(!browseBusy)SetFocus(GetDlgItem(w,FILELIST));return TRUE;}
  if(!getcwd(cwd,sizeof(cwd)))return TRUE;n=lstrlen(cwd);
  if(n+lstrlen(item)+2>sizeof(chosen))return TRUE;
  lstrcpy(chosen,cwd);if(n&&cwd[n-1]!='\\')lstrcat(chosen,"\\");lstrcat(chosen,item);EndDialog(w,IDOK);return TRUE;
 }
 return FALSE;
}
static int browse(HWND w) {
 int result,i,restored=1;unsigned drive;HGLOBAL h;char cwd[144];chosen[0]=0;browseFilter=0;
 if(!getcwd(browseOld,sizeof(browseOld)))return -1;
 _dos_getdrive(&drive);browseDrive=(int)drive;
 h=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,26*144);if(!h)return -1;
 browseDirs=(char FAR *)GlobalLock(h);if(!browseDirs){GlobalFree(h);return -1;}
 lstrcpy(browseDirs+(browseDrive-1)*144,browseOld);
 result=smallDialog(w,"Browse",BROWSEHEIGHT,(FARPROC)BrowseProc);
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
 case WM_TIMER:if(wp==HOLD_CLOSE_TIMER){if(TandyHoldCloseTick(w))DestroyWindow(w);}else if(wp==BOOT_TIMER){TandyBootTick(w);TandyHoldRefresh();}else if(wp==1)clockread(w);else if(wp==SAVER_TIMER)TSSaverTick(w);return 0;
 case STARTBOOT:if(primaryShell){TandyBootBegin(w);TSSaverBegin(w,instance);TandyHoldBegin(w,instance);}return 0;
 case HOLD_START:if(TandyHoldRequest(w,lp))popup(w);return 0;
 case OPENSYSTEM:
  systemQueued=0;if(GetActiveWindow()==w)systempopup(w);else TandyHoldMenuDone(1);return 0;
 case WM_LBUTTONDBLCLK:
  if((int)LOWORD(lp)>=width-45&&(int)LOWORD(lp)<width&&(int)HIWORD(lp)>=0&&(int)HIWORD(lp)<barHeight){TSSaverHold(1);TandyClock(w,instance);TSSaverHold(0);}
  return 0;
 case WM_RBUTTONUP:
  if((int)LOWORD(lp)>=width-45&&(int)LOWORD(lp)<width&&(int)HIWORD(lp)>=0&&(int)HIWORD(lp)<barHeight)clockpopup(w);
  return 0;
 case WM_SETFOCUS:return 0;
 case WM_COMMAND:
  if(wp==START){popup(w);return 0;}
  if(wp==SYSTEMMENU){
   if(!systemQueued){systemQueued=1;if(!PostMessage(w,OPENSYSTEM,0,0L))systemQueued=0;}
   return 0;
  }
  TandyHoldAction();
  if(wp>=FIRSTAPP&&wp<FIRSTAPP+1){launch(w,wp-FIRSTAPP);return 0;}
  if(wp==RUNAPP){TSSaverHold(1);runcommand(w);TSSaverHold(0);return 0;}
  if(wp==PROGRAMS){TSSaverHold(1);PmPrograms(w,instance);TSSaverHold(0);return 0;}
  if(wp==MYCOMPUTER){TSSaverHold(1);TandyFileManager(w,instance);TSSaverHold(0);return 0;}
  if(wp==ADJUSTTIME){TSSaverHold(1);TandyDateTime(w,instance);TSSaverHold(0);return 0;}
  if(wp==ABOUTSYS){TSSaverHold(1);TandySystem(w,instance);TSSaverHold(0);return 0;}
  if(wp==SAVERSETUP){TSSaverHold(1);TSSaverSettings(w,instance);TSSaverHold(0);return 0;}
  /* Snapshot Shift before confirmation runs its own modal input loop. */
  if(wp==EXITWIN){exitwindows(w,(GetKeyState(VK_SHIFT)&0x8000)!=0);return 0;}
  if(wp==CLOSEAPP&&!shellMode){if(TandyHoldClose(w))DestroyWindow(w);return 0;}break;
 case WM_CLOSE:TandyHoldAction();if(shellMode)exitwindows(w,0);else if(TandyHoldClose(w))DestroyWindow(w);return 0;
 case WM_QUERYENDSESSION:TSSaverShutdown(1);return TRUE;
 case WM_ENDSESSION:TSSaverShutdown(wp!=0);if(wp){TandyBootStop(w);DestroyWindow(w);}return 0;
 case WM_DESTROY:TandyHoldStop(w);TSSaverStop(w);TandyBootStop(w);KillTimer(w,1);PostQuitMessage(0);return 0;
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
 if(primaryShell)PostMessage(w,STARTBOOT,0,0L);else TandyHoldBegin(w,instance);
 while(GetMessage(&msg,NULL,0,0)){
  if(((msg.message==WM_KEYDOWN||msg.message==WM_SYSKEYDOWN)&&msg.wParam==VK_F10)||(msg.message==WM_KEYDOWN&&msg.wParam==VK_SPACE)){popup(w);continue;}
  if(msg.message==WM_SYSKEYDOWN&&msg.wParam=='S'){popup(w);continue;}
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
 return msg.wParam;
}
