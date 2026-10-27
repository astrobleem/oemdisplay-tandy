/* Token lists belong to Windows; preserve unrelated programs and arguments. */
#include <assert.h>
#include <string.h>
#include "PANSTART.H"
int main(void)
{
 char out[512],small[4];
 assert(PanStartupEdit("clock.exe, C:\\OLD\\XTPAN.EXE note.exe",0,out,sizeof(out)));
 assert(!strcmp(out,"clock.exe note.exe"));
 assert(PanStartupEdit("C:\\OLD\\XYCTL.EXE, \"D:\\MY APPS\\clock.exe\",keep.exe","C:\\WINDOWS\\PANCTL.EXE",out,sizeof(out)));
 assert(!strcmp(out,"\"D:\\MY APPS\\clock.exe\",keep.exe C:\\WINDOWS\\PANCTL.EXE"));
 assert(PanStartupEdit("MYXTPAN.EXE XTPAN.EXEX XTPAN.EXE",0,out,sizeof(out)));
 assert(!strcmp(out,"MYXTPAN.EXE XTPAN.EXEX"));
 assert(PanStartupEdit("xtpan.exe,xyctl.exe,panctl.exe,cgactl.exe,pancfg.exe",0,out,sizeof(out)));
 assert(!*out);
 assert(PanStartupEdit("\"C:\\old pan\\XTPAN.EXE\" clock.exe",0,out,sizeof(out)));
 assert(!strcmp(out,"clock.exe"));
 assert(!PanStartupEdit("\"unterminated",0,out,sizeof(out)));
 assert(!PanStartupEdit("clock.exe",0,small,sizeof(small)));
 assert(!PanStartupEdit("abc","d",small,sizeof(small)));
 assert(PanStartupEdit("abc",0,small,sizeof(small))&&!strcmp(small,"abc"));
 return 0;
}
