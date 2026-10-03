#define WINVER 0x0300
#include <windows.h>
#include <dos.h>
#include <direct.h>
static int phase,failed,waits,drive=3;
static HWND app,pop;
static char prefix[80]="C:\\TANDYLAB\\EXPER\\CDLG\\",start[100],roundpath[100],before[144],prior[144];
static void val(char *label,int n){HFILE f;char b[160];f=_lopen("C:\\STARTQA.LOG",OF_WRITE);_llseek(f,0L,2);wsprintf(b,"%s=%d\r\n",(LPSTR)label,n);_lwrite(f,b,lstrlen(b));_lclose(f);}
static void ck(char *label,int n){val(label,n!=0);if(!n)failed++;}
static int ready(int yes){if(yes){waits=0;return 1;}if(++waits>30){ck("TIMEOUT",0);phase=99;}return 0;}
static int samecwd(void){char cwd[144],other[144];return getcwd(cwd,144)&&_getdcwd(drive,other,144)&&!lstrcmpi(cwd,before)&&!lstrcmpi(other,prior);}
static void dlgkey(HWND w,int id){HWND b=GetDlgItem(w,id);PostMessage(w,WM_NEXTDLGCTL,(WPARAM)b,1L);PostMessage(b,WM_KEYDOWN,VK_RETURN,1L);PostMessage(b,WM_KEYUP,VK_RETURN,0xC0000001L);}
static void closebox(HWND w){HWND b=GetWindow(w,GW_CHILD);val("ERROR_CHILD_HANDLE",(int)b);if(b)val("ERROR_CHILD_ID",GetDlgCtrlID(b));PostMessage(w,WM_KEYDOWN,VK_RETURN,1L);PostMessage(w,WM_CHAR,13,1L);PostMessage(w,WM_KEYUP,VK_RETURN,0xC0000001L);}
static void tick(HWND w){char buf[160];HFILE f;int n;HANDLE h;switch(phase){
case 0:ck("REAL_MODE",!(GetWinFlags()&WF_PMODE));getcwd(before,144);_getdcwd(drive,prior,144);ck("START_LAUNCH",WinExec(start,SW_SHOWNORMAL)>=32);break;
case 1:app=FindWindow("CDTESTCLASS",NULL);if(!ready(app!=NULL))return;ck("CDTEST_WINDOW",1);h=GetModuleHandle("COMMDLG");ck("DLL_LOADED",h!=NULL);GetModuleFileName(h,buf,sizeof(buf));{char expected[100];lstrcpy(expected,prefix);lstrcat(expected,"COMMDLG.DLL");ck("EXACT_LOCAL_DLL",!lstrcmpi(buf,expected));}ck("PARENT_DIRS_RESTORED",samecwd());ck("LOADED_REJECT_LAUNCH",WinExec(start,SW_SHOWNORMAL)>=32);break;
case 2:pop=FindWindow(NULL,"CDSTART");if(!ready(pop!=NULL))return;ck("LOADED_MODULE_REJECTED",1);closebox(pop);break;
case 3:if(!ready(!IsWindow(pop)))return;ck("LOADED_REJECT_DIRS",samecwd());PostMessage(app,WM_COMMAND,102,0L);break;
case 4:pop=FindWindow(NULL,"Save test");if(!ready(pop!=NULL&&GetDlgItem(pop,IDOK)!=NULL))return;ck("SAVE_DIALOG",1);dlgkey(pop,IDOK);break;
case 5:if(!ready(!IsWindow(pop)))return;f=_lopen(roundpath,OF_READ);if(!ready(f!=HFILE_ERROR))return;ck("NEW_FILE_CREATED",f!=HFILE_ERROR);if(f!=HFILE_ERROR){n=_lread(f,buf,sizeof(buf)-1);buf[n]=0;_lclose(f);ck("SAVED_PAYLOAD",!lstrcmp(buf,"COMMDLG30 independent caller round-trip\r\n"));}PostMessage(app,WM_COMMAND,103,0L);break;
case 6:pop=FindWindow(NULL,"Open test");if(!ready(pop!=NULL&&GetDlgItem(pop,IDOK)!=NULL))return;ck("READ_DIALOG",1);dlgkey(pop,IDOK);break;
case 7:if(!ready(!IsWindow(pop)))return;PostMessage(app,WM_COMMAND,104,0L);break;
case 8:pop=FindWindow(NULL,"Please Cancel");if(!ready(pop!=NULL&&GetDlgItem(pop,IDOK)!=NULL))return;ck("CANCEL_DIALOG",1);PostMessage(pop,WM_COMMAND,IDCANCEL,0L);break;
case 9:if(!ready(!IsWindow(pop)))return;PostMessage(app,WM_COMMAND,105,0L);break;
case 10:if(!ready(!IsWindow(app)))return;ck("CDTEST_CLOSED",1);ck("DLL_UNLOADED",GetModuleHandle("COMMDLG")==NULL);val("CHILD_DIRS_EQUAL_PRELAUNCH",samecwd());getcwd(before,144);_getdcwd(drive,prior,144);ck("MISSDLL_LAUNCH",WinExec("C:\\MISSDLL\\CDSTART.EXE",SW_SHOWNORMAL)>=32);break;
case 11:pop=FindWindow(NULL,"CDSTART");if(!ready(pop!=NULL))return;ck("MISSING_DLL_REJECTED",1);closebox(pop);break;
case 12:if(!ready(!IsWindow(pop)))return;ck("MISSDLL_DIRS",samecwd());ck("MISSEXE_LAUNCH",WinExec("C:\\MISSEXE\\CDSTART.EXE",SW_SHOWNORMAL)>=32);break;
case 13:pop=FindWindow(NULL,"CDSTART");if(!ready(pop!=NULL))return;ck("MISSING_EXE_REJECTED",1);closebox(pop);break;
case 14:if(!ready(!IsWindow(pop)))return;ck("MISSEXE_DIRS",samecwd());ck("NO_DEMO_OR_DLL",FindWindow("CDTESTCLASS",NULL)==NULL&&GetModuleHandle("COMMDLG")==NULL);phase=99;return;
case 99:val("FAILURES",failed);val("COMPLETE",1);KillTimer(w,1);ExitWindows(0L,0);return;
}phase++;}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM p,LPARAM l){if(m==WM_TIMER){tick(w);Yield();return 0;}return DefWindowProc(w,m,p,l);}
int PASCAL WinMain(HINSTANCE a,HINSTANCE b,LPSTR c,int d){WNDCLASS wc;HWND w;MSG msg;HFILE f;if(c[0]=='D'){prefix[0]='D';drive=4;}lstrcpy(start,prefix);lstrcat(start,"CDSTART.EXE");lstrcpy(roundpath,prefix);lstrcat(roundpath,"CDROUND.TXT");f=_lcreat("C:\\STARTQA.LOG",0);_lclose(f);wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=a;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="STARTQA";if(!RegisterClass(&wc))return 1;w=CreateWindow("STARTQA","",WS_POPUP,0,0,1,1,NULL,NULL,a,NULL);SetTimer(w,1,500,NULL);while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return 0;}
