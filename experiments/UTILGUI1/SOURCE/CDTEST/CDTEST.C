#define WINVER 0x0300
#include <windows.h>
#include <stddef.h>
#include <direct.h>
#include "CDTEST.H"
static HINSTANCE instance;
static HWND rootWindow;
static FARPROC clockThunk;
static UINT clockId;
static HFILE logFile=HFILE_ERROR;
static int diagnostic;
static char result[32]="File > Open";
static HWND pathWindow;
static char selectedPath[144];
/* Win3.0 has no ES_READONLY. A native list shows bounded wrapped path rows. */
static void pathRows(void){RECT r;int cols,i,n,j;char row[144];
 if(!pathWindow)return;GetClientRect(pathWindow,&r);
 cols=(r.right-GetSystemMetrics(SM_CXVSCROLL)-4)/8;if(cols<1)cols=1;if(cols>143)cols=143;
 SendMessage(pathWindow,LB_RESETCONTENT,0,0L);n=lstrlen(selectedPath);
 for(i=0;i<n;i+=cols){for(j=0;j<cols&&i+j<n;j++)row[j]=selectedPath[i+j];row[j]=0;SendMessage(pathWindow,LB_ADDSTRING,0,(LONG)(LPSTR)row);}
}
static void showPath(char *s){lstrcpy(selectedPath,s);pathRows();}
static int failures,checks,automated,autoStep,tickBusy;
static char logPath[144], savedPath[144];
static char payload[]="COMMDLG30 independent caller round-trip\r\n";
static void line(char *s) { if(logFile==HFILE_ERROR)return;_lwrite(logFile,(LPSTR)s,lstrlen(s));_lwrite(logFile,"\r\n",2); _lclose(logFile);logFile=_lopen(logPath,OF_WRITE);_llseek(logFile,0L,2); }
static void check(int ok,char *s) { if(!diagnostic)return;++checks;if(!ok)++failures;_lwrite(logFile,ok?"PASS ":"FAIL ",5);line(s); }
static void clear(void FAR *v,unsigned n) { BYTE FAR *b=v;while(n--)*b++=0; }
static void init(OFNTEST FAR *o,LPSTR file,DWORD capacity) {
 clear(o,sizeof(*o));o->lStructSize=sizeof(*o);o->lpstrFile=file;
 o->nMaxFile=capacity;o->lpstrFilter="Text\0*.TXT\0All\0*.*\0\0";
 o->nFilterIndex=1;o->lpstrDefExt="TXT";
}
static void tests(void) {
 struct { WORD before; char text[32]; WORD after; } guard;
 OFNTEST o; HGLOBAL ho,hb; OFNTEST FAR *fo; BYTE FAR *fb;
 unsigned sp1,sp2,ds1,ds2; int rc,i; BOOL ret;
 line("BEGIN independent historical COMMDLG.LIB tests");
 {char metric[100];HDC dc=GetDC(NULL);wsprintf(metric,"RUNTIME %u x %u colors=%u flags=%lu",GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),GetDeviceCaps(dc,NUMCOLORS),GetWinFlags());ReleaseDC(NULL,dc);line(metric);check(!(GetWinFlags()&(WF_PMODE|WF_STANDARD|WF_ENHANCED)),"Windows real mode verified by GetWinFlags");}
 check(sizeof(OFNTEST)==72,"OPENFILENAME sizeof=72");
 check(offsetof(OFNTEST,lpstrFile)==24 && offsetof(OFNTEST,Flags)==48 && offsetof(OFNTEST,lpfnHook)==64,"OPENFILENAME offsets");
 guard.before=0xA55A;guard.after=0x5AA5;
 for(i=0;i<32;i++)guard.text[i]='!';
 _asm { mov sp1,sp }
 _asm { mov ds1,ds }
 rc=GetFileTitle("C:\\TEST\\ONE.TXT",guard.text,32);
 _asm { mov sp2,sp }
 _asm { mov ds2,ds }
 check(rc==0 && lstrcmp(guard.text,"ONE.TXT")==0,"GetFileTitle large buffer");
 check(sp1==sp2 && ds1==ds2,"FAR Pascal stack/DS preserved");
 check(guard.before==0xA55A && guard.after==0x5AA5,"FileTitle canaries");
 for(i=0;i<32;i++)guard.text[i]='!';
 rc=GetFileTitle("C:\\TEST\\ONE.TXT",guard.text,7);
 check(rc==8,"FileTitle short buffer reports 8 including NUL");
 check(guard.text[7]=='!' && guard.before==0xA55A && guard.after==0x5AA5,"short output no overwrite beyond capacity");
 rc=GetFileTitle("C:\\TEST\\ONE.TXT",guard.text,8);
 check(rc==0 && lstrcmp(guard.text,"ONE.TXT")==0 && guard.text[8]=='!',"FileTitle exact capacity");
 check(GetFileTitle("CON.TXT",guard.text,32)<0,"DOS device rejected");
 check(GetFileTitle("",guard.text,32)<0,"FileTitle empty rejected");
 check(GetFileTitle("C:\\TEST\\*.TXT",guard.text,32)<0,"FileTitle wildcard rejected");
 check(GetFileTitle("C:\\TEST\\",guard.text,32)<0,"FileTitle directory rejected");
 check(GetFileTitle("C:\\TEST\\BAD NAME",guard.text,32)<0,"FileTitle DOS space rejected");
 check(GetFileTitle("C:\\TEST\\[X].TXT",guard.text,32)<0,"FileTitle bracket rejected");
 for(i=0;i<16;i++) {
  init(&o,guard.text,32);o.lStructSize=71;
  ret=GetOpenFileName(&o);
  check(ret==FALSE && CommDlgExtendedError()==1L,"Open bad-size/error repeated");
  o.lStructSize=73;ret=GetSaveFileName(&o);
  check(ret==FALSE && CommDlgExtendedError()==1L,"Save bad-size/error repeated");
  rc=GetFileTitle("OK.TXT",guard.text,32);
  check(rc==0 && CommDlgExtendedError()==0L,"success clears error per 1992 SDK");
 }
 init(&o,guard.text,32);o.Flags=0x200L;
 check(!GetOpenFileName(&o) && CommDlgExtendedError()==2L,"unsupported multiselect fails explicitly");
 init(&o,guard.text,32);o.Flags=0x20L;
 check(!GetOpenFileName(&o) && CommDlgExtendedError()==2L,"hook request fails explicitly");
 init(&o,guard.text,32);o.Flags=0x40L;
 check(!GetSaveFileName(&o) && CommDlgExtendedError()==2L,"template request fails explicitly");
 ho=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,sizeof(OFNTEST));
 hb=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,64);
 check(ho!=NULL && hb!=NULL,"separate far allocations");
 if(ho && hb){
  fo=(OFNTEST FAR *)GlobalLock(ho);fb=(BYTE FAR *)GlobalLock(hb);
  if(fo && fb){
   fb[0]=0xA5;fb[63]=0x5A;
   init(fo,(LPSTR)(fb+1),62);fo->lStructSize=0;
   check(!GetOpenFileName(fo) && CommDlgExtendedError()==1L,"far structure rejected safely");
   check(GetFileTitle("C:\\X\\FAR.TXT",(LPSTR)(fb+1),62)==0 && lstrcmp((LPSTR)(fb+1),"FAR.TXT")==0,"separate segment output");
   check(fb[0]==0xA5 && fb[63]==0x5A,"far output canaries");
  } else check(0,"far allocations lock");
  GlobalUnlock(ho);GlobalUnlock(hb);
 }
 if(ho)GlobalFree(ho);if(hb)GlobalFree(hb);
 line(failures?"UNIT RESULT FAIL":"UNIT RESULT PASS");
}
static void dialog(HWND w,int action) {
 struct { WORD pre; char file[144]; WORD post; } b;
 OFNTEST o; char cwd[144],after[144],readbuf[64]; char title[32];
 BOOL ok; HFILE f; int n,closed; DWORD err;
 b.pre=0xA55A;b.post=0x5AA5;b.file[0]=0;title[0]=0;
 if(action==102)lstrcpy(b.file,"CDROUND.TXT");
 if(action==103 && savedPath[0])lstrcpy(b.file,savedPath);
 init(&o,b.file,144);o.hwndOwner=w;o.lpstrFileTitle=title;o.nMaxFileTitle=32;
 o.Flags=0x8L|0x4L|0x800L;
 if(action==102)o.Flags|=0x2L;else o.Flags|=0x1000L;
 o.lpstrTitle=action==102?"Save sample":action==104?"Try Cancel":"Open file";
 cwd[0]=0;getcwd(cwd,144);
 ok=action==102?GetSaveFileName(&o):GetOpenFileName(&o);err=CommDlgExtendedError();
 after[0]=0;getcwd(after,144);
 check(b.pre==0xA55A && b.post==0x5AA5,"UI output canaries");
 check(lstrcmp(cwd,after)==0,"NOCHANGEDIR restores cwd");
 if(!ok){lstrcpy(result,err?"Selection failed":"Cancelled");showPath("");InvalidateRect(w,NULL,TRUE);check(err==0L,"UI Cancel distinguished from failure");line("UI returned FALSE");if(automated)PostMessage(w,WM_COMMAND,105,0L);return;}
 lstrcpy(result,"Selected file");showPath(b.file);
 check(err==0L,"UI success clears error");line(b.file);
 check(o.nFileOffset<(UINT)lstrlen(b.file) && lstrcmp(b.file+o.nFileOffset,title)==0,"filename offset/title output");
 if(action==102){
  lstrcpy(result,"Save failed");f=_lcreat(b.file,0);check(f!=HFILE_ERROR,"caller creates selected output");
  if(f!=HFILE_ERROR){n=_lwrite(f,payload,lstrlen(payload));closed=_lclose(f);check(n==lstrlen(payload),"caller writes full payload");check(closed==0,"caller closes saved sample");if(n==lstrlen(payload)&&closed==0){lstrcpy(savedPath,b.file);lstrcpy(result,"Saved sample");}}
 }else if(action==103){
  lstrcpy(result,"Read failed");f=_lopen(b.file,OF_READ);check(f!=HFILE_ERROR,"caller opens selected file");
  if(f!=HFILE_ERROR){clear(readbuf,64);n=_lread(f,readbuf,63);closed=_lclose(f);check(n==lstrlen(payload) && lstrcmp(readbuf,payload)==0,"caller real file round-trip");check(closed==0,"caller closes read sample");if(n>=0&&closed==0)lstrcpy(result,n==lstrlen(payload)&&!lstrcmp(readbuf,payload)?"Sample matches":"Content differs");}
 }
 InvalidateRect(w,NULL,TRUE);if(automated)PostMessage(w,WM_COMMAND,action==102?103:104,0L);
}

