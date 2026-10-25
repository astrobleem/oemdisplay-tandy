/* Windows 3.0 / 8088: load the exact private About shim before WinMine.
 * No global DLL installation, INI changes, or display launch bypass.
 */
#define WINVER 0x0300
#include <windows.h>
typedef unsigned long U32;
static U32 crc(U32 c,unsigned char *p,unsigned n)
{
 unsigned i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c&1)?(c>>1)^0xedb88320UL:c>>1;}
 return c;
}
static int exact(char *path,U32 size,U32 expected)
{
 unsigned char b[512];HFILE f;unsigned n;U32 total=0,c=0xffffffffUL;
 f=_lopen(path,OF_READ|OF_SHARE_DENY_WRITE);if(f==HFILE_ERROR)return 0;
 for(;;){n=_lread(f,b,sizeof(b));if(n==(unsigned)-1){_lclose(f);return 0;}if(!n)break;
  total+=n;if(total>size){_lclose(f);return 0;}c=crc(c,b,n);
 }
 if(_lclose(f))return 0;return total==size&&(c^0xffffffffUL)==expected;
}
static int error(char *message)
{MessageBox(NULL,message,"Minesweeper",MB_OK|MB_ICONEXCLAMATION);return 1;}
int PASCAL WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR args,int show)
{
 char folder[128],exe[144],dll[144],loaded[144];int i;UINT n,result;HINSTANCE shim,existing;
 previous=previous;show=show;
 if(args[0])return error("Run MINERUN\nwithout switches.");
 if(GetWinFlags()&(WF_STANDARD|WF_ENHANCED))return error("Use Windows 3.0\nreal mode.");
 n=GetModuleFileName(instance,folder,sizeof(folder));
 if(!n||n>=sizeof(folder)-1||folder[1]!=':')return error("Cannot locate\nthe app folder.");
 for(i=(int)n-1;i>=0&&folder[i]!='\\';i--);
 if(i<2)return error("Cannot locate\nthe app folder.");folder[i+1]=0;
 lstrcpy(exe,folder);lstrcat(exe,"WINMINE.EXE");lstrcpy(dll,folder);lstrcat(dll,"WMABT.DLL");
 if(!exact(exe,30032UL,MINE_CRC)||!exact(dll,1998UL,SHIM_CRC))return error("App files differ.\nRun MINESET again\nin a new folder.");
 existing=GetModuleHandle("WMABT");
 if(existing){n=GetModuleFileName(existing,loaded,sizeof(loaded));
  if(!n||n>=sizeof(loaded)-1||!exact(loaded,1998UL,SHIM_CRC))return error("Another About DLL\nis already in use.\nExit Windows and\nstart it again.");
 }
 shim=LoadLibrary(dll);if((UINT)shim<32)return error("About helper\ncould not load.");
 result=WinExec(exe,SW_SHOWNORMAL);FreeLibrary(shim);
 if(result<32)return error("Minesweeper\ncould not start.");return 0;
}
