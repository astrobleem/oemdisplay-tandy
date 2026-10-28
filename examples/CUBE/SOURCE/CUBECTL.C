/* Developer-only native UI/idle acceptance controller. Never installed. */
#define WINVER 0x0300
#include <windows.h>
static int stage,ticks,errors,configSeen,shellSeen,pan,oldX,oldY,fieldLogged,ownerArmed,ownerLoss,ownerGained;static HWND cfg,bar;static DWORD since;static char ini[144];
static void logtext(char *s){HFILE f=_lopen("C:\\CUBEUI.LOG",OF_WRITE);if(f==HFILE_ERROR)f=_lcreat("C:\\CUBEUI.LOG",0);if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);}}
static void next(int s,char *text){stage=s;since=GetTickCount();logtext(text);}
static HWND dialog(int cube)
{
 HWND w=GetWindow(GetDesktopWindow(),GW_CHILD);
 while(w){if(IsWindowVisible(w)&&(GetDlgItem(w,cube?101:127)||(!cube&&GetDlgItem(w,128)))&&GetDlgItem(w,cube?105:125))return w;w=GetWindow(w,GW_HWNDNEXT);}return NULL;
}
static void click(HWND w,int id){HWND c=GetDlgItem(w,id);SetActiveWindow(w);SetFocus(c);SendMessage(w,WM_COMMAND,id,MAKELONG(c,BN_CLICKED));}
LONG FAR PASCAL ControlProc(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 HWND s;HDC dc;char b[80];int ok,in[2],answer[6];
 if(ownerArmed&&(m==WM_SETFOCUS||m==WM_KILLFOCUS||m==WM_ACTIVATE||m==WM_ACTIVATEAPP)){
  wsprintf(b,"UI OWNER EVENT message=%u state=%u\r\n",m,wp);logtext(b);
  if(m==WM_SETFOCUS||(m==WM_ACTIVATE&&wp!=WA_INACTIVE))ownerGained=1;
  if(ownerGained&&(m==WM_KILLFOCUS||(m==WM_ACTIVATE&&wp==WA_INACTIVE)||(m==WM_ACTIVATEAPP&&!wp)))ownerLoss++;
 }
 if(m==WM_TIMER){
  ticks++;if(GetTickCount()-since>(stage==21?300000UL:60000UL)){logtext("UI FAIL timeout\r\n");KillTimer(w,1);return 0;}
  if(stage==0){WinExec("C:\\WINXT\\CUBE.EXE /C",SW_SHOWNORMAL);next(1,"UI settings launched\r\n");}
  else if(stage==1&&(cfg=dialog(1))!=NULL){
   if(!configSeen++){next(1,"UI CONFIG VISIBLE\r\n");return 0;}
   if(GetTickCount()-since<2000UL)return 0;
   click(cfg,101);click(cfg,102);click(cfg,103);click(cfg,105);
   GetWindowsDirectory(ini,sizeof(ini));lstrcat(ini,"\\CUBE.INI");
   ok=GetPrivateProfileInt("Cube","Style",-1,ini)==1&&GetPrivateProfileInt("Cube","Speed",-1,ini)==3&&GetPrivateProfileInt("Cube","Size",-1,ini)==3;
   logtext(ok?"UI SAVE PASS\r\n":"UI FAIL save\r\n");if(!ok)errors++;
   click(cfg,104);next(2,"UI preview clicked\r\n");
  }else if(stage==2&&(s=FindWindow("TandyCubeSaver",NULL))!=NULL){
   next(3,"UI preview visible\r\n");
  }else if(stage==3&&GetTickCount()-since>2000UL){
   s=FindWindow("TandyCubeSaver",NULL);if(s){SendMessage(s,WM_KEYDOWN,VK_ESCAPE,0L);SendMessage(s,WM_KEYUP,VK_ESCAPE,0L);}next(4,"UI preview wake\r\n");
  }else if(stage==4&&!FindWindow("TandyCubeSaver",NULL)){
   if(!IsWindow(cfg)||!IsWindowVisible(cfg)||GetActiveWindow()!=cfg){logtext("UI FAIL preview return focus\r\n");errors++;return 0;}
   logtext("UI PREVIEW RETURN PASS\r\n");click(cfg,104);next(16,"UI ownership preview requested\r\n");
  }else if(stage==16&&FindWindow("TandyCubeSaver",NULL)){
   SetWindowPos(w,NULL,8,8,100,28,SWP_NOACTIVATE);ShowWindow(w,SW_SHOWNOACTIVATE);
   ownerLoss=ownerGained=0;ownerArmed=1;SetActiveWindow(w);next(17,"UI preview ownership transferred\r\n");
  }else if(stage==17&&!FindWindow("TandyCubeSaver",NULL)&&GetTickCount()-since>2000UL){
   wsprintf(b,"UI OWNER losses=%d active=%u expected=%u focus=%u\r\n",ownerLoss,GetActiveWindow(),w,GetFocus());logtext(b);
   ownerArmed=0;
   if(!ownerGained||ownerLoss||GetActiveWindow()!=w||GetFocus()!=w){logtext("UI FAIL preview stole focus\r\n");errors++;return 0;}
   logtext("UI PREVIEW OWNER PASS\r\n");ShowWindow(w,SW_HIDE);
   PostMessage(cfg,WM_CLOSE,0,0L);next(5,"UI preview returned\r\n");
  }else if(stage==5&&!GetModuleHandle("CUBE")){
   WinExec("C:\\WINDOWS\\TSHELL.EXE",SW_SHOWNORMAL);next(6,"UI shell launched\r\n");
  }else if(stage==6&&(bar=FindWindow("TandyStart",NULL))!=NULL){
   PostMessage(bar,WM_COMMAND,48,0L);next(7,"UI shell settings requested\r\n");
  }else if(stage==7&&(cfg=dialog(0))!=NULL){
   if(GetDlgItem(cfg,128))SendDlgItemMessage(cfg,128,CB_SETCURSEL,3,0L);else click(cfg,127);
   if(!shellSeen++){next(7,"UI SHELL CFG VISIBLE\r\n");return 0;}
   if(GetTickCount()-since<2000UL)return 0;
   SetActiveWindow(cfg);SetFocus(GetDlgItem(cfg,123));
   SendDlgItemMessage(cfg,123,EM_SETSEL,0,MAKELONG(0,32767));
   next(15,"UI NEED DELAY INPUT\r\n");
  }else if(stage==15){
   /* Query the edit procedure explicitly across tasks. The final acceptance
      is the shell's own persisted value after Apply. */
   b[0]=0;SendMessage(GetDlgItem(cfg,123),WM_GETTEXT,sizeof(b),(LPARAM)(LPSTR)b);
   if(!fieldLogged++){logtext("UI EDIT TEXT [");logtext(b);logtext("]\r\n");}
   if(GetTickCount()-since<3000UL)return 0;
   logtext("UI delay hardware input settled\r\n");
   SetActiveWindow(cfg);SetFocus(GetDlgItem(cfg,125));
   next(8,"UI shell Cube Apply\r\n");
   PostMessage(cfg,WM_COMMAND,125,MAKELONG(GetDlgItem(cfg,125),BN_CLICKED));
  }else if(stage==8){
   /* Dismiss only the shell's own Saved notice, preserving its settings dialog. */
   s=GetActiveWindow();if(s&&s!=cfg&&s!=bar){PostMessage(s,WM_CLOSE,0,0L);return 0;}
   GetWindowsDirectory(ini,sizeof(ini));lstrcat(ini,"\\TSHELL.INI");
   GetPrivateProfileString("ScreenSaver","Choice","?",b,sizeof(b),ini);
   if(lstrcmp(b,"Cube")||GetPrivateProfileInt("ScreenSaver","IdleSeconds",0,ini)!=10)return 0;
   logtext("UI SHELL SAVE PASS\r\n");
   PostMessage(cfg,WM_CLOSE,0,0L);next(9,"UI NEED REAL INPUT\r\n");
  }else if(stage==9&&(s=FindWindow("TandyCubeSaver",NULL))!=NULL){
   next(10,"UI IDLE CUBE PASS\r\n");
  }else if(stage==10&&GetTickCount()-since>2000UL){
   next(11,"UI NEED REAL WAKE\r\n");
  }else if(stage==11&&!GetModuleHandle("CUBE")){
   logtext(errors?"UI DONE FAIL\r\n":"UI DONE PASS\r\n");KillTimer(w,1);
  }else if(stage==20){
   if(pan){
    dc=GetDC(NULL);in[0]=-1;in[1]=0;
    ok=dc&&Escape(dc,0x5860,4,(LPSTR)in,(LPSTR)answer)>0;
    if(ok){oldX=answer[0];oldY=answer[1];in[0]=160;in[1]=28;
     ok=Escape(dc,0x5860,4,(LPSTR)in,(LPSTR)answer)>0&&answer[0]==160&&answer[1]==28&&answer[2]>=160&&answer[3]>=100&&answer[4]>answer[2];
    }
    if(dc)ReleaseDC(NULL,dc);
    if(!ok){logtext("UI FAIL viewport setup\r\n");KillTimer(w,1);return 0;}
    wsprintf(b,"VIEWPORT SET %d,%d %dx%d logical=%dx%d\r\n",answer[0],answer[1],answer[2],answer[3],answer[4],answer[5]);logtext(b);
   }
   WinExec("C:\\WINXT\\CUBE.EXE /Q",SW_SHOWNORMAL);next(21,"RENDER QA launched\r\n");
  }else if(stage==21&&!GetModuleHandle("CUBE")){
   if(pan){dc=GetDC(NULL);in[0]=oldX;in[1]=oldY;if(dc){Escape(dc,0x5860,4,(LPSTR)in,(LPSTR)answer);ReleaseDC(NULL,dc);}}
   logtext("RENDER QA returned; exiting private Windows fixture\r\n");KillTimer(w,1);ExitWindows(0L,0);
  }
  return 0;
 }
 if(m==WM_DESTROY){PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 WNDCLASS wc;HWND w;MSG msg;HFILE f;
 f=_lcreat("C:\\CUBEUI.LOG",0);if(f!=HFILE_ERROR)_lclose(f);
 wc.style=0;wc.lpfnWndProc=ControlProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;
 wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="CubeController";
 if(!RegisterClass(&wc))return 1;
 w=CreateWindow("CubeController","Cube acceptance",WS_POPUP,0,0,1,1,NULL,NULL,inst,NULL);if(!w)return 2;
 if(cmd[0]=='/'&&(cmd[1]=='Q'||cmd[1]=='q'))stage=20;
 if(cmd[0]=='/'&&(cmd[1]=='P'||cmd[1]=='p')){pan=1;stage=20;}
 since=GetTickCount();if(!SetTimer(w,1,550,NULL))return 3;
 while(GetMessage(&msg,NULL,0,0))DispatchMessage(&msg);return errors;
}
