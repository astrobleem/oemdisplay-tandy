/* Starfield choices are staged in memory; this module never writes an INI. */
#define WINVER 0x0300
#include <windows.h>
#include "TSSVOPT.H"
#include "TNOTICE.H"
#define OPT_WIDTH 128
#define OPT_HEIGHT 144
#define OPT_SLOW 130
#define OPT_MEDIUM 131
#define OPT_FAST 132
#define OPT_16 133
#define OPT_32 134
#define OPT_64 135
static HINSTANCE optInstance;
static HWND optWindow;
static int optBusy, optSpeed, optStars;
static HWND control(HWND w,char *text,DWORD style,int x,int y,int id)
{
 HWND child=CreateWindow("BUTTON",text,WS_CHILD|WS_VISIBLE|WS_TABSTOP|style,
                        x,y,54,20,w,(HMENU)id,optInstance,NULL);
 if(child)SendMessage(child,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
 return child;
}
BOOL FAR PASCAL StarOptProc(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 RECT r,c;PAINTSTRUCT ps;HDC dc;HFONT oldfont;int ww,hh;HWND button;
 if(m==WM_INITDIALOG){
  optWindow=w;GetWindowRect(w,&r);GetClientRect(w,&c);
  ww=OPT_WIDTH+r.right-r.left-c.right;hh=OPT_HEIGHT+r.bottom-r.top-c.bottom;
  if(ww>GetSystemMetrics(SM_CXSCREEN)||hh>GetSystemMetrics(SM_CYSCREEN)){EndDialog(w,IDCANCEL);return TRUE;}
  SetWindowPos(w,NULL,(GetSystemMetrics(SM_CXSCREEN)-ww)/2,(GetSystemMetrics(SM_CYSCREEN)-hh)/2,ww,hh,SWP_NOZORDER);
  if(!control(w,"&1",BS_RADIOBUTTON|WS_GROUP,6,18,OPT_SLOW)||
     !control(w,"&2",BS_RADIOBUTTON,6,38,OPT_MEDIUM)||
     !control(w,"&3",BS_RADIOBUTTON,6,58,OPT_FAST)||
     !control(w,"16",BS_RADIOBUTTON|WS_GROUP,68,18,OPT_16)||
     !control(w,"32",BS_RADIOBUTTON,68,38,OPT_32)||
     !control(w,"64",BS_RADIOBUTTON,68,58,OPT_64)||
     !control(w,"&OK",BS_PUSHBUTTON|WS_GROUP,6,120,IDOK)||
     !control(w,"&Cancel",BS_DEFPUSHBUTTON,68,120,IDCANCEL)){EndDialog(w,IDCANCEL);return TRUE;}
  CheckRadioButton(w,OPT_SLOW,OPT_FAST,OPT_SLOW+optSpeed-1);
  CheckRadioButton(w,OPT_16,OPT_64,optStars==16?OPT_16:optStars==64?OPT_64:OPT_32);
  SendMessage(w,DM_SETDEFID,IDCANCEL,0L);SetFocus(GetDlgItem(w,IDCANCEL));return FALSE;
 }
 if(m==WM_PAINT){
  dc=BeginPaint(w,&ps);oldfont=SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
  SetBkMode(dc,TRANSPARENT);SetTextColor(dc,GetSysColor(COLOR_WINDOWTEXT));
  TextOut(dc,6,0,"Speed",5);TextOut(dc,68,0,"Stars",5);
  TextOut(dc,6,82,"1 slow,3 fast",13);TextOut(dc,6,100,"OK, then Apply",14);
  SelectObject(dc,oldfont);EndPaint(w,&ps);return TRUE;
 }
 if(m==WM_COMMAND){
  if(wp==IDCANCEL){EndDialog(w,IDCANCEL);return TRUE;}
  if(wp>=OPT_SLOW&&wp<=OPT_64){
   if(HIWORD(lp)==BN_CLICKED&&(HWND)LOWORD(lp)==GetDlgItem(w,wp))
    CheckRadioButton(w,wp<=OPT_FAST?OPT_SLOW:OPT_16,wp<=OPT_FAST?OPT_FAST:OPT_64,wp);
   return TRUE;
  }
  if(wp==IDOK){
   button=GetDlgItem(w,IDOK);
   if(GetFocus()==button&&(!lp||((HWND)LOWORD(lp)==button&&HIWORD(lp)==BN_CLICKED))){
    optSpeed=IsDlgButtonChecked(w,OPT_SLOW)?1:IsDlgButtonChecked(w,OPT_FAST)?3:2;
    optStars=IsDlgButtonChecked(w,OPT_16)?16:IsDlgButtonChecked(w,OPT_64)?64:32;
    EndDialog(w,IDOK);
   }
   return TRUE;
  }
 }
 if(m==WM_CLOSE||(m==WM_ENDSESSION&&wp)){EndDialog(w,IDCANCEL);return TRUE;}
 if(m==WM_DESTROY)optWindow=NULL;
 return FALSE;
}
static void word(BYTE FAR **p,unsigned v){*(*p)++=(BYTE)v;*(*p)++=(BYTE)(v>>8);}
int SaverStarOptions(HWND owner,HINSTANCE instance,int *speed,int *stars)
{
 HGLOBAL memory;BYTE FAR *p;FARPROC proc;DWORD style,units;char *title="Starfield";int result=-1;
 if(optBusy){if(optWindow)SetActiveWindow(optWindow);return 0;}
 optBusy=1;optInstance=instance;optSpeed=*speed;optStars=*stars;
 memory=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,64);
 if(memory){p=(BYTE FAR *)GlobalLock(memory);if(p){
  style=WS_POPUP|WS_CAPTION|WS_SYSMENU|DS_MODALFRAME;
  word(&p,LOWORD(style));word(&p,HIWORD(style));*p++=0;units=GetDialogBaseUnits();
  word(&p,0);word(&p,0);word(&p,OPT_WIDTH*4/LOWORD(units));word(&p,OPT_HEIGHT*8/HIWORD(units));
  *p++=0;*p++=0;while(*title)*p++=*title++;*p=0;GlobalUnlock(memory);
  proc=MakeProcInstance((FARPROC)StarOptProc,instance);
  if(proc){result=DialogBoxIndirect(instance,memory,owner,(DLGPROC)proc);FreeProcInstance(proc);}
 }GlobalFree(memory);}
 optBusy=0;optWindow=NULL;
 if(result==IDOK){*speed=optSpeed;*stars=optStars;return 1;}
 if(result==-1)TinyNotice(owner,instance,"Starfield","Cannot open\noptions.");
 return 0;
}
