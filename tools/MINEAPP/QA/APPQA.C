/* Developer-only normal desktop acceptance controller; never in app packets.
 * Run as an extra Windows load task, preserving the fixture's normal shell.
 * The DOS fixture must have completed MINESET and COOKSET first.
 */
#define WINVER 0x0300
#include <windows.h>
static unsigned step,waits,round;
static HWND mine,cookie;
static HINSTANCE instance;
static char line[256];
static void logtext(char *text)
{
 HFILE f;f=_lopen("D:\\APPQA.LOG",OF_WRITE);
 if(f==HFILE_ERROR)f=_lcreat("D:\\APPQA.LOG",0);
 if(f==HFILE_ERROR)return;
 _llseek(f,0L,2);_lwrite(f,text,lstrlen(text));_lwrite(f,"\r\n",2);_lclose(f);
}
static void note(char *message)
{wsprintf(line,"step=%u round=%u tick=%lu %s",step,round,GetTickCount(),message);logtext(line);}
static void fail(char *message)
{note(message);logtext("FAIL");PostQuitMessage(1);}
static void next(void){step++;waits=0;}
static HWND about(HWND owner)
{
 HWND w;char classname[32];
 w=GetWindow(GetDesktopWindow(),GW_CHILD);
 while(w){GetClassName(w,classname,sizeof(classname));
  if(!lstrcmp(classname,"#32770")&&GetWindow(w,GW_OWNER)==owner)return w;
  w=GetWindow(w,GW_HWNDNEXT);
 }
 return NULL;
}
static HWND game(void)
{
 HWND w;char c[32];w=FindWindow(NULL,"Minesweeper");
 if(w){GetClassName(w,c,sizeof(c));if(!lstrcmp(c,"#32770"))return NULL;}
 return w;
}
static int saved(void)
{
 HFILE f;BYTE b[13];UINT n;unsigned sum=0x436b,i;
 f=_lopen("C:\\COOKIE\\COOKIE.SAV",OF_READ);if(f==HFILE_ERROR)return 0;
 n=_lread(f,b,13);_lclose(f);
 if(n!=12||b[0]!='T'||b[1]!='C'||b[2]!='C'||b[3]!=1||b[8]!=1||b[9])return 0;
 for(i=0;i<10;i++)sum=(sum<<1)^b[i]^(sum>>15);
 return b[10]==(BYTE)sum&&b[11]==(BYTE)(sum>>8);
}
static void tick(void)
{
 HWND d;unsigned i,result;char caption[80],path[144];HINSTANCE module;
 if(++waits>180){fail("Timed out waiting for the current app step");return;}
 switch(step){
 case 0:
  if(!FindWindow("Progman",NULL)&&!FindWindow("TandyStart",NULL))return;
  note("Starting private MINERUN from normal desktop");
  result=WinExec("C:\\MINETST\\MINERUN.EXE",SW_SHOWNORMAL);
  if(result<32){fail("MINERUN WinExec failed");return;}next();break;
 case 1:
  mine=game();if(!mine)return;
  module=GetModuleHandle("WMABT");if(!module){fail("Game loaded without its About module");return;}
  if(!GetModuleFileName(module,path,sizeof(path))){fail("Cannot inspect loaded About module");return;}
  logtext(path);if(lstrcmpi(path,"C:\\MINETST\\WMABT.DLL")){fail("About module was not app-local");return;}
  note("Game window and private About module present");
  PostMessage(mine,WM_COMMAND,596,0L);next();break;
 case 2:
  d=about(mine);if(!d)return;
  GetWindowText(d,caption,sizeof(caption));logtext(caption);
  note("About dialog present");PostMessage(d,WM_COMMAND,IDOK,0L);next();break;
 case 3:
  if(about(mine))return;
  PostMessage(mine,WM_COMMAND,510,0L);note("New game requested after About");next();break;
 case 4:
  if(!game()){fail("Game disappeared before normal close");return;}
  PostMessage(mine,WM_CLOSE,0,0L);next();break;
 case 5:
  if(game())return;
  note("Minesweeper closed normally");
  if(!round){round=1;step=0;waits=0;}else next();break;
 case 6:
  note("Starting unchanged Cookie directly from desktop");
  if(WinExec("C:\\COOKIE\\COOKIE.EXE",SW_SHOWNORMAL)<32){fail("Cookie WinExec failed");return;}
  next();break;
 case 7:
  cookie=FindWindow("CookieBench",NULL);if(!cookie)return;
  SendMessage(cookie,WM_COMMAND,101,0L);
  for(i=0;i<10;i++)SendMessage(cookie,WM_KEYDOWN,VK_SPACE,0L);
  SendMessage(cookie,WM_COMMAND,20,0L);
  SendMessage(cookie,WM_COMMAND,102,0L);next();break;
 case 8:
  if(!saved())return;
  note("Cookie click/buy/save produced a valid one-CPS save");
  SendMessage(cookie,WM_COMMAND,101,0L);
  SendMessage(cookie,WM_COMMAND,103,0L);
  SendMessage(cookie,WM_COMMAND,102,0L);next();break;
 case 9:
  if(!saved()){fail("Cookie load/save did not restore one CPS");return;}
  note("Cookie load/save passed");PostMessage(cookie,WM_CLOSE,0,0L);next();break;
 case 10:
  if(FindWindow("CookieBench",NULL))return;
  note("Cookie closed normally");logtext("PASS_NORMAL_DESKTOP_APPS");
  ExitWindows(0,0L);PostQuitMessage(0);step++;break;
 }
}
LONG FAR PASCAL WindowProc(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 if(m==WM_TIMER){tick();return 0;}
 if(m==WM_DESTROY){PostQuitMessage(1);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR args,int show)
{
 WNDCLASS c;HWND w;MSG msg;HFILE f;
 prev=prev;args=args;show=show;instance=inst;
 f=_lcreat("D:\\APPQA.LOG",0);if(f!=HFILE_ERROR)_lclose(f);
 logtext("BEGIN_NORMAL_DESKTOP_APPS");
 c.style=0;c.lpfnWndProc=WindowProc;c.cbClsExtra=0;c.cbWndExtra=0;
 c.hInstance=instance;c.hIcon=NULL;c.hCursor=NULL;c.hbrBackground=NULL;
 c.lpszMenuName=NULL;c.lpszClassName="NativeAppQA";
 if(!RegisterClass(&c)){fail("RegisterClass failed");return 1;}
 w=CreateWindow(c.lpszClassName,"Native app QA",WS_OVERLAPPEDWINDOW,
                0,0,120,80,NULL,NULL,instance,NULL);
 if(!w){fail("Controller window failed");return 1;}
 ShowWindow(w,SW_SHOWMINNOACTIVE);
 if(!SetTimer(w,1,1000,NULL)){fail("Controller timer failed");return 1;}
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 return msg.wParam;
}
