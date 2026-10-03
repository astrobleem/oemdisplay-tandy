/* Focused native Win3.0 keyboard message diagnosis; DLL remains unmodified. */
#define WINVER 0x0300
#include <windows.h>
#include <stddef.h>
#include <direct.h>
#include "CDTEST.H"
static HWND rootWindow;
static FARPROC clockThunk;
static UINT clockId;
static HFILE logFile;
static int checks,failures,nextCase,scenario=-1,phase,ticks,busy,prompts,targetPrompt,charIndex,queueSize;
static char logPath[144];
static char *chosen;
static void line(char *s){_lwrite(logFile,(LPSTR)s,lstrlen(s));_lwrite(logFile,"\r\n",2);_lclose(logFile);logFile=_lopen(logPath,OF_WRITE);_llseek(logFile,0L,2);}
static void check(int ok,char *s){++checks;if(!ok)++failures;_lwrite(logFile,ok?"PASS ":"FAIL ",5);line(s);}
static void clear(void FAR *v,unsigned n){BYTE FAR *p=v;while(n--)*p++=0;}
static BOOL filedlg(HWND a){char c[16];HWND e=GetDlgItem(a,100);if(!e)return FALSE;GetClassName(e,c,16);return lstrcmpi(c,"Edit")==0;}
static void key(HWND target,UINT code){check(PostMessage(target,WM_KEYDOWN,code,1L),"posted WM_KEYDOWN");check(PostMessage(target,WM_KEYUP,code,0xC0000001L),"posted WM_KEYUP");}
static void trace(char *what,HWND a){char b[400],cls[32],title[64];cls[0]=title[0]=0;if(IsWindow(a)){GetClassName(a,cls,32);GetWindowText(a,title,64);}wsprintf(b,"TRACE %s case=%d phase=%d tick=%d active=%u focus=%u edit=%u class=%s title=%s",(LPSTR)what,scenario,phase,ticks,a,GetFocus(),GetDlgItem(a,100),(LPSTR)cls,(LPSTR)title);line(b);}
static void drive(void){
 HWND a,e;char text[144];
 if(scenario<0||busy)return;busy=1;++ticks;a=GetActiveWindow();
 if(ticks==1||ticks%20==0)trace("heartbeat",a);
 if(ticks>150){
  if(ticks==151){check(0,"bounded native timer watchdog");trace("watchdog",a);}
  if(a!=rootWindow&&IsWindow(a))PostMessage(a,WM_COMMAND,IDCANCEL,0L);
  if(ticks>165){line("FINAL FAIL watchdog abort");_lclose(logFile);ExitWindows(0L,0);}
  busy=0;return;
 }
 if(a==rootWindow||!IsWindow(a)||!IsWindowVisible(a)){busy=0;return;}
 if(filedlg(a)){
  e=GetDlgItem(a,100);if(!GetDlgItem(a,IDOK)||!GetDlgItem(a,IDCANCEL)||!GetDlgItem(a,102)){busy=0;return;}
  if(phase==0){
   trace("ready",a);check(GetFocus()==e,"initial keyboard focus is filename Edit");GetWindowText(e,text,144);check(text[0]==0,"filename Edit initially empty");
   if(scenario==0){phase=90;trace("queue Escape",a);key(GetFocus(),VK_ESCAPE);}
   else {phase=1;charIndex=0;}
  }else if(phase==1){
   if(chosen[charIndex]){check(PostMessage(e,WM_CHAR,chosen[charIndex++],1L),"posted one queued WM_CHAR");}
   else {GetWindowText(e,text,144);line(text);check(lstrcmp(text,chosen)==0,"queued WM_CHAR produced exact chosen filename");phase=2;trace("queue Return from Edit",a);key(GetFocus(),VK_RETURN);}
  }else if(phase==4){check(0,"Yes returned to file dialog without accepting");phase=91;key(GetFocus(),VK_ESCAPE);}
 }else if(scenario==17&&GetDlgItem(a,IDYES)&&GetDlgItem(a,IDNO)){
  if(phase==2){++prompts;trace("CREATEPROMPT observed",a);check(GetFocus()==GetDlgItem(a,IDNO),"create prompt initial focus is No");phase=3;check(PostMessage(a,WM_NEXTDLGCTL,(WPARAM)GetDlgItem(a,IDYES),1L),"queued native focus move to Yes");}
  else if(phase==3){trace("prompt Yes focus",a);check(GetFocus()==GetDlgItem(a,IDYES),"queued focus move selected prompt Yes");phase=4;trace("queue Return on Yes",a);key(GetFocus(),VK_RETURN);}
 }else if(ticks>10){trace("unexpected prompt",a);check(0,"unexpected native prompt");PostMessage(a,WM_COMMAND,IDCANCEL,0L);}
 busy=0;
}
void FAR PASCAL ClockProc(HWND ignored,UINT message,UINT id,DWORD tick){drive();}
static void suite(void){
 struct {WORD pre;char file[256];WORD post;} g;
 struct {WORD pre;char title[32];WORD post;} t;
 OFNTEST o;int k,i,n;BOOL ok;DWORD err;char cwd[144],after[144],buf[400];HFILE f;UINT sp1,sp2,ds1,ds2;
 k=nextCase++;if(k>=(targetPrompt?1:2)){wsprintf(buf,"SUMMARY checks=%u failures=%u",checks,failures);line(buf);line(failures?"SUITE FAIL":"SUITE PASS");DestroyWindow(rootWindow);return;}
 scenario=targetPrompt?17:k;phase=ticks=prompts=0;wsprintf(buf,"BEGIN FOCUSED CASE %d",scenario);line(buf);
 chosen=scenario==17?"NEWOPEN.TXT":"ROUND";
 g.pre=0xA55A;g.post=0x5AA5;t.pre=0xC33C;t.post=0x3CC3;
 for(i=0;i<256;i++)g.file[i]='!';g.file[0]=0;for(i=0;i<32;i++)t.title[i]='!';clear(&o,sizeof(o));
 o.lStructSize=sizeof(o);o.hwndOwner=rootWindow;o.lpstrFile=g.file;o.nMaxFile=128;o.lpstrFilter="Text\0*.TXT\0All\0*.*\0\0";o.nFilterIndex=1;o.lpstrDefExt="TXT";o.lpstrInitialDir="C:\\CDCASE";o.Flags=0x8L|0x800L|0x4L;o.lpstrTitle="Bounded dialog";o.lpstrFileTitle=t.title;o.nMaxFileTitle=32;
 if(scenario==17)o.Flags|=0x1000L|0x2000L;
 getcwd(cwd,144);_asm {mov sp1,sp};_asm {mov ds1,ds};
 ok=scenario==1?GetSaveFileName(&o):GetOpenFileName(&o);err=CommDlgExtendedError();
 _asm {mov sp2,sp};_asm {mov ds2,ds};
 getcwd(after,144);wsprintf(buf,"RETURN case=%d ok=%d error=%lu phase=%d prompts=%d path=%s",scenario,ok,err,phase,prompts,(LPSTR)g.file);line(buf);
 check(sp1==sp2&&ds1==ds2,"FAR Pascal stack and DS preserved");check(g.pre==0xA55A&&g.post==0x5AA5&&g.file[128]=='!',"file output capacity and outer canaries");check(t.pre==0xC33C&&t.post==0x3CC3,"title output outer canaries");check(lstrcmp(cwd,after)==0,"NOCHANGEDIR restores caller cwd");
 if(scenario==0)check(!ok&&err==0L,"queued Escape cancels with extended error zero");
 else{
  check(ok&&err==0L,"queued Return accepts selected filename");
  check(lstrcmp(g.file,scenario==17?"C:\\CDCASE\\NEWOPEN.TXT":"C:\\CDCASE\\ROUND.TXT")==0,"exact selected path with expected extension");
  check(o.nFileOffset<(UINT)lstrlen(g.file)&&lstrcmp(g.file+o.nFileOffset,t.title)==0,"title and file offset agree");
  if(scenario==17){check(prompts==1&&phase==4,"FILEMUSTEXIST plus CREATEPROMPT confirms new Open once");f=_lopen(g.file,OF_READ);check(f==HFILE_ERROR,"dialog selection does not create new file");if(f!=HFILE_ERROR)_lclose(f);}
  else if(ok){f=_lcreat(g.file,0);check(f!=HFILE_ERROR,"caller creates selected Save output");if(f!=HFILE_ERROR){n=_lwrite(f,"Focused native Save test\r\n",26);_lclose(f);check(n==26,"caller writes real Save output");}}
 }
 wsprintf(buf,"END FOCUSED CASE %d",scenario);line(buf);scenario=-1;PostMessage(rootWindow,WM_USER+9,0,0L);
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){switch(m){case WM_USER+9:suite();return 0;case WM_DESTROY:if(clockId)KillTimer(NULL,clockId);line(failures?"FINAL FAIL":"FINAL PASS");_lclose(logFile);PostQuitMessage(0);return 0;}return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){
 WNDCLASS wc;MSG msg;int i,n;HDC dc;char buf[128];targetPrompt=(cmd[0]=='/'&&cmd[1]=='P');
 for(i=32;i>=8;i/=2)if(SetMessageQueue(i))break;if(i<8)return 4;queueSize=i;
 GetModuleFileName(inst,logPath,sizeof(logPath));n=lstrlen(logPath);for(i=n-1;i>=0&&logPath[i]!='\\'&&logPath[i]!=':';i--);logPath[i+1]=0;lstrcat(logPath,"CDTEST.LOG");logFile=_lcreat(logPath,0);if(logFile==HFILE_ERROR)return 3;
 line("BEGIN focused native Win16 SYNTHETIC KEYBOARD-MESSAGE probe (not physical input)");
 dc=GetDC(NULL);wsprintf(buf,"RUNTIME %u x %u colors=%u flags=%lu queue=%d",GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),GetDeviceCaps(dc,NUMCOLORS),GetWinFlags(),queueSize);ReleaseDC(NULL,dc);line(buf);
 check(!(GetWinFlags()&(WF_PMODE|WF_STANDARD|WF_ENHANCED)),"Windows real mode");check(sizeof(OFNTEST)==72,"historical OPENFILENAME is 72 bytes");check(offsetof(OFNTEST,lpstrFile)==24&&offsetof(OFNTEST,Flags)==48&&offsetof(OFNTEST,lpfnHook)==64,"historical OPENFILENAME offsets");
 clear(&wc,sizeof(wc));wc.lpfnWndProc=WndProc;wc.hInstance=inst;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszClassName="CDFOCUSCLASS";if(!RegisterClass(&wc))return 2;
 rootWindow=CreateWindow("CDFOCUSCLASS","Focused probe",WS_OVERLAPPEDWINDOW,0,0,140,100,NULL,NULL,inst,NULL);if(!rootWindow)return 2;ShowWindow(rootWindow,SW_SHOW);UpdateWindow(rootWindow);
 clockThunk=MakeProcInstance((FARPROC)ClockProc,inst);clockId=SetTimer(NULL,0,200,(TIMERPROC)clockThunk);check(clockThunk!=NULL&&clockId!=0,"native timer created");PostMessage(rootWindow,WM_USER+9,0,0L);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}FreeProcInstance(clockThunk);ExitWindows(0L,0);return failures?1:0;
}
