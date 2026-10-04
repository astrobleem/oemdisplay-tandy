/* Optional TSHELL startup and exit orchestration. No hardware writes here.
   The selected one-shot owns PSG. Other startup entries wait until it unloads. */
#define WINVER 0x0300
#include <windows.h>
#include "TSBOOT.H"
#include "TNOTICE.H"
#include "PROGMENU.H"
static char config[144], soundDir[144];
static char loadList[1024], runList[1024];
static int begun, waiting, listed, warned, useExit;
static char chimeModule[12];
static int same(char *a,char *b) { return !lstrcmpi(a,b); }
static char *baseName(char *s) {
 char *b=s;while(*s){if(*s=='\\'||*s==':')b=s+1;s++;}return b;
}
static void status(HWND w,char *a,char *b) {
 char text[64];lstrcpy(text,a);lstrcat(text,"\n");lstrcat(text,b);
 TinyNotice(w,(HINSTANCE)GetWindowWord(w,GWW_HINSTANCE),"Start",text);
}
static void readConfig(void) {
 int n;GetWindowsDirectory(config,sizeof(config));lstrcat(config,"\\TSHELL.INI");
 n=GetPrivateProfileString("Sounds","Directory","C:\\TSTART",soundDir,sizeof(soundDir),config);
 if(n>=(int)sizeof(soundDir)-1)soundDir[0]=0;
 n=lstrlen(soundDir);if(n&&soundDir[n-1]=='\\')soundDir[n-1]=0;
 useExit=GetPrivateProfileInt("Sounds","ExitChime",0,config)!=0;
}
static int soundPath(char *file,char *path) {
 OFSTRUCT of;int i,n=lstrlen(soundDir);
 if(n<3||soundDir[1]!=':'||soundDir[2]!='\\'||n+lstrlen(file)+2>=128)return 0;
 for(i=0;i<n;i++)if(soundDir[i]==' '||soundDir[i]=='\t'||soundDir[i]=='"'||soundDir[i]=='/'||soundDir[i]=='*'||soundDir[i]=='?')return 0;
 lstrcpy(path,soundDir);lstrcat(path,"\\");lstrcat(path,file);
 return OpenFile(path,&of,OF_EXIST)!=HFILE_ERROR;
}
static int psgBusy(void) {
 HMODULE h;
 if(FindWindow("TandyPSGTest",NULL)||FindWindow("TandyStartupChime",NULL)||
    FindWindow("TandyXPStartupChime",NULL)||FindWindow("TandyAutomaticMouth",NULL)||
    FindWindow("TandyPreExitChime",NULL)||GetModuleHandle("TEXIT"))return 1;
 h=GetModuleHandle("SOUND");return h&&GetProcAddress(h,"DEBUGTIMER")!=NULL;
}
/* WIN.INI 3.0 run/load are space-separated filenames, not commands with args.
   Executables/PIFs are supported. Associated documents are reported as skipped. */
static void launchList(HWND w,char *p,int show) {
 char token[128],*b,*ext;int n,count=0;UINT r;
 while(*p){
  while(*p==' '||*p=='\t')p++;if(!*p)break;n=0;
  while(*p&&*p!=' '&&*p!='\t'){if(n<127)token[n++]=*p;p++;}
  token[n]=0;if(++count>64){warned=1;return;}
  if(!n||n>126){warned=1;continue;}
  b=baseName(token);
  if(same(b,"TCHIME.EXE")||same(b,"XPCHIME.EXE")||same(b,"TCHIME")||same(b,"XPCHIME"))continue;
  if(same(b,"TEXIT.EXE")||same(b,"TEXIT")||same(b,"TSHELL.EXE")||same(b,"TSHELL")){warned=1;continue;}
  ext=b;while(*ext&&*ext!='.')ext++;
  if(*ext&&!same(ext,".EXE")&&!same(ext,".COM")&&!same(ext,".BAT")&&!same(ext,".PIF")){warned=1;continue;}
  /* GRP-compatible launch helper supplies executable-directory behavior. */
  r=PmLaunchShow(w,token,show);if(r<32)warned=1;
 }
}
static void runLists(HWND w) {
 if(listed)return;listed=1;
 launchList(w,loadList,SW_SHOWMINNOACTIVE);launchList(w,runList,SW_SHOWNORMAL);
 if(warned)status(w,"Startup skipped.","See README.TXT.");
}
void TandyBootBegin(HWND w) {
 char choice[16],path[144];UINT r;int n;
 if(begun)return;begun=1;readConfig();loadList[0]=runList[0]=0;
 if(GetPrivateProfileInt("Startup","LoadRun",1,config)){
  n=GetProfileString("windows","load","",loadList,sizeof(loadList));if(n>=(int)sizeof(loadList)-1){loadList[0]=0;warned=1;}
  n=GetProfileString("windows","run","",runList,sizeof(runList));if(n>=(int)sizeof(runList)-1){runList[0]=0;warned=1;}
 }
 GetPrivateProfileString("Sounds","Startup","NONE",choice,sizeof(choice),config);
 chimeModule[0]=0;
 if(same(choice,"XP"))lstrcpy(chimeModule,"XPCHIME");
 else if(same(choice,"TANDY"))lstrcpy(chimeModule,"TCHIME");
 else if(!same(choice,"NONE")){warned=1;}
 if(!chimeModule[0]||psgBusy()){runLists(w);return;}
 if(!soundPath(same(choice,"XP")?"XPCHIME.EXE":"TCHIME.EXE",path)){warned=1;runLists(w);return;}
 /* No timer means we cannot serialize safely: skip sound, retain startup. */
 if(!SetTimer(w,BOOT_TIMER,110,NULL)){warned=1;runLists(w);return;}
 waiting=1;r=WinExec(path,SW_HIDE);
 if(r<32){waiting=0;KillTimer(w,BOOT_TIMER);warned=1;runLists(w);}
}
void TandyBootTick(HWND w) {
 if(!waiting)return;
 if(GetModuleHandle(chimeModule))return;
 waiting=0;KillTimer(w,BOOT_TIMER);runLists(w);
}
void TandyBootStop(HWND w) { waiting=0;listed=1;KillTimer(w,BOOT_TIMER); }
void TandyExit(HWND w,int silent) {
 char path[144];UINT r;readConfig();
 if(silent||!useExit){if(!ExitWindows(0L,0))status(w,"Exit canceled.","Windows stays.");return;}
 if(psgBusy()){status(w,"Sound is busy.","Use silent exit.");return;}
 if(!soundPath("TEXIT.EXE",path)){status(w,"No exit chime.","Use silent exit.");return;}
 if(lstrlen(path)+4>=(int)sizeof(path)){status(w,"Bad sound path.","Use silent exit.");return;}
 lstrcat(path," /go");r=WinExec(path,SW_SHOWNORMAL);
 if(r<32)status(w,"Chime failed.","Use silent exit.");
}

int TandyBootBusy(void) { return begun && (!listed || waiting); }
