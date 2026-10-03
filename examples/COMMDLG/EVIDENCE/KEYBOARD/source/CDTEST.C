/* Independent Win16 synthetic keyboard-message regression.
 * Real native controls and DialogBox message loops, no direct WM_COMMAND
 * except bounded failure recovery. This is not physical keyboard input.
 * Link only historical Microsoft COMMDLG.LIB, never implementation headers.
 */
#define WINVER 0x0300
#include <windows.h>
#include <stddef.h>
#include <direct.h>
#include "CDTEST.H"
static HINSTANCE instance;
static HWND rootWindow;
static FARPROC clockThunk;
static UINT clockId;
static HFILE logFile;
static int checks,failures,nextCase,scenario=-1,phase,ticks,busy,prompts;
static char logPath[144],savedPath[144];
static char payload[]="COMMDLG native keyboard message round-trip\r\n";
static void line(char *s){_lwrite(logFile,(LPSTR)s,lstrlen(s));_lwrite(logFile,"\r\n",2);_lclose(logFile);logFile=_lopen(logPath,OF_WRITE);_llseek(logFile,0L,2);}
static void check(int ok,char *s){++checks;if(!ok)++failures;_lwrite(logFile,ok?"PASS ":"FAIL ",5);line(s);}
static void clear(void FAR *v,unsigned n){BYTE FAR *p=v;while(n--)*p++=0;}
static void init(OFNTEST FAR *o,LPSTR file){clear(o,sizeof(*o));o->lStructSize=sizeof(*o);o->hwndOwner=rootWindow;o->lpstrFile=file;o->nMaxFile=144;o->lpstrFilter="Text\0*.TXT\0All\0*.*\0\0";o->nFilterIndex=1;o->lpstrDefExt="TXT";o->lpstrInitialDir="C:\\CDKEY";o->Flags=0x8L|0x800L|0x4L;o->lpstrTitle="Keyboard-message probe";}
static BOOL filedlg(HWND a){char c[16];HWND e=GetDlgItem(a,100);if(!e)return FALSE;GetClassName(e,c,16);return lstrcmpi(c,"Edit")==0;}
static void key(HWND target,UINT code){check(PostMessage(target,WM_KEYDOWN,code,1L),"posted native WM_KEYDOWN");check(PostMessage(target,WM_KEYUP,code,0xC0000001L),"posted native WM_KEYUP");}
static void drive(void){
 HWND a,e,f;char text[144],buf[100];DWORD sel;int i;
 if(scenario<0||busy)return;busy=1;++ticks;a=GetActiveWindow();
 if(ticks>150){
  if(ticks==151){check(0,"watchdog: keyboard flow did not finish within 150 timer ticks");wsprintf(buf,"WATCHDOG case=%d phase=%d active=%u focus=%u",scenario,phase,a,GetFocus());line(buf);}
  if(a!=rootWindow&&IsWindow(a))PostMessage(a,WM_COMMAND,IDCANCEL,0L);
  if(ticks>165){line("FINAL FAIL watchdog abort");_lclose(logFile);ExitWindows(0L,0);}
  busy=0;return;
 }
 if(a==rootWindow||!IsWindow(a)||!IsWindowVisible(a)){busy=0;return;}
 if(filedlg(a)){
  e=GetDlgItem(a,100);if(!GetDlgItem(a,IDOK)||!GetDlgItem(a,IDCANCEL)||!GetDlgItem(a,102)){busy=0;return;}
  if(phase==0){
   phase=1;f=GetFocus();check(f==e,"initial focus is native filename Edit");
   GetWindowText(e,text,144);
   if(scenario==2||scenario==4||scenario==6){
    check(text[0]!=0,"prefilled filename text is present");sel=SendMessage(e,EM_GETSEL,0,0L);
    wsprintf(buf,"SELECTION start=%u end=%u length=%u",LOWORD(sel),HIWORD(sel),lstrlen(text));line(buf);
    check(LOWORD(sel)==0&&HIWORD(sel)==(UINT)lstrlen(text),"prefilled filename selection covers zero through end");
   }else check(text[0]==0,"initially empty filename Edit");
   if(scenario==1){for(i=0;"KEYTEST"[i];i++)check(PostMessage(f,WM_CHAR,"KEYTEST"[i],1L),"posted native WM_CHAR");}
   else if(scenario==2||scenario==4)key(f,VK_RETURN);
   else if(scenario==3)key(f,VK_TAB);
   else key(f,VK_ESCAPE);
  }else if(scenario==1&&phase==1){
   phase=2;GetWindowText(e,text,144);check(lstrcmp(text,"KEYTEST")==0,"queued WM_CHAR typed KEYTEST in empty Save Edit");key(GetFocus(),VK_RETURN);
  }else if(scenario==3&&phase==1){
   phase=2;check(GetFocus()!=e&&GetParent(GetFocus())==a,"queued Tab moved focus to another dialog control");check(GetFocus()==GetDlgItem(a,101),"Tab from filename Edit selects native file ListBox");key(GetFocus(),VK_ESCAPE);
  }else if(scenario==4&&phase==2){
   phase=3;check(prompts==1,"Return accepted overwrite prompt default No and returned to file dialog");key(GetFocus(),VK_ESCAPE);
  }
 }else if(scenario==4&&phase==1&&GetDlgItem(a,IDYES)&&GetDlgItem(a,IDNO)){
  phase=2;++prompts;check(GetFocus()==GetDlgItem(a,IDNO),"overwrite prompt initial keyboard focus is No");
  check((GetWindowLong(GetDlgItem(a,IDNO),GWL_STYLE)&0xFL)==BS_DEFPUSHBUTTON,"overwrite No is default pushbutton");key(GetFocus(),VK_RETURN);
 }else if(scenario!=4&&ticks>10){
  check(0,"unexpected native prompt");PostMessage(a,WM_COMMAND,IDCANCEL,0L);
 }
 busy=0;
}
void FAR PASCAL ClockProc(HWND ignored,UINT message,UINT id,DWORD tick){drive();}
static void suite(void){
 struct {WORD before;char file[144];WORD after;} g;
 OFNTEST o;int k,n;BOOL ok;DWORD err;char cwd[144],after[144],readbuf[80],buf[128];HFILE f;UINT sp1,sp2,ds1,ds2;
 k=nextCase++;if(k>=9){wsprintf(buf,"SUMMARY checks=%u failures=%u",checks,failures);line(buf);line(failures?"SUITE FAIL":"SUITE PASS");DestroyWindow(rootWindow);return;}
 scenario=k;phase=ticks=prompts=0;wsprintf(buf,"BEGIN KEYBOARD CASE %d",k);line(buf);
 g.before=0xA55A;g.after=0x5AA5;clear(g.file,144);init(&o,g.file);
 if(k==2||k==4||k==6)lstrcpy(g.file,"KEYTEST.TXT");
 if(k==4)o.Flags|=0x2L;
 if(k!=1&&k!=4)o.Flags|=0x1000L;
 getcwd(cwd,144);_asm {mov sp1,sp};_asm {mov ds1,ds};
 ok=(k==1||k==4)?GetSaveFileName(&o):GetOpenFileName(&o);err=CommDlgExtendedError();
 _asm {mov sp2,sp};_asm {mov ds2,ds};
 scenario=-1;getcwd(after,144);check(sp1==sp2&&ds1==ds2,"FAR Pascal stack and DS preserved");check(g.before==0xA55A&&g.after==0x5AA5,"caller output canaries preserved");check(lstrcmp(cwd,after)==0,"NOCHANGEDIR restores caller cwd");
 if(k==1||k==2){
  check(ok&&err==0L,"keyboard Return accepts selected filename");
  check(lstrcmp(g.file,"C:\\CDKEY\\KEYTEST.TXT")==0,"selected path includes typed filename and default TXT extension");
  if(ok&&k==1){lstrcpy(savedPath,g.file);f=_lcreat(g.file,0);check(f!=HFILE_ERROR,"caller creates real selected file");if(f!=HFILE_ERROR){n=_lwrite(f,payload,lstrlen(payload));_lclose(f);check(n==lstrlen(payload),"caller writes full real payload");}}
  if(ok&&k==2){f=_lopen(g.file,OF_READ);check(f!=HFILE_ERROR,"caller opens real selected file");if(f!=HFILE_ERROR){clear(readbuf,80);n=_lread(f,readbuf,79);_lclose(f);check(n==lstrlen(payload)&&lstrcmp(readbuf,payload)==0,"real file read/write round-trip matches");}}
 }else{
  check(!ok&&err==0L,"queued Escape cancels with extended error zero");
  if(k==4){check(phase==3&&prompts==1,"overwrite Return chose No before Escape cancellation");f=_lopen(savedPath,OF_READ);check(f!=HFILE_ERROR,"original file still opens after overwrite No");if(f!=HFILE_ERROR){clear(readbuf,80);n=_lread(f,readbuf,79);_lclose(f);check(n==lstrlen(payload)&&lstrcmp(readbuf,payload)==0,"overwrite No preserves original payload");}}
 }
 wsprintf(buf,"END KEYBOARD CASE %d",k);line(buf);PostMessage(rootWindow,WM_USER+9,0,0L);
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){switch(m){case WM_USER+9:suite();return 0;case WM_DESTROY:if(clockId)KillTimer(NULL,clockId);line(failures?"FINAL FAIL":"FINAL PASS");_lclose(logFile);PostQuitMessage(0);return 0;}return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){
 WNDCLASS wc;MSG msg;int i,n;HDC dc;char buf[128];instance=inst;
 GetModuleFileName(inst,logPath,sizeof(logPath));n=lstrlen(logPath);for(i=n-1;i>=0&&logPath[i]!='\\'&&logPath[i]!=':';i--);logPath[i+1]=0;lstrcat(logPath,"CDTEST.LOG");logFile=_lcreat(logPath,0);if(logFile==HFILE_ERROR)return 3;
 line("BEGIN native Win16 SYNTHETIC KEYBOARD-MESSAGE probe (not physical keyboard input)");
 dc=GetDC(NULL);wsprintf(buf,"RUNTIME %u x %u colors=%u flags=%lu",GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),GetDeviceCaps(dc,NUMCOLORS),GetWinFlags());ReleaseDC(NULL,dc);line(buf);
 check(!(GetWinFlags()&(WF_PMODE|WF_STANDARD|WF_ENHANCED)),"Windows real mode");check(sizeof(OFNTEST)==72,"historical OPENFILENAME is 72 bytes");check(offsetof(OFNTEST,lpstrFile)==24&&offsetof(OFNTEST,Flags)==48&&offsetof(OFNTEST,lpfnHook)==64,"historical OPENFILENAME offsets");
 clear(&wc,sizeof(wc));wc.lpfnWndProc=WndProc;wc.hInstance=inst;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszClassName="CDKEYCLASS";if(!RegisterClass(&wc))return 2;
 rootWindow=CreateWindow("CDKEYCLASS","Key probe",WS_OVERLAPPEDWINDOW,0,0,140,100,NULL,NULL,inst,NULL);if(!rootWindow)return 2;ShowWindow(rootWindow,SW_SHOW);UpdateWindow(rootWindow);
 clockThunk=MakeProcInstance((FARPROC)ClockProc,inst);clockId=SetTimer(NULL,0,200,(TIMERPROC)clockThunk);check(clockThunk!=NULL&&clockId!=0,"native timer created");PostMessage(rootWindow,WM_USER+9,0,0L);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}FreeProcInstance(clockThunk);ExitWindows(0L,0);return failures?1:0;
}
