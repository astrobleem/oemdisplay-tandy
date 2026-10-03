#define WINVER 0x0300
#include <windows.h>
extern unsigned FAR PASCAL BiosMode(void);
static HFILE logFile;
static void line(char *key, int value)
{
    char out[100], digits[8];
    int n=0, d=0;
    unsigned v;
    while (*key) out[n++]=*key++;
    out[n++]='=';
    if (value<0) { out[n++]='-'; v=(unsigned)(-value); }
    else v=(unsigned)value;
    do { digits[d++]=(char)('0'+v%10); v/=10; } while(v);
    while(d) out[n++]=digits[--d];
    out[n++]='\r'; out[n++]='\n';
    _lwrite(logFile,out,n);
}

int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 POINT p,old;
 MSG msg;
 DWORD start,last;
 int n=0;
 logFile=_lcreat("C:\\PROBECUR.LOG",0);
 if(logFile==HFILE_ERROR) return 1;
 line("PROBE_VERSION",3);
 line("SM_CXSCREEN",GetSystemMetrics(0));
 line("SM_CYSCREEN",GetSystemMetrics(1));
 line("BIOS_MODE_DECIMAL",BiosMode() & 255);
 GetCursorPos(&old);
 start=GetTickCount();last=start-1000L;
 while(GetTickCount()-start<60000L) {
  if(PeekMessage(&msg,NULL,0,0,PM_REMOVE)) {
   TranslateMessage(&msg);DispatchMessage(&msg);
  }
  if(GetTickCount()-last>=250L) {
   last=GetTickCount();GetCursorPos(&p);
   if(n==0 || p.x!=old.x || p.y!=old.y) {
    line("SAMPLE",n++);line("ELAPSED_SECONDS",(int)((last-start)/1000L));
    line("CURSOR_X",p.x);line("CURSOR_Y",p.y);old=p;
   }
  }
 }
 line("COMPLETE",1);_lclose(logFile);return 0;
}
