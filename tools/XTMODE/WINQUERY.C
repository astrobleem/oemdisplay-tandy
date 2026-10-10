/* Original test-only Windows 3.0 real-mode guard query. MIT license.
 * Run as the initial app: WIN /R WINQUERY. No configuration writes.
 */
#define WINVER 0x0300
#include <windows.h>
extern unsigned far query(unsigned value);
int PASCAL WinMain(HINSTANCE current,HINSTANCE prior,LPSTR args,int show)
{
 HFILE f;DWORD flags;unsigned a,b,n;char line[120];
 (void)current;(void)prior;(void)args;(void)show;
 flags=GetWinFlags();a=query(0x1600);b=query(0x4680);
 n=(unsigned)wsprintf(line,"NATIVE WIN16 flags=%04x:%04x AX1600=%04x AX4680=%04x\r\nDONE\r\n",(unsigned)(flags>>16),(unsigned)flags,a,b);
 f=_lcreat("C:\\WINQUERY.LOG",0);if(f==HFILE_ERROR)return 1;
 if(_lwrite(f,line,n)!=n){_lclose(f);return 2;}_lclose(f);return 0;
}
