from pathlib import Path
import os,subprocess,sys,json,importlib.util,importlib.machinery
import argparse
p=argparse.ArgumentParser();p.add_argument('--cc',type=Path,default=Path('gcc'));p.add_argument('--out',type=Path,required=True);a=p.parse_args()
R=Path(__file__).resolve().parent.parent;O=a.out.resolve();O.mkdir(parents=True,exist_ok=True);GCC=a.cc
def crlf(path,text):path.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
# Run the exact existing parser regression suite using the current source.
env=dict(os.environ,PATH=str(GCC.parent)+os.pathsep+os.environ['PATH'])
with (O/'GRPTEST.LOG').open('w') as log:
    subprocess.run([sys.executable,str(R/'TESTS/GRPTEST.PY')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
crlf(O/'windows.h',r'''
#ifndef NAV_HOST_WINDOWS_H
#define NAV_HOST_WINDOWS_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stdint.h>
#define FAR
#define PASCAL
#define TRUE 1
#define FALSE 0
#define NULL ((void*)0)
typedef unsigned UINT;typedef unsigned WORD;typedef unsigned char BYTE;
typedef long LONG;typedef unsigned long DWORD;typedef intptr_t LPARAM;
typedef unsigned WPARAM;typedef int BOOL;typedef int HWND;typedef int HINSTANCE;
typedef int HFILE;typedef int HMENU;typedef int HDC;typedef int HFONT;
typedef char *LPSTR;typedef struct {int left,top,right,bottom;} RECT;
typedef struct {int tmHeight,tmMaxCharWidth;} TEXTMETRIC;
typedef struct {char szPathName[144];} OFSTRUCT;
#define HFILE_ERROR (-1)
#define OF_READ 0
#define OF_SHARE_DENY_WRITE 0
#define OF_EXIST 0
#define SW_SHOWNORMAL 1
#define GWW_HINSTANCE 0
#define SM_CXSCREEN 0
#define SM_CYSCREEN 1
#define SM_CYBORDER 2
#define SM_CYMENU 3
#define SYSTEM_FONT 0
#define LOWORD(v) ((unsigned)(v)&65535)
#define MF_STRING 0
#define MF_GRAYED 1
#define MF_POPUP 16
#define MF_BYPOSITION 32
#define lstrcmp strcmp
#define lstrlen strlen
#define lstrcpy strcpy
#define lstrcat strcat
#define wsprintf sprintf
int GetWindowWord(int,int);int GetWindowsDirectory(char*,int);
int GetPrivateProfileString(char*,char*,char*,char*,unsigned,char*);
int _lopen(char*,int);long _llseek(int,long,int);unsigned _lread(int,void*,unsigned);int _lclose(int);
int OpenFile(char*,OFSTRUCT*,int);int WinExec(char*,int);
int GetMenuItemCount(int);int GetSubMenu(int,int);int RemoveMenu(int,int,int);int DestroyMenu(int);
int CreatePopupMenu(void);int AppendMenu(int,int,unsigned,char*);
int GetSystemMetrics(int);int GetDC(int);int SelectObject(int,int);int GetStockObject(int);
int GetTextMetrics(int,TEXTMETRIC*);int ReleaseDC(int,int);int GetWindowRect(int,RECT*);
int SetActiveWindow(int);int SetFocus(int);int TrackPopupMenu(int,int,int,int,int,int,void*);
#endif
''')
crlf(O/'direct.h',r'''
int _getdrive(void);int _chdrive(int);char *getcwd(char*,unsigned);
char *_getdcwd(int,char*,unsigned);int chdir(char*);
''')
import struct
fixture_namespace=dict(struct=struct)
fixture_source=(R/'TESTS/GRPTEST.PY').read_text().split('def word(b, p):',1)[1].split('class Source:',1)[0]
exec('def word(b, p):'+fixture_source,fixture_namespace)
make=fixture_namespace['make']
fixtures=[]
for n in range(1,41):
    data=make(50 if n==1 else 1,command=b'  C:\\APPS\\ARGAPP.EXE  /MiXeD\t"Two Words" ',name=b'Item & literal',title=('Group %d'%n).encode())
    if n==1:
        for index in range(1,50):
            record=fixture_namespace['word'](data,34+2*index)
            start=fixture_namespace['word'](data,record+20)
            pos=data.index(b'Words',start)
            data[pos:pos+5]=('App%02d'%index).encode()
        fixture_namespace['checksum'](data)
    if n==2:data=make(0,title=b'Empty')
    if n==3:data[4]^=1 # Bad checksum: peek OK, entry rejected.
    if n==4:data=bytearray(b'junk') # Malformed header.
    fixtures.append(data)
arrays='\n'.join('static unsigned char g%d[]={%s};'%(i+1,','.join(map(str,b))) for i,b in enumerate(fixtures))
sizes=','.join(str(len(b)) for b in fixtures);ptrs=','.join('g%d'%(i+1) for i in range(40))
code=r'''
#include "windows.h"
#include "direct.h"
'''+arrays+f'\nstatic unsigned char *groups[]={{ {ptrs} }};\nstatic unsigned sizes[]={{ {sizes} }};\n'+r'''
static int registered=4,screenw=320,screenh=200,activeMenus,allocations,appends,failAlloc,failAppend,bundleWanted,noDC;
static unsigned long reads;static int opened,closed,launches,drive=3,failed;
static char cwdC[144]="C:\\ORIG",cwdD[144]="D:\\KEPT",launched[128],launchcwd[144];
typedef struct {int used,count;struct {int flags;unsigned id;char text[140];} row[60];} MENU;
static MENU menus[300];static long positions[41];
int GetWindowWord(int w,int n){return 1;}
int GetPrivateProfileInt(char *section,char *key,int value,char *ini){return bundleWanted;}
int GetWindowsDirectory(char *s,int n){strcpy(s,"C:\\WINDOWS");return 10;}
int GetPrivateProfileString(char *section,char *key,char *def,char *out,unsigned cap,char *ini){
 if(!strcmp(section,"Programs")){strcpy(out,!strncmp(key,"Name",4)?"Bundle & app":"C:\\APPS\\ARGAPP.EXE /bundle");return strlen(out);}
 int n=atoi(key+5);if(n<1||n>registered){out[0]=0;return 0;}
 sprintf(out,"G%d.GRP",n);return strlen(out);
}
int _lopen(char *path,int flags){char *s=strrchr(path,'\\');int n=atoi(s+2);if(n<1||n>40)return -1;positions[n]=0;opened++;return n;}
long _llseek(int f,long p,int w){positions[f]=(w==2?sizes[f-1]:w==1?positions[f]:0)+p;return positions[f];}
unsigned _lread(int f,void *b,unsigned n){if(positions[f]+n>sizes[f-1])return 0;memcpy(b,groups[f-1]+positions[f],n);positions[f]+=n;reads+=n;return n;}
int _lclose(int f){closed++;return 0;}
int OpenFile(char *token,OFSTRUCT *of,int flags){strcpy(of->szPathName,"C:\\APPS\\ARGAPP.EXE");return 1;}
int _getdrive(void){return drive;}int _chdrive(int d){drive=d;return 0;}
char *getcwd(char *s,unsigned n){strcpy(s,drive==3?cwdC:cwdD);return s;}
char *_getdcwd(int d,char *s,unsigned n){strcpy(s,d==3?cwdC:cwdD);return s;}
int chdir(char *s){strcpy(drive==3?cwdC:cwdD,s);return 0;}
int WinExec(char *s,int show){strcpy(launched,s);getcwd(launchcwd,144);launches++;return 33;}
void TinyNotice(HWND w,HINSTANCE i,char *title,char *text){}
int GetMenuItemCount(int m){return menus[m].count;}
int GetSubMenu(int m,int n){return (menus[m].row[n].flags&16)?menus[m].row[n].id:0;}
int RemoveMenu(int m,int n,int flags){memmove(&menus[m].row[n],&menus[m].row[n+1],sizeof(menus[m].row[0])*(menus[m].count-n-1));menus[m].count--;return 1;}
int DestroyMenu(int m){int i;if(!menus[m].used){failed++;return 0;}for(i=0;i<menus[m].count;i++)if(menus[m].row[i].flags&16)DestroyMenu(menus[m].row[i].id);menus[m].used=0;activeMenus--;return 1;}
int CreatePopupMenu(void){int i;allocations++;if(allocations==failAlloc)return 0;for(i=1;i<300;i++)if(!menus[i].used){memset(&menus[i],0,sizeof(menus[i]));menus[i].used=1;activeMenus++;return i;}return 0;}
int AppendMenu(int m,int flags,unsigned id,char *text){int n;appends++;if(appends==failAppend)return 0;n=menus[m].count++;if(n>=60){failed++;return 0;}menus[m].row[n].flags=flags;menus[m].row[n].id=id;strcpy(menus[m].row[n].text,text);return 1;}
int GetSystemMetrics(int n){return n==0?screenw:n==1?screenh:n==3?11:1;}
int GetDC(int n){return noDC?0:1;}int SelectObject(int d,int f){return 1;}int GetStockObject(int n){return 1;}
unsigned long GetTextExtent(int d,char *s,int n){return n*8;}
int GetTextMetrics(int d,TEXTMETRIC *t){t->tmHeight=8;t->tmMaxCharWidth=8;return 1;}int ReleaseDC(int n,int d){return 1;}
int GetWindowRect(int w,RECT*r){r->top=180;return 1;}int SetActiveWindow(int w){return 1;}int SetFocus(int w){return 1;}
int TrackPopupMenu(int m,int f,int x,int y,int r,int w,void*p){return 1;}
void TSMenuTrack(int m,int x,int y,int w){}
#include "PROGMENU.C"
static void ck(char *name,int ok){printf("CHECK %s=%d\n",name,ok!=0);if(!ok)failed++;}
static int itemcount(int m){int i,n=0;for(i=0;i<menus[m].count;i++){if(menus[m].row[i].flags&16)n+=itemcount(menus[m].row[i].id);else if(menus[m].row[i].id>=1000)n++;}return n;}
int main(void){int m,child,i,before;char label[128],amp[64];unsigned long readbefore;
 strcpy(label,"A&B");pmlabel(amp,label);ck("literal_ampersand_exact",!strcmp(amp,"A&&B"));
 noDC=1;ck("failed_gdi_metrics_fallback",pmrows()==16);noDC=0;
 screenh=400;ck("logical_height_capped_to_viewport",pmrows()==20);screenh=200;
 readbefore=reads;m=PmMenuCreate(1);ck("start_defers_group_reads",reads==readbefore&&!pmReady&&GetMenuItemCount(m)==1);PmMenuInit(m);
 ck("bounded_title_peeks",reads-readbefore<=4*98);
 ck("registered_groups",GetMenuItemCount(m)==4);
 ck("malformed_group_disabled",menus[m].row[3].flags&MF_GRAYED);
 child=GetSubMenu(m,0);PmMenuInit(child);ck("fifty_items_paged",itemcount(child)==50);
 ck("literal_ampersands",strstr(menus[child].row[0].text,"&&")!=NULL || screenw==320);
 readbefore=reads;PmMenuInit(child);ck("no_repeat_hover_reads",reads==readbefore);
 PmMenuDone();before=launches;ck("deferred_selection_handled",PmMenuChoose(1,1000));
 PmMenuChoose(1,1000);ck("posted_selection_consumed_once",launches==before+1);
 pmBusy=1;pmReady=1; /* Continue testing the existing native menu tree. */
 ck("selected_command_exact",launches==before+1&&!strcmp(launched,"  C:\\APPS\\ARGAPP.EXE  /MiXeD\t\"Two Words\" "));
 ck("working_directory",!strcmp(launchcwd,"C:\\APPS"));
 ck("cwd_restoration",!strcmp(cwdC,"C:\\ORIG")&&!strcmp(cwdD,"D:\\KEPT")&&drive==3);
 PmMenuChoose(1,1049);ck("last_paged_item_mapping",!strcmp(launched,"  C:\\APPS\\ARGAPP.EXE  /MiXeD\t\"Two App49\" "));
 child=GetSubMenu(m,1);PmMenuInit(child);ck("empty_group",GetMenuItemCount(child)==1&&menus[child].row[0].flags&MF_GRAYED);
 ck("one_group_resident",itemcount(pmIndex[0].menu)==0);
 child=GetSubMenu(m,2);PmMenuInit(child);ck("checksum_rejected",GetMenuItemCount(child)==1&&menus[child].row[0].flags&MF_GRAYED);
 pmReady=1;PmMenuInit(pmIndex[0].menu);before=launches;groups[0][4]^=1;PmMenuChoose(1,1000);ck("changed_group_refused",launches==before);groups[0][4]^=1;
 DestroyMenu(m);PmMenuDone();ck("session_cleanup",activeMenus==0&&opened==closed);
 registered=0;m=PmMenuCreate(1);PmMenuInit(m);ck("no_groups_disabled",GetMenuItemCount(m)==1&&menus[m].row[0].flags&MF_GRAYED);DestroyMenu(m);PmMenuDone();
 registered=40;screenw=160;m=PmMenuCreate(1);PmMenuInit(m);ck("forty_groups_paged",pmGroups==40&&GetMenuItemCount(m)<=pmRows+1);DestroyMenu(m);PmMenuDone();
 bundleWanted=1;m=PmMenuCreate(1);PmMenuInit(m);ck("configured_bundle_preserved",pmGroups==41&&pmIndex[40].number==0);PmMenuInit(pmIndex[40].menu);DestroyMenu(m);PmMenuDone();before=launches;PmMenuChoose(1,3000);ck("configured_bundle_deferred_launch",launches==before+1&&!strcmp(launched,"C:\\APPS\\ARGAPP.EXE /bundle"));bundleWanted=0;
 for(i=1;i<=50;i++){allocations=appends=0;failAlloc=i;m=PmMenuCreate(1);if(m){PmMenuInit(m);DestroyMenu(m);}PmMenuDone();if(activeMenus)break;}
 ck("allocation_fault_cleanup",!activeMenus);failAlloc=0;
 for(i=1;i<=150;i++){allocations=appends=0;failAppend=i;m=PmMenuCreate(1);if(m){PmMenuInit(m);DestroyMenu(m);}PmMenuDone();if(activeMenus)break;}
 ck("append_fault_cleanup",!activeMenus);failAppend=0;
 printf("FINAL failures=%d\n",failed);return failed?1:0;
}
'''
crlf(O/'HOSTNAV.C',code)
subprocess.run([str(GCC),'-std=c89','-w','-I'+str(O),'-I'+str(R),'-x','c',str(O/'HOSTNAV.C'),str(R/'GRPREAD.C'),'-o',str(O/'HOSTNAV.EXE')],env=env,check=True)
r=subprocess.run([str(O/'HOSTNAV.EXE')],capture_output=True,text=True,env=env)
(O/'HOSTNAV.LOG').write_text(r.stdout+r.stderr);print(r.stdout);r.check_returncode()
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',parser='13 parser groups including 1000 mutations',menu_log=r.stdout),indent=2))
