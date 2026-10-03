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
    HDC dc;
    POINT pt;
    logFile=_lcreat("C:\\PROBE.LOG",0);
    if(logFile==HFILE_ERROR) return 1;
    line("PROBE_VERSION",1);
    line("SM_CXSCREEN",GetSystemMetrics(0));
    line("SM_CYSCREEN",GetSystemMetrics(1));
    dc=GetDC(NULL);
    line("HORZRES",GetDeviceCaps(dc,8));
    line("VERTRES",GetDeviceCaps(dc,10));
    line("BITSPIXEL",GetDeviceCaps(dc,12));
    line("PLANES",GetDeviceCaps(dc,14));
    line("NUMCOLORS",GetDeviceCaps(dc,24));
    line("BIOS_MODE_DECIMAL",BiosMode() & 255);
    GetCursorPos(&pt);
    line("CURSOR_X",pt.x);
    line("CURSOR_Y",pt.y);
    ReleaseDC(NULL,dc);
    line("COMPLETE",1);
    _lclose(logFile);
    return 0;
}
