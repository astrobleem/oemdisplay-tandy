#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <assert.h>
#include "windows.h"
static char *choice="XP",*dir="C:\\TSTART",*loads="",*runs="";
static int opts=1,exitopt=1,missing=0,timerok=1,busy=0,driver=1,live=0,exitLive=0,execfail=0,veto=0;
static int api=1,openapi=1,closeapi=1,soundBusy,claimFail,held,opens,closes;
static char*busyClass="TandyPSGTest";
static int execs,apps,exits,boxes,timer,appfail,mode[80];static char commands[80][144],last[180];
int lstrcmpi(const char*a,const char*b){return strcasecmp(a,b);}int lstrlen(const char*a){return strlen(a);}char*lstrcpy(char*a,const char*b){return strcpy(a,b);}char*lstrcat(char*a,const char*b){return strcat(a,b);}
static int copy(char*d,const char*s,int n){strncpy(d,s,n-1);d[n-1]=0;return strlen(d);}
UINT GetWindowsDirectory(char*d,UINT n){return copy(d,"C:\\WINDOWS",n);}
int GetPrivateProfileString(const char*s,const char*k,const char*f,char*d,int n,const char*p){(void)s;(void)p;return copy(d,!strcmp(k,"Startup")?choice:!strcmp(k,"Directory")?dir:f,n);}
int GetPrivateProfileInt(const char*s,const char*k,int d,const char*p){(void)s;(void)d;(void)p;return !strcmp(k,"LoadRun")?opts:exitopt;}
int GetProfileString(const char*s,const char*k,const char*f,char*d,int n){(void)s;(void)f;return copy(d,!strcmp(k,"load")?loads:runs,n);}
int OpenFile(const char*s,OFSTRUCT*o,UINT f){(void)s;(void)o;(void)f;return missing?-1:1;}
int FindWindow(const char*c,const char*t){(void)t;return busy&&!strcmp(c,busyClass);}
HMODULE GetModuleHandle(const char*m){return !strcmp(m,"SOUND")?driver:!strcmp(m,"TEXIT")?exitLive:(!strcmp(m,"XPCHIME")||!strcmp(m,"TCHIME"))?live:0;}
static int rawLease(unsigned v,unsigned op){if(v!=1)return -1;if(op==1){if(claimFail)return -3;held=1;return 0;}if(op==2){held=0;return 0;}return -1;}
static int mockOpen(void){if(soundBusy)return -1;opens++;return 3;}
static void mockClose(void){closes++;held=0;}
FARPROC GetProcAddress(HMODULE h,const char*s){
 if(!h)return NULL;
 if(!strcmp(s,"DEBUGTIMER")||(api&&!strcmp(s,"TANDYPSGLEASE")))return (FARPROC)rawLease;
 if(openapi&&!strcmp(s,"OPENSOUND"))return (FARPROC)mockOpen;
 if(closeapi&&!strcmp(s,"CLOSESOUND"))return (FARPROC)mockClose;
 return NULL;
}
int SetTimer(HWND w,int i,int ms,void*f){(void)w;(void)i;(void)ms;(void)f;timer=timerok;return timerok;}int KillTimer(HWND w,int i){(void)w;(void)i;timer=0;return 1;}
UINT WinExec(const char*c,UINT s){(void)s;execs++;assert(!held);strcpy(last,c);if(execfail)return 2;if(strstr(c,"TEXIT"))exitLive=1;else live=1;return 42;}
UINT PmLaunchShow(HWND w,char*c,int show){(void)w;strcpy(commands[apps],c);mode[apps++]=show;if(appfail){boxes++;return 2;}return 42;}
int ExitWindows(DWORD d,unsigned r){(void)d;(void)r;exits++;return !veto;}int MessageBox(HWND w,const char*t,const char*c,UINT m){(void)w;(void)t;(void)c;(void)m;boxes++;return 1;}
unsigned GetWindowWord(HWND w,int n){(void)w;(void)n;return 1;}
void TinyNotice(HWND w,HINSTANCE i,char*t,char*s){(void)w;(void)i;(void)t;(void)s;boxes++;}
#include "../TSBOOT.C"
static void reset(void){begun=waiting=listed=warned=useExit=0;commandSet=commandTooLong=0;bootCommand[0]=0;choice="XP";dir="C:\\TSTART";loads=runs="";opts=exitopt=timerok=1;missing=busy=live=exitLive=execfail=veto=appfail=0;driver=api=openapi=closeapi=1;soundBusy=claimFail=held=opens=closes=0;execs=apps=exits=boxes=timer=0;busyClass="TandyPSGTest";}
static void commandTests(void){
 char tail[128];int n;
 reset();opts=0;TandyBootCommand("  \"C:\\MMLAB\\MINIPLAY.EXE\" /Case \"two args\"  ");
 TandyBootBegin(1);assert(execs==1&&apps==0&&timer&&TandyBootBusy());
 TandyBootTick(1);assert(!apps);
 live=0;TandyBootTick(1);
 assert(apps==1&&mode[0]==SW_SHOWNORMAL&&!timer&&!TandyBootBusy());
 assert(!strcmp(commands[0],"  \"C:\\MMLAB\\MINIPLAY.EXE\" /Case \"two args\"  "));
 TandyBootBegin(1);TandyBootTick(1);assert(apps==1);
 reset();choice="NONE";opts=0;TandyBootCommand("START.EXE /s");
 TandyBootBegin(1);assert(apps==1&&!strcmp(commands[0],"START.EXE /s"));
 reset();choice="NONE";opts=0;TandyBootCommand("/S");
 TandyBootBegin(1);assert(!apps&&!boxes);
 reset();choice="NONE";opts=0;TandyBootCommand(" \t/s \t");
 TandyBootBegin(1);assert(!apps&&!boxes);
 reset();choice="NONE";runs="OK.EXE";TandyBootCommand("");
 TandyBootBegin(1);assert(apps==1&&!strcmp(commands[0],"OK.EXE")&&!boxes);
 reset();choice="NONE";opts=0;TandyBootCommand(" \t");
 TandyBootBegin(1);assert(!apps&&!boxes);
 reset();choice="NONE";opts=0;TandyBootCommand(NULL);
 TandyBootBegin(1);assert(!apps&&!boxes);
 reset();choice="NONE";opts=0;memset(tail,'A',127);tail[127]=0;
 TandyBootCommand(tail);TandyBootBegin(1);assert(!apps&&boxes==1);
 TandyBootBegin(1);TandyBootTick(1);assert(!apps&&boxes==1);
 reset();choice="NONE";opts=0;lstrcpy(tail,"\"C:\\APP.EXE\" ");
 for(n=lstrlen(tail);n<126;n++)tail[n]='x';
 tail[n]=0;
 TandyBootCommand(tail);TandyBootBegin(1);
 assert(apps==1&&lstrlen(commands[0])==126&&!strcmp(commands[0],tail)&&!boxes);
 reset();opts=0;memset(tail,'A',127);tail[127]=0;
 TandyBootCommand(tail);TandyBootBegin(1);assert(!apps&&!boxes&&timer);
 live=0;TandyBootTick(1);assert(!apps&&boxes==1&&!timer);
 reset();choice="NONE";opts=0;appfail=1;TandyBootCommand("C:\\FAIL.EXE");
 TandyBootBegin(1);assert(apps==1&&boxes==1);
 TandyBootBegin(1);TandyBootTick(1);assert(apps==1&&boxes==1);
 reset();choice="NONE";opts=0;TandyBootCommand("FIRST.EXE");
 TandyBootCommand("SECOND.EXE");TandyBootBegin(1);
 assert(apps==1&&!strcmp(commands[0],"FIRST.EXE"));
 reset();choice="NONE";opts=0;TandyBootBegin(1);
 TandyBootCommand("LATE.EXE");TandyBootTick(1);assert(!apps);
 reset();opts=0;TandyBootCommand("APP.EXE");TandyBootBegin(1);
 TandyBootStop(1);live=0;TandyBootTick(1);assert(!apps&&!timer);
 reset();choice="NONE";loads="ONE.EXE";runs="TWO.EXE";
 TandyBootCommand("THREE.EXE arg");TandyBootBegin(1);
 assert(apps==3&&mode[0]==SW_SHOWMINNOACTIVE&&mode[1]==SW_SHOWNORMAL&&
  mode[2]==SW_SHOWNORMAL&&!strcmp(commands[0],"ONE.EXE")&&
  !strcmp(commands[1],"TWO.EXE")&&!strcmp(commands[2],"THREE.EXE arg"));
 reset();choice="NONE";opts=0;TandyBootCommand("/S other.exe");
 TandyBootBegin(1);assert(apps==1&&!strcmp(commands[0],"/S other.exe"));
}
int main(void){char huge[1100];int i;
reset();loads="ONE.EXE";runs="TWO.COM XPCHIME.EXE TCHIME.EXE";TandyBootBegin(1);assert(execs==1&&apps==0&&timer);TandyBootBegin(1);TandyBootTick(1);assert(execs==1&&apps==0);live=0;TandyBootTick(1);assert(apps==2&&mode[0]==7&&mode[1]==1&&!timer);TandyBootTick(1);assert(apps==2);assert(!strcmp(commands[0],"ONE.EXE"));
reset();choice="TANDY";TandyBootBegin(1);assert(strstr(last,"TCHIME.EXE")&&!strstr(last,"XPCHIME"));
reset();choice="NONE";runs="TCHIME.EXE XPCHIME.EXE APP.PIF";TandyBootBegin(1);assert(execs==0&&apps==1);
reset();busy=1;runs="OK.EXE";TandyBootBegin(1);assert(!execs&&apps==1);
reset();soundBusy=1;runs="OK.EXE";TandyBootBegin(1);assert(!execs&&apps==1);
reset();missing=1;runs="OK.EXE";TandyBootBegin(1);assert(!execs&&apps==1&&boxes==1);
reset();timerok=0;runs="OK.EXE";TandyBootBegin(1);assert(!execs&&apps==1&&boxes==1);
reset();execfail=1;runs="OK.EXE";TandyBootBegin(1);assert(execs==1&&apps==1&&!timer&&boxes==1);
reset();runs="OK.EXE";TandyBootBegin(1);TandyBootStop(1);live=0;TandyBootTick(1);assert(!apps&&!timer);
reset();choice="NONE";runs="TEXIT.EXE TSHELL.EXE FILE.TXT OK.BAT";TandyBootBegin(1);assert(apps==1&&boxes==1&&!strcmp(commands[0],"OK.BAT"));
reset();choice="NONE";memset(huge,'X',sizeof(huge)-1);huge[sizeof(huge)-1]=0;runs=huge;TandyBootBegin(1);assert(!apps&&boxes==1);
reset();choice="NONE";memset(huge,'X',127);strcpy(huge+127," OK.EXE");runs=huge;TandyBootBegin(1);assert(apps==1&&boxes==1&&!strcmp(commands[0],"OK.EXE"));
reset();choice="NONE";huge[0]=0;for(i=0;i<66;i++)strcat(huge,"A.EXE ");runs=huge;TandyBootBegin(1);assert(apps==64&&boxes==1);
reset();TandyExit(1,0);assert(execs==1&&!strcmp(last,"C:\\TSTART\\TEXIT.EXE /go")&&!exits);TandyExit(1,0);assert(execs==1&&boxes==1);
reset();missing=1;TandyExit(1,0);assert(!execs&&!exits&&boxes==1);TandyExit(1,1);assert(exits==1);
reset();busy=1;TandyExit(1,0);assert(!execs&&!exits&&boxes==1);
reset();soundBusy=1;TandyExit(1,0);assert(!execs&&!exits&&boxes==1);
reset();veto=1;TandyExit(1,1);assert(exits==1&&boxes==1);
reset();exitopt=0;TandyExit(1,0);assert(exits==1&&!execs);
reset();dir="C:\\BAD PATH";TandyBootBegin(1);assert(!execs&&boxes==1);
reset();memset(huge,'A',sizeof(huge)-1);huge[sizeof(huge)-1]=0;dir=huge;TandyBootBegin(1);assert(!execs&&boxes==1);
reset();busy=1;busyClass="TandyStartupChime";TandyExit(1,0);assert(!execs&&!exits&&boxes==1);
reset();busy=1;busyClass="TandyXPStartupChime";TandyExit(1,0);assert(!execs&&!exits&&boxes==1);
reset();TandyBootBegin(1);assert(execs==1&&opens==1&&closes==1&&!held);
reset();driver=0;TandyBootBegin(1);assert(!execs&&!opens&&!held);
reset();api=0;TandyBootBegin(1);assert(!execs&&!opens&&!held);
reset();claimFail=1;TandyBootBegin(1);assert(!execs&&opens==1&&closes==1&&!held);
reset();TandyExit(1,0);assert(execs==1&&opens==1&&closes==1&&!held);
reset();openapi=0;TandyBootBegin(1);assert(!execs&&!opens&&!closes&&!held);
reset();closeapi=0;TandyBootBegin(1);assert(!execs&&!opens&&!closes&&!held);
commandTests();
puts("PASS: 30 lifecycle/lease and 16 primary command-tail scenarios");return 0;}
