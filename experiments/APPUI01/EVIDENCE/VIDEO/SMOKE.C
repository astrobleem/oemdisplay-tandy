#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HFILE logf;static int failures,passes,app,stage;
static char *exes[]={"COOKIE","PINBALL","BRIGHT","GIFLOAD","TABOUT","SWAT","TSHELL"};
static char *classes[]={"CookieBench","TinyPinball","BrighterTomorrow","GifImport","TandyAbout","TandyFlySwat","TandyStart"};
static HWND child;static int busy;
static void check(char *s,int ok){char b[160];wsprintf(b,"%s %s %s\r\n",(LPSTR)(ok?"PASS":"FAIL"),(LPSTR)(app<7?exes[app]:"ALL"),(LPSTR)s);_lwrite(logf,b,lstrlen(b));if(ok)passes++;else failures++;}
static void typefield(HWND parent,int id,char *text) {
 HWND edit=GetDlgItem(parent,id);char actual[128];int i;
 check("edit control found",edit!=NULL);if(!edit)return;
 SendMessage(edit,EM_SETSEL,0,MAKELONG(0,32767));
 SendMessage(edit,WM_CLEAR,0,0L);
 for(i=0;text[i];i++)SendMessage(edit,WM_CHAR,(WPARAM)text[i],1L);
 SendMessage(edit,WM_GETTEXT,sizeof(actual),(LONG)(LPSTR)actual);
 check("typed field matches",!lstrcmp(actual,text));
}
static void shot(int n){char name[32];HFILE f;unsigned char m=*((unsigned char FAR *)0x00400049L);unsigned char FAR *v=(unsigned char FAR *)0xb8000000L;wsprintf(name,"C:\\%s%d.RAW",(LPSTR)exes[app],n);f=_lcreat(name,0);if(f!=HFILE_ERROR){_lwrite(f,(LPSTR)v,(m==9||m==10)?32768U:16384U);_lclose(f);}}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){char cmd[80];HWND d;RECT r;int x;HFILE hf;switch(m){case WM_CREATE:SetTimer(w,1,300,NULL);return 0;case WM_TIMER:
 if(busy)return 0;busy=1;
 if(app==7){KillTimer(w,1);wsprintf(cmd,"PASS_COUNT=%d\r\nFAIL_COUNT=%d\r\nCOMPLETE=1\r\n",passes,failures);_lwrite(logf,cmd,lstrlen(cmd));_lclose(logf);DestroyWindow(w);ExitWindows(0L,0);return 0;}
 if(stage==0){wsprintf(cmd,"C:\\%s.EXE",(LPSTR)exes[app]);check("WinExec accepted",WinExec(cmd,SW_SHOWNORMAL)>=32);}
 else if(stage==1){child=FindWindow(classes[app],NULL);check("production window created",child!=NULL);if(child){UpdateWindow(child);shot(0);switch(app){
 case 0:SendMessage(child,WM_KEYDOWN,VK_SPACE,0L);UpdateWindow(child);shot(2);break;
 case 1:SendMessage(child,WM_KEYDOWN,VK_SPACE,0L);SendMessage(child,WM_KEYDOWN,'P',0L);break;
 case 2:SendMessage(child,WM_COMMAND,100,0L);break;
 case 3:SendMessage(child,WM_COMMAND,104,0L);check("open before conversion stays",IsWindow(child));typefield(child,101,"C:\\TEST.GIF");typefield(child,102,"C:\\SMOKE.BMP");SendMessage(child,WM_COMMAND,103,0L);hf=_lopen("C:\\SMOKE.BMP",OF_READ);check("named conversion output exists",hf!=HFILE_ERROR);if(hf!=HFILE_ERROR)_lclose(hf);break;
 case 4:SendMessage(child,WM_COMMAND,103,0L);hf=_lopen("C:\\SMOKE.BMP",OF_READ);check("named conversion output exists",hf!=HFILE_ERROR);if(hf!=HFILE_ERROR)_lclose(hf);break;
 case 5:GetClientRect(child,&r);x=(r.right-148)/2;SendMessage(child,WM_LBUTTONDOWN,0,MAKELONG(x+70,90));SendMessage(child,WM_LBUTTONDOWN,0,MAKELONG(x+6,34));break;
 case 6:PostMessage(child,WM_COMMAND,42,0L);break;
 }}}
 else if(stage==2){if(child){UpdateWindow(child);shot(1);if(app==3){typefield(child,102,"C:\\OTHER.BMP");SendMessage(child,WM_COMMAND,104,0L);check("edited output stays",IsWindow(child));typefield(child,102,"C:\\FINAL.BMP");SendMessage(child,WM_COMMAND,103,0L);SendMessage(child,WM_COMMAND,104,0L);check("successful Open closes helper",!IsWindow(child));}if(app==6){d=FindWindow(NULL,"Run");check("Run dialog",d!=NULL);if(d){typefield(d,100,"C:\\NOAPP.EXE");SendMessage(d,WM_COMMAND,IDOK,0L);UpdateWindow(d);shot(2);}}}}
 else if(stage==3){if(app==3){d=FindWindow("pbParent",NULL);check("Paintbrush opened output",d!=NULL);if(d){GetWindowText(d,cmd,sizeof(cmd));check("Paintbrush title names output",strstr(cmd,"FINAL.BMP")!=NULL);UpdateWindow(d);shot(3);PostMessage(d,WM_CLOSE,0,0L);}}if(app==6){d=FindWindow(NULL,"Run");if(d)PostMessage(d,WM_COMMAND,IDCANCEL,0L);}}
 else if(stage==4){if(child)PostMessage(child,WM_CLOSE,0,0L);}
 else if(stage==5){check("ordinary close returns",!IsWindow(child));if(app==3)check("Paintbrush close returns",!FindWindow("pbParent",NULL));app++;stage=-1;}
 stage++;busy=0;return 0;
 case WM_DESTROY:PostQuitMessage(0);return 0;}return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;HWND w;MSG msg;logf=_lcreat("C:\\SMOKE.LOG",0);check("real mode",!(GetWinFlags()&WF_PMODE));wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="PolishSmoke";if(!RegisterClass(&wc))return 1;w=CreateWindow("PolishSmoke","",WS_POPUP,0,0,1,1,NULL,NULL,inst,NULL);if(!w)return 1;while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return failures;}
