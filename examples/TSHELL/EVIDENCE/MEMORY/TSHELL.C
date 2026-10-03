#define WINVER 0x0300
#include <windows.h>
int PASCAL WinMain(HINSTANCE a,HINSTANCE b,LPSTR c,int d){HFILE f;UINT r;HWND bar;DWORD before,after;char s[400];HGLOBAL code;FARPROC proc;DWORD cb,db;UINT cf;
 before=GetFreeSpace(0);r=WinExec("C:\\WINDOWS\\TSHELL.EXE",SW_SHOWNORMAL);after=GetFreeSpace(0);bar=FindWindow("TandyStart",NULL);proc=bar?(FARPROC)GetWindowLong(bar,GWL_WNDPROC):NULL;code=proc?GetCodeHandle(proc):0;cb=code?GlobalSize(code):0;cf=code?GlobalFlags(code):0;db=GlobalSize((HGLOBAL)r);
 f=_lcreat("C:\\MEMQA.LOG",0);wsprintf(s,"REAL_MODE=%u\r\nLAUNCHED=%u\r\nBAR_FOUND=%u\r\nFREE_BEFORE=%lu\r\nFREE_AFTER=%lu\r\nDELTA=%lu\r\nCODE_BYTES=%lu\r\nCODE_FLAGS=%u\r\nDATA_BYTES=%lu\r\n",!(GetWinFlags()&WF_PMODE),r>=32,bar!=NULL,before,after,before-after,cb,cf,db);_lwrite(f,s,lstrlen(s));_lclose(f);
 if(bar)SendMessage(bar,WM_COMMAND,41,0L);Yield();f=_lopen("C:\\MEMQA.LOG",OF_WRITE);_llseek(f,0L,2);wsprintf(s,"BAR_CLOSED=%u\r\nNO_COMMDLG=%u\r\nCOMPLETE=1\r\n",FindWindow("TandyStart",NULL)==NULL,GetModuleHandle("COMMDLG")==NULL);_lwrite(f,s,lstrlen(s));_lclose(f);ExitWindows(0L,0);return 0;}
