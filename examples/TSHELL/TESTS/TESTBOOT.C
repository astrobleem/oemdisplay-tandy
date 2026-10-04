#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <assert.h>
#include "windows.h"
static char *choice="XP",*dir="C:\\TSTART",*loads="",*runs="";
static int opts=1,exitopt=1,missing=0,timerok=1,busy=0,driver=0,live=0,exitLive=0,execfail=0,veto=0;
static char*busyClass="TandyPSGTest";
static int execs,apps,exits,boxes,timer,mode[80];static char commands[80][144],last[180];
int lstrcmpi(const char*a,const char*b){return strcasecmp(a,b);}int lstrlen(const char*a){return strlen(a);}char*lstrcpy(char*a,const char*b){return strcpy(a,b);}char*lstrcat(char*a,const char*b){return strcat(a,b);}
static int copy(char*d,const char*s,int n){strncpy(d,s,n-1);d[n-1]=0;return strlen(d);}
UINT GetWindowsDirectory(char*d,UINT n){return copy(d,"C:\\WINDOWS",n);}
int GetPrivateProfileString(const char*s,const char*k,const char*f,char*d,int n,const char*p){(void)s;(void)p;return copy(d,!strcmp(k,"Startup")?choice:!strcmp(k,"Directory")?dir:f,n);}
int GetPrivateProfileInt(const char*s,const char*k,int d,const char*p){(void)s;(void)d;(void)p;return !strcmp(k,"LoadRun")?opts:exitopt;}
int GetProfileString(const char*s,const char*k,const char*f,char*d,int n){(void)s;(void)f;return copy(d,!strcmp(k,"load")?loads:runs,n);}
int OpenFile(const char*s,OFSTRUCT*o,UINT f){(void)s;(void)o;(void)f;return missing?-1:1;}
int FindWindow(const char*c,const char*t){(void)t;return busy&&!strcmp(c,busyClass);}
HMODULE GetModuleHandle(const char*m){return !strcmp(m,"SOUND")?driver:!strcmp(m,"TEXIT")?exitLive:(!strcmp(m,"XPCHIME")||!strcmp(m,"TCHIME"))?live:0;}
FARPROC GetProcAddress(HMODULE h,const char*s){(void)s;return h?(void*)1:0;}
int SetTimer(HWND w,int i,int ms,void*f){(void)w;(void)i;(void)ms;(void)f;timer=timerok;return timerok;}int KillTimer(HWND w,int i){(void)w;(void)i;timer=0;return 1;}
UINT WinExec(const char*c,UINT s){(void)s;execs++;strcpy(last,c);if(execfail)return 2;if(strstr(c,"TEXIT"))exitLive=1;else live=1;return 42;}
UINT PmLaunchShow(HWND w,char*c,int show){(void)w;strcpy(commands[apps],c);mode[apps++]=show;return 42;}
int ExitWindows(DWORD d,unsigned r){(void)d;(void)r;exits++;return !veto;}int MessageBox(HWND w,const char*t,const char*c,UINT m){(void)w;(void)t;(void)c;(void)m;boxes++;return 1;}
unsigned GetWindowWord(HWND w,int n){(void)w;(void)n;return 1;}
void TinyNotice(HWND w,HINSTANCE i,char*t,char*s){(void)w;(void)i;(void)t;(void)s;boxes++;}
#include "../TSBOOT.C"
static void reset(void){begun=waiting=listed=warned=useExit=0;choice="XP";dir="C:\\TSTART";loads=runs="";opts=exitopt=timerok=1;missing=busy=driver=live=exitLive=execfail=veto=0;execs=apps=exits=boxes=timer=0;busyClass="TandyPSGTest";}
int main(void){char huge[1100];int i;
reset();loads="ONE.EXE";runs="TWO.COM XPCHIME.EXE TCHIME.EXE";TandyBootBegin(1);assert(execs==1&&apps==0&&timer);TandyBootBegin(1);TandyBootTick(1);assert(execs==1&&apps==0);live=0;TandyBootTick(1);assert(apps==2&&mode[0]==7&&mode[1]==1&&!timer);TandyBootTick(1);assert(apps==2);assert(!strcmp(commands[0],"ONE.EXE"));
reset();choice="TANDY";TandyBootBegin(1);assert(strstr(last,"TCHIME.EXE")&&!strstr(last,"XPCHIME"));
reset();choice="NONE";runs="TCHIME.EXE XPCHIME.EXE APP.PIF";TandyBootBegin(1);assert(execs==0&&apps==1);
reset();busy=1;runs="OK.EXE";TandyBootBegin(1);assert(!execs&&apps==1);
reset();driver=1;runs="OK.EXE";TandyBootBegin(1);assert(!execs&&apps==1);
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
reset();driver=1;TandyExit(1,0);assert(!execs&&!exits&&boxes==1);
reset();veto=1;TandyExit(1,1);assert(exits==1&&boxes==1);
reset();exitopt=0;TandyExit(1,0);assert(exits==1&&!execs);
reset();dir="C:\\BAD PATH";TandyBootBegin(1);assert(!execs&&boxes==1);
reset();memset(huge,'A',sizeof(huge)-1);huge[sizeof(huge)-1]=0;dir=huge;TandyBootBegin(1);assert(!execs&&boxes==1);
reset();busy=1;busyClass="TandyStartupChime";TandyExit(1,0);assert(!execs&&!exits&&boxes==1);
reset();busy=1;busyClass="TandyXPStartupChime";TandyExit(1,0);assert(!execs&&!exits&&boxes==1);
puts("PASS: 23 host lifecycle/option/failure scenarios");return 0;}
