"""Host API regression for silent optional DLL lookup and client lifetime."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
for n in ('PANKCL.C','PANKEY.H','PANCMD.H'):shutil.copyfile(HERE/n,out/n)
(out/'WINDOWS.H').write_text(r'''#ifndef CLIENT_WINDOWS_H
#define CLIENT_WINDOWS_H
#define FAR
#define PASCAL
#define VK_SHIFT 16
#define VK_CONTROL 17
#define VK_MENU 18
#define VK_HOME 36
#define VK_END 35
#define VK_LEFT 37
#define VK_RIGHT 39
#define VK_UP 38
#define VK_DOWN 40
#define VK_NUMPAD1 97
#define VK_NUMPAD2 98
#define VK_NUMPAD4 100
#define VK_NUMPAD6 102
#define VK_NUMPAD7 103
#define VK_NUMPAD8 104
#define GWW_HINSTANCE -6
#define OF_EXIST 0x4000
#define HFILE_ERROR -1
#define SEM_NOOPENFILEERRORBOX 0x8000
#define NULL ((void *)0)
typedef unsigned short WORD;
typedef unsigned int UINT;
typedef unsigned long DWORD;
typedef int BOOL;
typedef unsigned short HINSTANCE;
typedef unsigned short HWND;
typedef char *LPSTR;
typedef void (*FARPROC)(void);
typedef struct {int unused;} OFSTRUCT;
int OpenFile(LPSTR,OFSTRUCT *,int);
UINT SetErrorMode(UINT);
HINSTANCE LoadLibrary(LPSTR);
UINT GetSystemDirectory(LPSTR,int);
int GetModuleFileName(HINSTANCE,LPSTR,int);
WORD GetWindowWord(HWND,int);
int lstrlen(const char *);
LPSTR lstrcat(LPSTR,const char *);
FARPROC GetProcAddress(HINSTANCE,const char *);
void FreeLibrary(HINSTANCE);
int GetAsyncKeyState(int);
DWORD GetTickCount(void);
#endif
''')
(out/'TEST.C').write_text(r'''#include <assert.h>
#include <string.h>
#include "PANKCL.C"
static int beside,systemFile=1,valid=1,installOK=1,removeOK=1,loads,frees,installed,key;
static UINT mode=3;
static DWORD ticks;
static char loaded[160];
int OpenFile(LPSTR p,OFSTRUCT *o,int f){(void)o;assert(f==OF_EXIST);return strstr(p,"SYSTEM")?(systemFile?1:-1):(beside?1:-1);}
UINT SetErrorMode(UINT value){UINT old=mode;mode=value;return old;}
HINSTANCE LoadLibrary(LPSTR p){assert(mode==(3|SEM_NOOPENFILEERRORBOX));assert(strstr(p,"SYSTEM")?systemFile:beside);strcpy(loaded,p);loads++;return valid?33:2;}
UINT GetSystemDirectory(LPSTR p,int n){(void)n;strcpy(p,"C:\\WINDOWS\\SYSTEM");return (UINT)strlen(p);}
int GetModuleFileName(HINSTANCE h,LPSTR p,int n){(void)n;assert(h==1);strcpy(p,"C:\\WINDOWS\\OWNER.EXE");return (int)strlen(p);}
WORD GetWindowWord(HWND w,int index){assert(w==1&&index==GWW_HINSTANCE);return 1;}
int lstrlen(const char *p){return (int)strlen(p);}
LPSTR lstrcat(LPSTR p,const char *q){return strcat(p,q);}
static BOOL Install(HWND w,WORD message,const PANBIND *map,int n){assert(w==1&&message==100&&map&&n==13);installed++;return installOK;}
static BOOL Remove(void){return removeOK;}
static int Next(void){return PK_HOME;}
FARPROC GetProcAddress(HINSTANCE h,const char *n){assert(h==33);if(!strcmp(n,"PanKeyInstallEx"))return (FARPROC)Install;if(!strcmp(n,"PanKeyRemove"))return (FARPROC)Remove;if(!strcmp(n,"PanKeyNext"))return (FARPROC)Next;return 0;}
void FreeLibrary(HINSTANCE h){assert(h==33);frees++;}
int GetAsyncKeyState(int vk){return vk==VK_CONTROL||vk==VK_MENU||vk==key?0x8000:0;}
DWORD GetTickCount(void){return ticks;}
int main(void){PANBIND map[PK_BIND_MAX];int n=PanInputDefaults(map,PK_X|PK_Y);
 assert(n==13&&PanInputStart(1,100,map,n));assert(loads==1&&installed==1&&mode==3&&strstr(loaded,"SYSTEM"));
 assert(PanInputActive()&&PanInputNext()==PK_HOME);removeOK=0;assert(!PanInputStop()&&!frees);removeOK=1;assert(PanInputStop()&&frees==1&&!PanInputActive());
 beside=1;assert(PanInputStart(1,100,map,n));assert(!strstr(loaded,"SYSTEM")&&mode==3);assert(PanInputStop());
 beside=systemFile=0;loads=0;assert(!PanInputStart(1,100,map,n)&&!loads&&mode==3);
 key=VK_RIGHT;assert(PanInputNext()==PK_RIGHT);assert(!PanInputNext());ticks=201;assert(PanInputNext()==PK_RIGHT);key=0;assert(!PanInputNext());assert(PanInputStop());
 beside=1;valid=0;assert(!PanInputStart(1,100,map,n)&&loads==1&&mode==3);assert(PanInputStop());
 valid=1;installOK=0;frees=0;assert(!PanInputStart(1,100,map,n)&&frees==1&&mode==3);assert(PanInputStop());
 return 0;}
''')
launcher=Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'
p=subprocess.run([sys.executable,str(launcher),'--','-x','c','-std=c89','-I',str(out),str(out/'TEST.C'),'-o',str(out/'TEST.EXE')],capture_output=True,text=True);(out/'BUILD.LOG').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
subprocess.run([str(out/'TEST.EXE')],check=True)
r=dict(outcome='PASS_HOST_API_STUBS',source_sha256=hashlib.sha256((HERE/'PANKCL.C').read_bytes()).hexdigest(),checks=['missing adjacent file never passed to LoadLibrary','installed SYSTEM module loads silently','previous error mode restored','adjacent module preferred when present','missing or damaged optional module falls back silently','failed unhook retains reference until successful retry','failed installation releases only its reference','bounded polling repeat fallback'])
(out/'RESULT.JSN').write_text(json.dumps(r,indent=2));print(json.dumps(r))
