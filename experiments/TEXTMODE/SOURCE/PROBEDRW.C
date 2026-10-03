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

static COLORREF colors[16]={
 RGB(0,0,0), RGB(0,0,128), RGB(0,128,0), RGB(0,128,128),
 RGB(128,0,0), RGB(128,0,128), RGB(128,128,0), RGB(128,128,128),
 RGB(64,64,64), RGB(0,0,255), RGB(0,255,0), RGB(0,255,255),
 RGB(255,0,0), RGB(255,0,255), RGB(255,255,0), RGB(255,255,255)
};
static void fill(HDC dc,int l,int t,int r,int b,COLORREF c)
{
 HBRUSH brush;
 RECT rect;
 rect.left=l;rect.top=t;rect.right=r;rect.bottom=b;
 brush=CreateSolidBrush(c);FillRect(dc,&rect,brush);DeleteObject(brush);
}
static int hideCount;
static HCURSOR previousCursor;
static void hideCursor(void)
{
 int count;
 hideCount=0;
 do { count=ShowCursor(FALSE);hideCount++; } while(count>=0 && hideCount<32);
 previousCursor=SetCursor(NULL);
 line("CURSOR_HIDE_CALLS",hideCount);
 line("CURSOR_SHOW_COUNT",count);
}
static void restoreCursor(void)
{
 SetCursor(previousCursor);
 while(hideCount>0) {ShowCursor(TRUE);hideCount--;}
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 HDC dc;
 HFILE dump;
 int i;
 logFile=_lcreat("C:\\PROBEDRW.LOG",0);
 if(logFile==HFILE_ERROR) return 1;
 line("PROBE_VERSION",2);
 dc=GetDC(NULL);
 line("SM_CXSCREEN",GetSystemMetrics(0));
 line("SM_CYSCREEN",GetSystemMetrics(1));
 line("HORZRES",GetDeviceCaps(dc,8));
 line("VERTRES",GetDeviceCaps(dc,10));
 line("BITSPIXEL",GetDeviceCaps(dc,12));
 line("PLANES",GetDeviceCaps(dc,14));
 line("NUMCOLORS",GetDeviceCaps(dc,24));
 line("BIOS_MODE_DECIMAL",BiosMode() & 255);
 if(GetSystemMetrics(0)!=320 || GetSystemMetrics(1)!=200) {
  line("WRONG_DIMENSIONS",1); ReleaseDC(NULL,dc);_lclose(logFile);return 2;
 }
 hideCursor();
 fill(dc,0,0,320,200,colors[0]);
 for(i=0;i<16;i++) fill(dc,i*20,32,(i+1)*20,168,colors[i]);
 fill(dc,0,0,320,1,colors[15]);
 fill(dc,0,199,320,200,colors[15]);
 fill(dc,0,0,1,200,colors[15]);
 fill(dc,319,0,320,200,colors[15]);
 fill(dc,1,1,9,9,colors[12]);
 fill(dc,311,1,319,9,colors[10]);
 fill(dc,1,191,9,199,colors[9]);
 fill(dc,311,191,319,199,colors[14]);
 dump=_lcreat("C:\\PROBEDRW.BIN",0);
 line("DUMP_CREATED",dump!=HFILE_ERROR);
 if(dump!=HFILE_ERROR) {
  line("DUMP_32768_BYTES",_lwrite(dump,(const void _huge *)0xb8000000L,0x8000U)==0x8000U);
  _lclose(dump);
 }
 line("COMPLETE",1);
 _lclose(logFile);
 ReleaseDC(NULL,dc);
 restoreCursor();
 return 0;
}
