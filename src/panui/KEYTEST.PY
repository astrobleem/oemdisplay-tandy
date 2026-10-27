#!/usr/bin/env python3
"""Host C89 API-stub checks for shared key bindings, queue and callback lifetime, no Win16 claim."""
from pathlib import Path
import argparse,os,subprocess,sys,json,hashlib
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
out=ap.parse_args().out.resolve();out.mkdir(parents=True)
src=Path(__file__).resolve().with_name('PANKEY.C');(out/'PANKEY.C').write_bytes(src.read_bytes());(out/'PANKEY.H').write_bytes(src.with_suffix('.H').read_bytes());(out/'PANCMD.H').write_bytes(src.with_name('PANCMD.H').read_bytes())
(out/'windows.h').write_text('''#ifndef KEY_TEST_WINDOWS_H
#define KEY_TEST_WINDOWS_H
#define VK_SHIFT 16
#define VK_NEXT 34
#define FAR
#define PASCAL
#define NULL ((void*)0)
#define TRUE 1
#define FALSE 0
#define HC_ACTION 0
#define WH_KEYBOARD 2
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
#define VK_CONTROL 17
typedef unsigned short WORD;
typedef unsigned char BYTE;
typedef unsigned long DWORD;
typedef int BOOL;
typedef void *HINSTANCE;
typedef void *HWND;
typedef char *LPSTR;
typedef void (*FARPROC)(void);
int GetKeyState(int);
int PostMessage(HWND,WORD,WORD,long);
int DefHookProc(int,WORD,DWORD,FARPROC*);
FARPROC GetProcAddress(HINSTANCE,const char*);
FARPROC SetWindowsHook(int,FARPROC);
int UnhookWindowsHook(int,FARPROC);
#endif
''')
(out/'TEST.C').write_text('''#include <assert.h>
#include "PANKEY.C"
static int posts,chain,control=1,post_ok=1,remove_ok=1,reenter=0;
static void dummy(void){}
int GetKeyState(int key){return control?0x8000:0;}
int PostMessage(HWND h,WORD m,WORD w,long l){assert(h);posts++;return post_ok;}
int DefHookProc(int c,WORD k,DWORD b,FARPROC *p){chain++;if(reenter){assert(!PanKeyRemove());}return 7;}
FARPROC GetProcAddress(HINSTANCE h,const char *n){return dummy;}
FARPROC SetWindowsHook(int kind,FARPROC proc){return NULL;}
int UnhookWindowsHook(int kind,FARPROC proc){return remove_ok;}
int main(void){int i;PANBIND map[2];
 LibMain((HINSTANCE)1,0,0,NULL);
 assert(PanKeyInstall((HWND)2,100));
 assert(!PanKeyInstall((HWND)3,100));
 assert(PanKeyHook(-1,VK_RIGHT,0x20000000L)==7);
 PanKeyHook(0,VK_RIGHT,0xa0000000L);
 control=0;PanKeyHook(0,VK_RIGHT,0x20000000L);control=1;
 assert(PanKeyNext()==0 && posts==0 && chain==3);
 for(i=0;i<31;i++)PanKeyHook(0,VK_RIGHT,0x20000000L);
 assert(posts==1);
 PanKeyHook(0,VK_LEFT,0x20000000L);
 for(i=0;i<31;i++)assert(PanKeyNext()==PK_RIGHT);
 assert(PanKeyNext()==0);
 post_ok=0;PanKeyHook(0,VK_DOWN,0x20000000L);
 assert(PanKeyNext()==PK_DOWN && PanKeyNext()==0);
 post_ok=1;PanKeyHook(0,VK_HOME,0x20000000L);
 assert(PanKeyNext()==PK_HOME);
 reenter=1;PanKeyHook(0,VK_LEFT,0x20000000L);reenter=0;assert(live && !owner);
 assert(PanKeyRemove());assert(PanKeyInstall((HWND)2,100));
 remove_ok=0;assert(!PanKeyRemove());
 i=posts;PanKeyHook(0,VK_LEFT,0x20000000L);assert(posts==i);
 assert(!PanKeyInstall((HWND)4,100));
 remove_ok=1;assert(PanKeyRemove());
 assert(PanKeyInstall((HWND)4,100));assert(PanKeyRemove());
 map[0].key=VK_NEXT;map[0].command=PK_DOWN;map[0].mods=PK_ALT;map[0].flags=PK_ONCE;
 map[1]=map[0];map[1].key='S';map[1].command=PK_SETTINGS;map[1].mods=PK_CTRL|PK_ALT;map[1].flags=0;
 assert(!PanKeyInstallEx((HWND)2,100,map,PK_BIND_MAX+1));
 map[0].mods=8;assert(!PanKeyInstallEx((HWND)2,100,map,2));map[0].mods=PK_ALT;
 assert(PanKeyInstallEx((HWND)2,100,map,2));
 control=0;PanKeyHook(0,VK_NEXT,0x20000000L);assert(PanKeyNext()==PK_DOWN);
 PanKeyHook(0,VK_NEXT,0x60000000L);assert(!PanKeyNext());
 PanKeyHook(0,'S',0x20000000L);assert(!PanKeyNext());control=1;
 PanKeyHook(0,'S',0x20000000L);assert(PanKeyNext()==PK_SETTINGS);
 assert(PanKeyRemove());
 return 0;}
''')
launcher=Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'
cmd=[sys.executable,str(launcher),'--','-x','c','-std=c89','-I',str(out),str(out/'TEST.C'),'-o',str(out/'TEST.EXE')]
r=subprocess.run(cmd,capture_output=True,text=True);(out/'BUILD.LOG').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
env=os.environ.copy();env['PATH']=r'C:\msys64\ucrt64\bin;'+env.get('PATH','')
subprocess.run([str((out/'TEST.EXE').resolve())],env=env,check=True)
r=dict(outcome='PASS',kind='HOST_API_STUBS_ONLY',source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),checks=['legacy default ABI and configurable modifier/once bindings','invalid binding maps refused','callback reentrancy prevents unload','hook chain, negative code and key-up ignored','Ctrl/Alt required','31 retained commands, one wake, bounded overflow','drain after failed PostMessage','unhook failure stops posting and refuses another install','successful retry and reinstall'])
(out/'RESULT.JSN').write_text(json.dumps(r,indent=2));print(json.dumps(r))
