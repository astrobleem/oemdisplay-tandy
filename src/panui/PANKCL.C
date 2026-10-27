/* No drawing or engine state here: shared load, queue and safe removal. */
#include <windows.h>
#include "PANKEY.H"
typedef BOOL (FAR PASCAL *INSTALL)(HWND,WORD,const PANBIND FAR *,int);
typedef BOOL (FAR PASCAL *REMOVE)(void);
typedef int (FAR PASCAL *NEXT)(void);
static HINSTANCE library;
static REMOVE removeKeys;
static NEXT nextKey;
static PANBIND fallback[PK_BIND_MAX];
static int count,held;
static DWORD last;
int PanInputDefaults(PANBIND *map,int axes)
{
 static WORD keys[13]={VK_HOME,VK_END,VK_LEFT,VK_RIGHT,VK_UP,VK_DOWN,
  VK_NUMPAD7,VK_NUMPAD1,VK_NUMPAD4,VK_NUMPAD6,VK_NUMPAD8,VK_NUMPAD2,'S'};
 int i,n=0,cmd;
 for(i=0;i<13;i++){
  cmd=i==12?PK_SETTINGS:i%6+1;
  if((cmd==PK_LEFT || cmd==PK_RIGHT) && !(axes&PK_X))continue;
  if((cmd==PK_UP || cmd==PK_DOWN) && !(axes&PK_Y))continue;
  map[n].key=keys[i];map[n].command=cmd;map[n].mods=PK_CTRL|PK_ALT;
  map[n++].flags=0;
 }
 return n;
}
/* LoadLibrary displays a blocking file-error box on Windows 3.0 unless
 * suppressed. Optional lookup must never put such a box off the viewport. */
static HINSTANCE TryLibrary(const char *path)
{
 OFSTRUCT of;HINSTANCE result;UINT oldMode;
 if(!path[0] || OpenFile((LPSTR)path,&of,OF_EXIST)==HFILE_ERROR)return 0;
 oldMode=SetErrorMode(SEM_NOOPENFILEERRORBOX);
 SetErrorMode(oldMode|SEM_NOOPENFILEERRORBOX);
 result=LoadLibrary((LPSTR)path);
 SetErrorMode(oldMode);return result;
}
int PanInputStart(HWND owner,WORD message,const PANBIND *map,int n)
{
 INSTALL install;int i,length;char path[160];
 if(library || n<1 || n>PK_BIND_MAX)return 0;
 for(i=0;i<n;i++)fallback[i]=map[i];count=n;held=0;
 /* Prefer the matching packet beside this owner over an older system DLL. */
 path[0]=0;
 if(GetModuleFileName((HINSTANCE)GetWindowWord(owner,GWW_HINSTANCE),path,sizeof(path))){
  for(i=lstrlen(path)-1;i>=0 && path[i]!='\\';i--);path[i+1]=0;
  if(i>=0 && i<140)lstrcat(path,"PANKEY.DLL");else path[0]=0;
 }
 library=TryLibrary(path);
 if(library<(HINSTANCE)32){
  length=GetSystemDirectory(path,sizeof(path));
  if(length>0 && length<140){
   if(path[length-1]!='\\')lstrcat(path,"\\");
   lstrcat(path,"PANKEY.DLL");library=TryLibrary(path);
  }else library=0;
 }
 if(library<(HINSTANCE)32){library=0;return 0;}
 install=(INSTALL)GetProcAddress(library,"PanKeyInstallEx");
 removeKeys=(REMOVE)GetProcAddress(library,"PanKeyRemove");
 nextKey=(NEXT)GetProcAddress(library,"PanKeyNext");
 if(!install || !removeKeys || !nextKey ||
    !install(owner,message,(const PANBIND FAR *)map,n)){
  removeKeys=0;nextKey=0;FreeLibrary(library);library=0;return 0;
 }
 return 1;
}
int PanInputActive(void){return nextKey!=0;}
int PanInputNext(void)
{
 int i,mods=0,cmd=0;DWORD now;
 if(nextKey)return nextKey();
 if(GetAsyncKeyState(VK_CONTROL)&0x8000)mods|=PK_CTRL;
 if(GetAsyncKeyState(VK_MENU)&0x8000)mods|=PK_ALT;
 if(GetAsyncKeyState(VK_SHIFT)&0x8000)mods|=PK_SHIFT;
 for(i=0;i<count;i++)if((WORD)(mods&fallback[i].mods)==fallback[i].mods &&
   (GetAsyncKeyState(fallback[i].key)&0x8000)){cmd=fallback[i].command;break;}
 now=GetTickCount();
 if(!cmd){held=0;return 0;}
 if(cmd==held && ((fallback[i].flags&PK_ONCE) || now-last<200L))return 0;
 held=cmd;last=now;return cmd;
}
int PanInputStop(void)
{
 if(!library){count=0;return 1;}
 if(!removeKeys || !removeKeys())return 0;
 nextKey=0;removeKeys=0;count=0;FreeLibrary(library);library=0;return 1;
}
