/* Identical small shell for fixed/panned free-memory comparisons. */
#include <windows.h>
static HFILE f;
static void line(char *k,LONG v){char b[100];int n=wsprintf(b,"%s=%ld\r\n",(LPSTR)k,v);_lwrite(f,b,n);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 HDC d=GetDC(NULL);f=_lcreat("C:\\SPTEST.LOG",0);if(f==HFILE_ERROR || !d)return 1;
 line("HORZRES",GetDeviceCaps(d,HORZRES));line("VERTRES",GetDeviceCaps(d,VERTRES));
 line("FREE_START",GetFreeSpace(0));line("COMPLETE",1);ReleaseDC(NULL,d);_lclose(f);return 0;
}
