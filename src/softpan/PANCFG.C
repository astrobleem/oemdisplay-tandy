/* Enable/remove the helper without asking users to edit WIN.INI. */
#include <windows.h>
#include "PANSET.H"
#include "PANOWN.H"
#include "PANSTART.H"
static char path[128];
static HINSTANCE noticeInst;
static HWND noticeButton;
static int smallNotice;
static void CopyArg(char *d,LPSTR s,int cap){int i=0;while(s[i] && i<cap-1){d[i]=s[i];i++;}d[i]=0;}
long FAR PASCAL NoticeProc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp)
{
 switch(msg){
 case WM_CREATE:
  CreateWindow("STATIC","Panning is off or unavailable. Run PANCFG to enable a supported owner.",WS_CHILD|WS_VISIBLE|SS_LEFT,smallNotice?4:12,8,smallNotice?140:256,smallNotice?44:44,hwnd,NULL,noticeInst,NULL);
  noticeButton=CreateWindow("BUTTON","OK",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_DEFPUSHBUTTON,smallNotice?56:110,smallNotice?58:62,smallNotice?40:60,smallNotice?10:20,hwnd,(HMENU)1,noticeInst,NULL);return 0;
 case WM_SETFOCUS:if(noticeButton)SetFocus(noticeButton);return 0;
 case WM_COMMAND:if(wp==1){DestroyWindow(hwnd);return 0;}break;
 case WM_CLOSE:DestroyWindow(hwnd);return 0;
 case WM_DESTROY:noticeButton=NULL;PostQuitMessage(0);return 0;
 }
 return DefWindowProc(hwnd,msg,wp,lp);
}
static void OffNotice(HINSTANCE inst)
{
 HDC dc;HWND owner;WNDCLASS wc;MSG msg;int x=0,y=0,w,h,q=-1,in[2],out[6];
 owner=FindWindow("PanCfgNotice",NULL);if(owner){BringWindowToTop(owner);SetFocus(owner);return;}
 w=GetSystemMetrics(SM_CXSCREEN);h=GetSystemMetrics(SM_CYSCREEN);dc=GetDC(NULL);
 if(Escape(dc,0x5850,2,(LPSTR)&q,(LPSTR)out)>0 && out[0]>=0 && out[1]>0){y=out[0];h=out[1];}
 else{in[0]=-1;in[1]=0;if(Escape(dc,0x5860,4,(LPSTR)in,(LPSTR)out)>0 && out[0]>=0 && out[1]>=0 && out[2]>0 && out[3]>0){x=out[0];y=out[1];w=out[2];h=out[3];}}
 ReleaseDC(NULL,dc);smallNotice=w<280 || h<112;
 noticeInst=inst;wc.style=0;wc.lpfnWndProc=NoticeProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);wc.lpszMenuName=NULL;wc.lpszClassName="PanCfgNotice";
 if(!RegisterClass(&wc))return;
 owner=CreateWindow("PanCfgNotice","Panning settings",WS_POPUP|WS_CAPTION|WS_SYSMENU,x+(w-(smallNotice?152:280))/2,y+(h-(smallNotice?90:112))/2,smallNotice?152:280,smallNotice?90:112,NULL,NULL,inst,NULL);
 if(!owner)return;ShowWindow(owner,SW_SHOWNORMAL);SetFocus(owner);
 while(IsWindow(owner) && GetMessage(&msg,NULL,0,0)){
  if(msg.message==WM_KEYDOWN && (msg.wParam==VK_RETURN || msg.wParam==VK_ESCAPE)){DestroyWindow(owner);continue;}
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 char old[512],out[512],oldRun[512],runOut[512],arg[24],run[176];
 char oldEnabled[24],oldWindow[24];
 int kind,ownerKind,fixed=0,started=0,failure=4,changedRun=0;HWND owner;
 CopyArg(arg,cmd,sizeof(arg));kind=PanCmdParse(arg);
 owner=PanOwnerFind(&ownerKind);
 if(kind==PS_CMD_SETTINGS&&owner){PanOwnerRoute(1);return 0;}
 if(kind!=PS_CMD_OFF){
  if(!owner)ownerKind=PanOwnerDetect(&fixed);
  else if(ownerKind==PN_VERT&&PanOwnerDetect(&fixed)!=PN_VERT)fixed=0;
  if(!ownerKind){OffNotice(inst);return 8;}
  if(!PanOwnerPath(owner?(HINSTANCE)GetWindowWord(owner,GWW_HINSTANCE):inst,ownerKind,path,sizeof(path))){OffNotice(inst);return 5;}
  if(kind==PS_CMD_SETTINGS){
   if(PanRoute(0,ownerKind!=PN_VERT||GetProfileInt("XTPan","Enabled",1))==PS_ROUTE_OFF){OffNotice(inst);return 7;}
   lstrcpy(run,path);lstrcat(run," " PS_ARG_SETTINGS);
   if(WinExec(run,SW_SHOWNORMAL)<32 || !PanOwnerFind(0)){OffNotice(inst);return 4;}
   return 0;
  }
 }
 if(GetProfileString("windows","load","",old,sizeof(old))>=sizeof(old)-1 ||
    GetProfileString("windows","run","",oldRun,sizeof(oldRun))>=sizeof(oldRun)-1)return 1;
 if(!PanStartupEdit(old,kind==PS_CMD_OFF?0:path,out,sizeof(out)) ||
    !PanStartupEdit(oldRun,0,runOut,sizeof(runOut)))return 2;
 if(kind==PS_CMD_OFF){
  if(!WriteProfileString("windows","run",runOut))return 3;
  if(!WriteProfileString("windows","load",out)){
   (void)WriteProfileString("windows","run",oldRun);return 3;
  }
  if(owner)PostMessage(owner,WM_CLOSE,0,0L);return 0;
 }
 if(ownerKind==PN_VERT){
  if(GetProfileString("XTPan","Enabled","\1",oldEnabled,sizeof(oldEnabled))>=sizeof(oldEnabled)-1 ||
     GetProfileString("XTPan","WindowWorkspace","\1",oldWindow,sizeof(oldWindow))>=sizeof(oldWindow)-1)return 1;
  if(!WriteProfileString("XTPan","Enabled","1"))return 6;
  if(fixed&&!WriteProfileString("XTPan","WindowWorkspace","1")){failure=6;goto failed;}
 }
 if(!owner){
  if(WinExec(path,SW_SHOWNORMAL)<32)goto failed;
  owner=PanOwnerFind(0);if(!owner)goto failed;started=1;
 }
 failure=3;
 if(!WriteProfileString("windows","run",runOut))goto failed;
 changedRun=1;
 if(WriteProfileString("windows","load",out))return 0;
failed:
 if(changedRun)(void)WriteProfileString("windows","run",oldRun);
 if(started)PostMessage(owner,WM_CLOSE,0,0L);
 if(ownerKind==PN_VERT){
  (void)WriteProfileString("XTPan","Enabled",oldEnabled[0]=='\1'?NULL:oldEnabled);
  (void)WriteProfileString("XTPan","WindowWorkspace",oldWindow[0]=='\1'?NULL:oldWindow);
 }
 if(failure==4)OffNotice(inst);
 return failure;
}
