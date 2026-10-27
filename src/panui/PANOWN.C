#include <windows.h>
#include "PANOWN.H"
static const char *classes[5]={"","XTPan","XYOverviewControl","CGAPan","CGASlide"};
static const char *programs[5]={"","XTPAN.EXE","XYCTL.EXE","PANCTL.EXE","CGACTL.EXE"};
static const char *messages[5]={"","XTPanSettings","XYPanSettings","CGAPanSettings","CGAWindowSettings"};
HWND PanOwnerFind(int *kind)
{
 HWND w;int i;
 for(i=1;i<=4;i++)if((w=FindWindow((LPSTR)classes[i],0))!=0){if(kind)*kind=i;return w;}
 if(kind)*kind=PN_NONE;return 0;
}
WORD PanOwnerMessage(int kind)
{return kind>0 && kind<=4?RegisterWindowMessage((LPSTR)messages[kind]):0;}
const char *PanOwnerExe(int kind)
{return kind>0 && kind<=4?programs[kind]:programs[0];}
int PanOwnerRoute(int settings)
{
 int kind;HWND w=PanOwnerFind(&kind);
 if(!w)return 0;
 if(settings)PostMessage(w,PanOwnerMessage(kind),0,0L);
 else if(IsWindowVisible(w)){if(IsIconic(w))ShowWindow(w,SW_RESTORE);BringWindowToTop(w);}
 return 1;
}
int PanOwnerDetect(int *fixed)
{
 HDC dc;int q=-1,in[2],out[6],w,h,colors,kind=PN_NONE;
 if(fixed)*fixed=0;dc=GetDC(0);if(!dc)return PN_NONE;
 w=GetDeviceCaps(dc,HORZRES);h=GetDeviceCaps(dc,VERTRES);colors=GetDeviceCaps(dc,NUMCOLORS);
 if(Escape(dc,0x5850,2,(LPSTR)&q,(LPSTR)out)>0 && (w==320 || w==640) &&
    out[0]>=0 && out[1]==200 && out[2]==400)kind=PN_VERT;
 else{
  in[0]=-1;in[1]=0;
  if(Escape(dc,0x5860,4,(LPSTR)in,(LPSTR)out)>0){
   if(w==640 && (h==256 || h==400) && out[2]==320 && out[3]==200 && out[4]==640 && out[5]==h)kind=PN_XY;
   else if(w==320 && h==200 && colors==16 && out[2]==160 && out[3]==100 && out[4]==320 && out[5]==200)kind=PN_CGA;
  }else if(w==160 && h==100 && colors==16)kind=PN_FIXED;
  else if((w==160 || w==320 || w==640) && h==200){kind=PN_VERT;if(fixed)*fixed=1;}
 }
 ReleaseDC(0,dc);return kind;
}
static int Exists(const char *path)
{
 OFSTRUCT of;return OpenFile((LPSTR)path,&of,OF_EXIST)!=HFILE_ERROR;
}
int PanOwnerPath(HINSTANCE instance,int kind,char *path,int cap)
{
 int i,n;const char *name=PanOwnerExe(kind);
 n=GetModuleFileName(instance,path,cap);
 if(!n || n>=cap || !name[0])return 0;
 for(i=n-1;i>=0 && path[i]!='\\';i--);
 if(i<0 || i+1+lstrlen((LPSTR)name)>=cap)return 0;
 path[i+1]=0;lstrcat(path,(LPSTR)name);
 if(Exists(path))return 1;
 n=GetWindowsDirectory(path,cap);
 if(!n || n+1+lstrlen((LPSTR)name)>=cap)return 0;
 if(path[n-1]!='\\')lstrcat(path,"\\");
 lstrcat(path,(LPSTR)name);return Exists(path);
}
