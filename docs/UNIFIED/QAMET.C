#define WINVER 0x0300
#include <windows.h>
int PASCAL WinMain(HINSTANCE h,HINSTANCE p,LPSTR cmd,int show) {
 HDC dc;HFILE f;TEXTMETRIC tm;HFONT old;char s[512];
 dc=GetDC(NULL); old=SelectObject(dc,GetStockObject(SYSTEM_FONT));GetTextMetrics(dc,&tm);
 wsprintf(s,"FLAGS=%u SCREEN=%dx%d BITS=%d PLANES=%d COLORS=%d DPI=%dx%d FONT=%dx%d ASCENT=%d\r\n",(unsigned)GetWinFlags(),GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),GetDeviceCaps(dc,BITSPIXEL),GetDeviceCaps(dc,PLANES),GetDeviceCaps(dc,NUMCOLORS),GetDeviceCaps(dc,LOGPIXELSX),GetDeviceCaps(dc,LOGPIXELSY),tm.tmAveCharWidth,tm.tmHeight,tm.tmAscent);
 f=_lcreat("C:\\QAMET.LOG",0);if(f!=HFILE_ERROR){_lwrite(f,s,lstrlen(s));_lclose(f);} SelectObject(dc,old);ReleaseDC(NULL,dc);return 0;
}