static int scenario=-1,driveStep,prompts,question;
static char chosen[128];
static int focusOK,openOK,cancelOK;
static char lockedPath[]="C:\\CDCASE\\LOCKED.TXT";
static void lockfile(void){_asm {mov dx,offset lockedPath}; _asm {mov cx,1}; _asm {mov ax,4301h}; _asm {int 21h};}
static BOOL filedlg(HWND w){char cls[16];HWND e=GetDlgItem(w,100);if(!e)return FALSE;GetClassName(e,cls,16);return lstrcmpi(cls,"Edit")==0;}
static void dlgkey(HWND w,int id){HWND b;if(id==IDCANCEL){PostMessage(w,WM_KEYDOWN,VK_ESCAPE,1L);PostMessage(w,WM_KEYUP,VK_ESCAPE,0xC0000001L);}else{b=GetDlgItem(w,id);PostMessage(w,WM_NEXTDLGCTL,(WPARAM)b,1L);PostMessage(b,WM_KEYDOWN,VK_RETURN,1L);PostMessage(b,WM_KEYUP,VK_RETURN,0xC0000001L);}}
static void drive(HWND root) {
 HWND a=GetActiveWindow();int id;RECT r;
 if(!IsWindowVisible(a))return;
 if(a==root)return;
 if(filedlg(a)) {
  /* A timer can run while native control creation is still yielding. */
  if(!GetDlgItem(a,IDOK)||!GetDlgItem(a,IDCANCEL)||!GetDlgItem(a,102))return;
  if(driveStep==0) {
   driveStep=1;focusOK=GetFocus()==GetDlgItem(a,100);
   GetWindowRect(GetDlgItem(a,IDOK),&r);openOK=r.left>=0&&r.top>=0&&r.right<=GetSystemMetrics(SM_CXSCREEN)&&r.bottom<=GetSystemMetrics(SM_CYSCREEN);
   GetWindowRect(GetDlgItem(a,IDCANCEL),&r);cancelOK=r.left>=0&&r.top>=0&&r.right<=GetSystemMetrics(SM_CXSCREEN)&&r.bottom<=GetSystemMetrics(SM_CYSCREEN);
   if(scenario==0||scenario==14){dlgkey(a,IDCANCEL);driveStep=1;return;}
   if(scenario==4){PostMessage(GetDlgItem(a,102),CB_SETCURSEL,1,0L);PostMessage(a,WM_COMMAND,102,MAKELONG(GetDlgItem(a,102),CBN_SELCHANGE));}
   PostMessage(GetDlgItem(a,100),WM_SETTEXT,0,(LONG)(LPSTR)(scenario==11?"C:\\CDCASE":chosen));
   dlgkey(a,IDOK);driveStep=1;
  } else if(scenario==11&&driveStep==1){PostMessage(GetDlgItem(a,100),WM_SETTEXT,0,(LONG)(LPSTR)"ROUND.TXT");dlgkey(a,IDOK);driveStep=3;}
  else if(driveStep==2){dlgkey(a,IDCANCEL);driveStep=3;}
 } else {
  prompts++;if(GetDlgItem(a,IDYES))question=1;id=scenario==7||scenario==9||scenario==17?IDYES:scenario==8?IDNO:IDOK;
  dlgkey(a,id);if(scenario!=7&&scenario!=9&&scenario!=17)driveStep=2;
 }
}
void FAR PASCAL ClockProc(HWND ignored,UINT message,UINT id,DWORD tick) {
 HWND a;if(tickBusy)return;tickBusy=1;
 if(scenario>=0)drive(rootWindow);
 else if(automated){a=GetActiveWindow();if(a!=rootWindow&&filedlg(a))PostMessage(a,WM_COMMAND,autoStep==104?IDCANCEL:IDOK,0L);}
 tickBusy=0;
}
static int nextCase;
static void suite(HWND w) {
 struct {WORD pre;char file[256];WORD post;} g;
 struct {WORD pre;char title[32];WORD post;} t;
 OFNTEST o;char cwd[144],after[144],dcwd[144],dafter[144],readbuf[64],linebuf[100];
 BOOL ok;DWORD err;UINT cap,expected=21,sp1,sp2,ds1,ds2;int k,i;HFILE f;
 /* Exact expected path: C:\CDCASE\ROUND.TXT, 19 characters plus NUL. */
 expected=lstrlen("C:\\CDCASE\\ROUND.TXT")+1;lockfile();
 k=nextCase++;if(k<27) {
  scenario=k;driveStep=prompts=question=0;focusOK=openOK=cancelOK=-1;
  wsprintf(linebuf,"BEGIN UI CASE %d",k);line(linebuf);
  g.pre=0xA55A;g.post=0x5AA5;t.pre=0xC33C;t.post=0x3CC3;
  for(i=0;i<256;i++)g.file[i]='!';g.file[0]=0;for(i=0;i<32;i++)t.title[i]='!';
  cap=k==3?2:k==12?1:k==4?expected:128;init(&o,g.file,cap);
  o.hwndOwner=w;o.lpstrInitialDir="C:\\CDCASE";o.lpstrTitle="Bounded dialog";
  o.lpstrFileTitle=t.title;o.nMaxFileTitle=k==5?3:32;
  o.Flags=0x8L|0x800L|0x4L;
  lstrcpy(chosen,"ROUND.TXT");
  if(k==1)lstrcpy(chosen,"ROUND");
  if(k==2||k==6||k==10||k==11)o.Flags|=0x1000L;
  if(k==5)lstrcpy(chosen,"OTHER.BIN");
  if(k==6)lstrcpy(chosen,"MISSING.TXT");
  if(k==7||k==8)o.Flags|=0x2L;
  if(k==9){lstrcpy(chosen,"CREATE.TXT");o.Flags|=0x2000L;}
  if(k==10){lstrcpy(chosen,"LOCKED.TXT");o.Flags|=0x8000L;}
  if(k==11)o.lpstrInitialDir="C:\\";
  if(k==13||k==14)o.lpstrInitialDir="D:\\THERE";
  if(k==15)o.lpstrInitialDir="D:\\MISSING";
  if(k==16)lstrcpy(g.file,"D:\\THERE\\INITIAL.TXT");
  if(k==17){lstrcpy(chosen,"NEWOPEN.TXT");o.Flags|=0x1000L|0x2000L;}
  if(k==18){lstrcpy(chosen,"C:\\MISSING\\NEW.TXT");o.Flags=0x200cL;}
  if(k==19||k==20){o.lpstrInitialDir="E:\\";o.Flags|=0x8000L;lstrcpy(chosen,k==19?"MEDIA.TXT":"NEW.TXT");if(k==19)o.Flags|=0x1000L;}
  if(k==21){lstrcpy(chosen,"PLAIN");o.lpstrDefExt=NULL;o.Flags|=0x1000L;}
  if(k==22){lstrcpy(chosen,"PLAIN.");o.Flags|=0x1000L;}
  if(k==23){o.lpstrDefExt="";o.Flags|=0x400L;}
  if(k==24){o.lpstrDefExt=NULL;o.Flags|=0x400L;}
  if(k==25)o.Flags|=0x8000L|0x1000L;
  if(k==26){o.Flags|=0x8000L;lstrcpy(chosen,"WRITEOK.TXT");}
  getcwd(cwd,144);_getdcwd(4,dcwd,144);
  _asm {mov sp1,sp};_asm {mov ds1,ds};
  ok=(k>=17||k==2||k==6||k==10||k==11||k==0)?GetOpenFileName(&o):GetSaveFileName(&o);err=CommDlgExtendedError();_asm {mov sp2,sp};_asm {mov ds2,ds};getcwd(after,144);_getdcwd(4,dafter,144);
  if(k!=15){check(focusOK==1,"initial keyboard focus is filename edit");check(openOK==1,"Open/Save button within screen");check(cancelOK==1,"Cancel button within screen");}
  check(lstrcmp(dcwd,dafter)==0,"restores inactive drive working directory");
  check(sp1==sp2&&ds1==ds2,"UI FAR Pascal stack and DS preserved");
  check(g.pre==0xA55A&&g.post==0x5AA5&&g.file[cap]=='!',"selected-file outer and capacity canaries");
  check(t.pre==0xC33C&&t.post==0x3CC3,"file-title outer canaries");
  check(lstrcmp(cwd,after)==0,"restores cwd after each UI outcome");
  if(k==0||k==6||k==8||k==10||k==14||k==18||k==19||k==20){check(!ok&&err==0L,"cancel has error zero");if(k!=0&&k!=14)check(prompts>0,"validation/prompt appeared");if(k==18)check(!question,"missing CREATEPROMPT path never asks to create");goto next_case;}
  if(k==15){check(!ok&&err==0x3002L,"bad initial directory has documented error");goto next_case;}
  if(k==3||k==12){check(!ok&&err==0x3003L,"tiny selected-file reports buffer too small");if(k==3)check(*(WORD *)g.file==expected,"tiny file reports required NUL-inclusive bytes");else check(g.file[0]==0,"one-byte file buffer remains NUL");goto next_case;}
  check(ok&&err==0L,"selected-file success");if(!ok)goto next_case;
  check(o.nFileOffset<(UINT)lstrlen(g.file)&&o.nFileExtension<=(UINT)lstrlen(g.file),"offsets within selected path");
  if(k!=5)check(lstrcmp(g.file+o.nFileOffset,t.title)==0,"title and file offset agree");
  if(k==13||k==16)check(g.file[0]=='D'&&g.file[1]==':',"drive selection and initial file path");
  if(k==17)check(question&&prompts==1,"FILEMUSTEXIST with CREATEPROMPT can confirm new file");
  if(k==21)check(o.nFileExtension==(UINT)lstrlen(g.file),"no extension offset is terminating NUL");
  if(k==22)check(o.nFileExtension==0&&!(o.Flags&0x400L),"explicit trailing period suppresses default extension");
  if(k==23)check(!(o.Flags&0x400L),"empty default acts like NULL in this subset");
  if(k==24)check(!(o.Flags&0x400L),"NULL default clears stale extension-different flag");
  if(k==25||k==26)check(ok,"NOREADONLYRETURN permits writable Open selection");
  if(k==4)check(o.nFilterIndex==2L,"one-based filter index changes");
  if(k==5){check((o.Flags&0x400L)!=0,"extension-different output flag");check(t.title[0]=='O'&&t.title[1]=='T'&&t.title[2]==0&&t.title[3]=='!',"tiny title truncates with NUL and capacity canary");}
  if(k==7||k==9)check(prompts==1,"overwrite/create confirmation appears once");
  if(k==1){f=_lcreat(g.file,0);check(f!=HFILE_ERROR,"new selection creates real file");if(f!=HFILE_ERROR){check(_lwrite(f,payload,lstrlen(payload))==(UINT)lstrlen(payload),"round-trip write");_lclose(f);}}
  if(k==2){f=_lopen(g.file,OF_READ);check(f!=HFILE_ERROR,"open selected real file");if(f!=HFILE_ERROR){clear(readbuf,64);i=_lread(f,readbuf,63);_lclose(f);check(i==lstrlen(payload)&&lstrcmp(readbuf,payload)==0,"round-trip read matches");}}
 next_case:
  scenario=-1;PostMessage(w,WM_USER+9,0,0L);return;
 }
 scenario=-1;
 init(&o,g.file,128);o.lStructSize=1;GetOpenFileName(&o);
 check(CommDlgExtendedError()==1L,"parent task has independent error");
 check(WinExec("C:\\CDTEST.EXE /A",SW_SHOW)>=32,"start second caller task");
 for(i=0;i<32;i++)Yield();
 check(CommDlgExtendedError()==1L,"second caller does not clear parent error");
 line(failures?"SUITE FAIL":"SUITE PASS");DestroyWindow(w);
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HDC dc;PAINTSTRUCT ps;HWND a;
 switch(m){
 case WM_CREATE:pathWindow=CreateWindow("LISTBOX","",WS_CHILD|WS_VISIBLE|WS_BORDER|WS_VSCROLL|LBS_NOINTEGRALHEIGHT,2,22,138,60,w,(HMENU)201,instance,NULL);if(!pathWindow)return -1;SendMessage(pathWindow,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);return 0;
 case WM_SIZE:MoveWindow(pathWindow,2,22,LOWORD(lp)>4?LOWORD(lp)-4:1,HIWORD(lp)>24?HIWORD(lp)-24:1,TRUE);pathRows();return 0;
 case WM_PAINT:dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));TextOut(dc,2,4,result,lstrlen(result));EndPaint(w,&ps);return 0;
 case WM_USER+9:suite(w);return 0;
 case WM_TIMER:if(scenario>=0){drive(w);return 0;}a=GetActiveWindow();if(a!=w&&filedlg(a)){PostMessage(a,WM_COMMAND,autoStep==104?IDCANCEL:IDOK,0L);}return 0;
 case WM_COMMAND:autoStep=wp;if(wp>=101 && wp<=104)dialog(w,wp);else if(wp==105)DestroyWindow(w);return 0;
 case WM_DESTROY:if(clockId)KillTimer(NULL,clockId);line(failures?"FINAL FAIL":"FINAL PASS");if(logFile!=HFILE_ERROR)_lclose(logFile);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;HMENU menu,pop;MSG msg;int i,n; instance=inst;
 /* Windows 3.0 defaults to only eight queued messages. */
 for(i=64;i>=8;i/=2)if(SetMessageQueue(i))break;
 if(i<8)return 4;
 diagnostic=cmd[0]=='/'&&(cmd[1]=='A'||cmd[1]=='a'||cmd[1]=='B'||cmd[1]=='b'||cmd[1]=='C'||cmd[1]=='c');
 if(diagnostic){GetModuleFileName(inst,logPath,sizeof(logPath));n=lstrlen(logPath);
 for(i=n-1;i>=0 && logPath[i]!='\\' && logPath[i]!=':';i--);logPath[i+1]=0;
 lstrcat(logPath,prev?"CDTEST2.LOG":"CDTEST.LOG");logFile=_lcreat(logPath,0);
 if(logFile==HFILE_ERROR)return 3;tests();}
 if(cmd[0]=='/' && (cmd[1]=='A'||cmd[1]=='a')){_lclose(logFile);return failures?1:0;}
 if(!prev){clear(&wc,sizeof(wc));wc.lpfnWndProc=WndProc;wc.hInstance=inst;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszClassName="CDTESTCLASS";if(!RegisterClass(&wc))return 2;}
 menu=CreateMenu();pop=CreatePopupMenu();AppendMenu(pop,MF_STRING,101,"&Open...");AppendMenu(pop,MF_STRING,102,"&Save sample...");AppendMenu(pop,MF_STRING,103,"&Read sample...");AppendMenu(pop,MF_STRING,104,"Try &Cancel...");AppendMenu(pop,MF_STRING,105,"E&xit");AppendMenu(menu,MF_POPUP,(UINT)pop,"&File");
 w=CreateWindow("CDTESTCLASS","Dialogs",WS_OVERLAPPEDWINDOW|WS_CLIPCHILDREN,0,0,GetSystemMetrics(SM_CXSCREEN)<300?156:300,140,NULL,menu,inst,NULL);if(!w)return 2;rootWindow=w;ShowWindow(w,SW_SHOW);UpdateWindow(w);
 clockThunk=MakeProcInstance((FARPROC)ClockProc,inst);
 if(cmd[0]=='/'&&(cmd[1]=='B'||cmd[1]=='b')){automated=1;clockId=SetTimer(NULL,0,200,(TIMERPROC)clockThunk);PostMessage(w,WM_COMMAND,102,0L);}
 if(cmd[0]=='/'&&(cmd[1]=='C'||cmd[1]=='c')){clockId=SetTimer(NULL,0,200,(TIMERPROC)clockThunk);PostMessage(w,WM_USER+9,0,0L);}
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}FreeProcInstance(clockThunk);if(cmd[0]=='/'&&(cmd[1]=='B'||cmd[1]=='C'))ExitWindows(0L,0);return msg.wParam;
}
