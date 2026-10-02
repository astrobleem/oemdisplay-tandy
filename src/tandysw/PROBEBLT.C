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

static int cases[12][6]={
 {16,16,0,0,32,16},{65,16,1,0,31,16},{114,16,2,0,29,16},
 {163,16,3,0,27,16},{212,16,7,0,25,16},{261,16,15,0,17,16},
 {17,64,0,1,31,15},{66,64,1,2,30,14},{115,64,3,3,29,13},
 {164,64,4,4,28,12},{213,64,6,5,26,11},{262,64,7,6,25,10}
};
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
 HDC dc,mem;
 HBITMAP bitmap,previous;
 HFILE dump;
 int x,y,i,ok=1;
 logFile=_lcreat("C:\\PROBEBLT.LOG",0);
 if(logFile==HFILE_ERROR) return 1;
 line("PROBE_VERSION",4);
 line("SM_CXSCREEN",GetSystemMetrics(0));
 line("SM_CYSCREEN",GetSystemMetrics(1));
 line("BIOS_MODE_DECIMAL",BiosMode() & 255);
 if(GetSystemMetrics(0)!=320 || GetSystemMetrics(1)!=200) {
  line("WRONG_DIMENSIONS",1);_lclose(logFile);return 2;
 }
 dc=GetDC(NULL);mem=CreateCompatibleDC(dc);
 bitmap=CreateCompatibleBitmap(dc,32,16);
 line("MEMORY_DC_CREATED",mem!=0);line("BITMAP_CREATED",bitmap!=0);
 if(mem==0 || bitmap==0) {
  if(bitmap)DeleteObject(bitmap);if(mem)DeleteDC(mem);
  ReleaseDC(NULL,dc);_lclose(logFile);return 3;
 }
 previous=SelectObject(mem,bitmap);
 for(y=0;y<16;y++) for(x=0;x<32;x++)
  SetPixel(mem,x,y,colors[(x*3+y*5)&15]);
 hideCursor();fill(dc,0,0,320,200,colors[8]);
 for(i=0;i<12;i++) {
  line("CASE",i);
  x=BitBlt(dc,cases[i][0],cases[i][1],cases[i][4],cases[i][5],
           mem,cases[i][2],cases[i][3],SRCCOPY);
  line("BITBLT_RETURN",x);if(!x)ok=0;
 }
 line("ALL_BITBLT_CALLS_SUCCEEDED",ok);
 dump=_lcreat("C:\\PROBEBLT.BIN",0);
 line("DUMP_CREATED",dump!=HFILE_ERROR);
 if(dump!=HFILE_ERROR) {
  line("DUMP_32768_BYTES",_lwrite(dump,(const void _huge *)0xb8000000L,0x8000U)==0x8000U);
  _lclose(dump);
 }
 line("COMPLETE",1);_lclose(logFile);
 SelectObject(mem,previous);DeleteObject(bitmap);DeleteDC(mem);
 ReleaseDC(NULL,dc);restoreCursor();return 0;
}
