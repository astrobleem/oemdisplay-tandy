/* Enable/remove the helper without asking users to edit WIN.INI. */
#include <windows.h>
#include "PANSET.H"
static char path[128];
static HINSTANCE noticeInst;
static HWND noticeButton;
static void CopyArg(char *d,LPSTR s,int cap){int i=0;while(s[i] && i<cap-1){d[i]=s[i];i++;}d[i]=0;}
long FAR PASCAL NoticeProc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp)
{
 switch(msg){
 case WM_CREATE:
  CreateWindow("STATIC","XTPAN panning is turned off. Run PANCFG to turn it on, then PANCFG SETTINGS.",WS_CHILD|WS_VISIBLE|SS_LEFT,12,8,256,44,hwnd,NULL,noticeInst,NULL);
  noticeButton=CreateWindow("BUTTON","OK",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_DEFPUSHBUTTON,110,62,60,20,hwnd,(HMENU)1,noticeInst,NULL);return 0;
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
 ReleaseDC(NULL,dc);
 noticeInst=inst;wc.style=0;wc.lpfnWndProc=NoticeProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);wc.lpszMenuName=NULL;wc.lpszClassName="PanCfgNotice";
 if(!RegisterClass(&wc))return;
 owner=CreateWindow("PanCfgNotice","Panning settings",WS_POPUP|WS_CAPTION|WS_SYSMENU,x+(w-280)/2,y+(h-112)/2,280,112,NULL,NULL,inst,NULL);
 if(!owner)return;ShowWindow(owner,SW_SHOWNORMAL);SetFocus(owner);
 while(IsWindow(owner) && GetMessage(&msg,NULL,0,0)){
  if(msg.message==WM_KEYDOWN && (msg.wParam==VK_RETURN || msg.wParam==VK_ESCAPE)){DestroyWindow(owner);continue;}
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 char old[512],out[512],token[512],arg[24],run[160];int i=0,j=0,k,off,found=0,kind;HWND h,h2;
 if(!GetModuleFileName(inst,path,sizeof(path)))return 5;
 for(k=lstrlen(path)-1;k>=0 && path[k]!='\\';k--);path[k+1]=0;lstrcat(path,"XTPAN.EXE");
 CopyArg(arg,cmd,sizeof(arg));kind=PanCmdParse(arg);
 if(kind==PS_CMD_SETTINGS){
  /* Settings never touch load= or Enabled: only reach the running owner. */
  h=FindWindow("XTPan",NULL);
  if(!h && (h2=FindWindow("XYOverviewControl",NULL))!=NULL){PostMessage(h2,RegisterWindowMessage(PS_MSG_XY),0,0L);return 0;}
  switch(PanRoute(h!=NULL,GetProfileInt("XTPan","Enabled",1)!=0)){
  case PS_ROUTE_POST:PostMessage(h,RegisterWindowMessage(PS_MSG_VERT),0,0L);return 0;
  case PS_ROUTE_START:lstrcpy(run,path);lstrcat(run," " PS_ARG_SETTINGS);
   if(WinExec(run,SW_SHOWNORMAL)<32)return 4;return 0;
  }
  OffNotice(inst);
  return 7;
 }
 off=kind==PS_CMD_OFF;
 if(GetProfileString("windows","load","",old,sizeof(old))>=sizeof(old)-1)return 1;
 while(old[i]){
  while(old[i]==' ' || old[i]=='\t')i++;k=0;
  while(old[i] && old[i]!=' ' && old[i]!='\t')token[k++]=old[i++];token[k]=0;
  if(!k)break;
  if(!lstrcmpi(token,path)){found=1;if(off)continue;}
  if(j)out[j++]=' ';for(k=0;token[k];k++)out[j++]=token[k];
 }
 if(!off && !found){if(j+lstrlen(path)+2>=sizeof(out))return 2;if(j)out[j++]=' ';for(k=0;path[k];k++)out[j++]=path[k];}
 out[j]=0;if(!WriteProfileString("windows","load",out))return 3;
 if(!off && !WriteProfileString("XTPan","Enabled","1"))return 6;
 if(off){h=FindWindow("XTPan",NULL);if(h)PostMessage(h,WM_CLOSE,0,0L);}
 else if(!FindWindow("XTPan",NULL) && WinExec(path,SW_SHOWNORMAL)<32)return 4;
 return 0;
}
