#define WINVER 0x0300
#include <windows.h>
#include "TDROP.H"
static HWND root;
static unsigned step,ticks,failures;
static int busy;
static HFILE logFile;
static char pair[]="C:\\DROP.TXT\0C:\\SECOND.TXT\0";
static char longPath[]="C:\\LONGNAME\\SECOND\\THIRD\\FOURTH\\FIFTH\\SIXTH\\SEVENTH\\EIGHTH\\LONGFILE.TXT";
static char one[]="C:\\DROP.TXT\0";
static void check(int ok,char *name){char b[120];wsprintf(b,"%s %s\r\n",(LPSTR)(ok?"PASS":"FAIL"),(LPSTR)name);_lwrite(logFile,b,lstrlen(b));if(!ok)failures++;_lclose(logFile);logFile=_lopen("C:\\UIQA.LOG",OF_WRITE);_llseek(logFile,0L,2);}
static void sendpath(HWND w,int two){POINT p;HGLOBAL h;p.x=2;p.y=2;h=TDPack(two?pair:one,two?sizeof(pair):sizeof(one),p,FALSE);check(h&&TDPost(w,h),two?"post two normal paths":"post one normal path");}
static void closeclass(char *cls){HWND w=FindWindow(cls,NULL);if(w)PostMessage(w,WM_CLOSE,0,0L);}
static void capture(char *name){HFILE f;unsigned n;unsigned char mode;unsigned char FAR *v=(unsigned char FAR *)0xb8000000L;
 if(GetWinFlags()&WF_PMODE)return;mode=*((unsigned char FAR *)0x00400049L);if(mode!=4&&mode!=6&&mode!=8&&mode!=9&&mode!=10)return;
 n=(mode==9||mode==10)?32768U:16384U;f=_lcreat(name,0);if(f==HFILE_ERROR){check(0,"capture create");return;}
 check(_lwrite(f,(LPSTR)v,n)==n,"capture bounded framebuffer");_lclose(f);
}
static int ready(HWND w){return GetDlgItem(w,100)&&GetDlgItem(w,IDOK)&&GetDlgItem(w,IDCANCEL)&&GetDlgItem(w,102);}
static void typePath(HWND e,char *path){unsigned i;char b[144];
 SendMessage(e,EM_SETSEL,0,MAKELONG(0,32767));SendMessage(e,WM_CHAR,VK_BACK,1L);
 for(i=0;path[i];i++)SendMessage(e,WM_CHAR,(WPARAM)(unsigned char)path[i],1L);
 SendMessage(e,WM_GETTEXT,sizeof(b),(LONG)(LPSTR)b);check(!lstrcmp(b,path),"explicit edit messages set full path");
}
static void advance(void){HWND w,a,e;char b[144],row[144];int i,n;
 w=FindWindow("CDTESTCLASS",NULL);a=GetActiveWindow();
 switch(step){
 case 0:check(WinExec("C:\\EXJOY.EXE /demo",SW_SHOW)>=32,"launch EXJOY normal demo");break;
 case 1:w=FindWindow("TandyEXJOY",NULL);if(!w)return;SendMessage(w,WM_COMMAND,101,0L);SendDlgItemMessage(w,101,WM_GETTEXT,144,(LONG)(LPSTR)b);check(!lstrcmp(b,"&Run"),"pause button becomes Run");UpdateWindow(w);capture("C:\\PAUSED.RAW");break;
 case 2:w=FindWindow("TandyEXJOY",NULL);SendMessage(w,WM_COMMAND,101,0L);SendDlgItemMessage(w,101,WM_GETTEXT,144,(LONG)(LPSTR)b);check(!lstrcmp(b,"&Pause"),"resume button becomes Pause");break;
 case 3:closeclass("TandyEXJOY");break;
 case 4:check(!FindWindow("TandyEXJOY",NULL),"EXJOY closed");check(WinExec("C:\\DROPRX.EXE",SW_SHOW)>=32,"launch normal receiver");break;
 case 5:w=FindWindow("TandyDropRx",NULL);if(!w||!FindWindow("TandyDropTx",NULL))return;check(1,"normal independent sender launched");sendpath(w,1);break;
 case 6:UpdateWindow(FindWindow("TandyDropRx",NULL));capture("C:\\TWO.RAW");break;
 case 7:sendpath(FindWindow("TandyDropRx",NULL),0);break;
 case 8:UpdateWindow(FindWindow("TandyDropRx",NULL));capture("C:\\ONE.RAW");closeclass("TandyDropTx");closeclass("TandyDropRx");break;
 case 9:check(!FindWindow("TandyDropRx",NULL),"drop pair closed");check(WinExec("C:\\CDLG\\CDSTART.EXE",SW_SHOW)>=32,"launch unchanged CDSTART");break;
 case 10:if(!w)return;e=GetDlgItem(w,201);GetClassName(e,b,144);check(e&&!lstrcmpi(b,"LISTBOX"),"normal result path uses read-only list");PostMessage(w,WM_COMMAND,101,0L);break;
 case 11:e=GetDlgItem(a,100);if(!e||a==w||!ready(a))return;typePath(e,"C:\\DROP.TXT");PostMessage(a,WM_COMMAND,IDOK,0L);break;
 case 12:if(!w||a!=w)return;SendDlgItemMessage(w,201,LB_GETTEXT,0,(LONG)(LPSTR)b);check(!lstrcmp(b,"C:\\DROP.TXT"),"selected path displayed exactly");UpdateWindow(w);capture("C:\\SELECTED.RAW");break;
 case 13:PostMessage(w,WM_COMMAND,104,0L);break;
 case 14:e=GetDlgItem(a,100);if(!e||a==w||!ready(a))return;PostMessage(a,WM_COMMAND,IDCANCEL,0L);break;
 case 15:if(!w||a!=w)return;check(SendDlgItemMessage(w,201,LB_GETCOUNT,0,0L)==0,"Cancel clears stale selected path");UpdateWindow(w);capture("C:\\CANCEL.RAW");break;
 case 16:closeclass("CDTESTCLASS");break;
 case 17:check(!w,"normal dialog demo closed");check(WinExec("C:\\CDLG\\CDSTART.EXE",SW_SHOW)>=32,"reopen through unchanged CDSTART");break;
 case 18:if(!w)return;check(GetDlgItem(w,201)!=NULL,"reopened result field exists");break;
 case 19:PostMessage(w,WM_COMMAND,101,0L);break;
 case 20:e=GetDlgItem(a,100);if(!e||a==w||!ready(a))return;typePath(e,longPath);PostMessage(a,WM_COMMAND,IDOK,0L);break;
 case 21:if(!w||a!=w)return;b[0]=0;n=(int)SendDlgItemMessage(w,201,LB_GETCOUNT,0,0L);check(n>1,"long selected path wraps across rows");for(i=0;i<n;i++){SendDlgItemMessage(w,201,LB_GETTEXT,i,(LONG)(LPSTR)row);if(lstrlen(b)+lstrlen(row)<144)lstrcat(b,row);else check(0,"bounded QA row reconstruction");}check(!lstrcmp(b,longPath),"all long-path bytes remain visible in rows");UpdateWindow(w);capture("C:\\LONGPATH.RAW");break;
 case 22:closeclass("CDTESTCLASS");break;
 default:check(!FindWindow("CDTESTCLASS",NULL),"reopened demo closed");DestroyWindow(root);return;
 }
 step++;
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){char b[80];
 switch(m){case WM_CREATE:root=w;SetTimer(w,1,1000,NULL);return 0;
 case WM_TIMER:if(busy)return 0;busy=1;if(++ticks>80){check(0,"bounded timeout");closeclass("CDTESTCLASS");closeclass("TandyDropRx");closeclass("TandyDropTx");closeclass("TandyEXJOY");DestroyWindow(w);}else advance();busy=0;return 0;
 case WM_DESTROY:KillTimer(w,1);wsprintf(b,"FINAL failures=%u step=%u\r\n",failures,step);_lwrite(logFile,b,lstrlen(b));_lclose(logFile);PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE h,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS c;HWND w;MSG msg;int i;HDC dc;char metrics[100];
 for(i=64;i>=8;i/=2)if(SetMessageQueue(i))break;
 logFile=_lcreat("C:\\UIQA.LOG",0);if(logFile==HFILE_ERROR)return 1;
 check(!(GetWinFlags()&WF_PMODE),"normal-flow Windows real mode");dc=GetDC(NULL);wsprintf(metrics,"RUNTIME %d x %d colors=%d flags=%lu\r\n",GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),GetDeviceCaps(dc,NUMCOLORS),GetWinFlags());ReleaseDC(NULL,dc);_lwrite(logFile,metrics,lstrlen(metrics));
 c.style=0;c.lpfnWndProc=WndProc;c.cbClsExtra=c.cbWndExtra=0;c.hInstance=h;c.hIcon=NULL;c.hCursor=NULL;c.hbrBackground=NULL;c.lpszMenuName=NULL;c.lpszClassName="UtilityQA";if(!RegisterClass(&c))return 2;
 w=CreateWindow("UtilityQA","",WS_POPUP,0,0,1,1,NULL,NULL,h,NULL);if(!w)return 3;
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}ExitWindows(0L,0);return failures?1:0;
}
