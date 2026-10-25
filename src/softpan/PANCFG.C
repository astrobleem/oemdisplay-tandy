/* Enable/remove the helper without asking users to edit WIN.INI. */
#include <windows.h>
#include "PANSET.H"
static char path[128];
static void CopyArg(char *d,LPSTR s,int cap){int i=0;while(s[i] && i<cap-1){d[i]=s[i];i++;}d[i]=0;}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 char old[512],out[512],token[512],arg[24],run[160];int i=0,j=0,k,off,found=0,kind;HWND h,h2;
 if(!GetModuleFileName(inst,path,sizeof(path)))return 5;
 for(k=lstrlen(path)-1;k>=0 && path[k]!='\\';k--);path[k+1]=0;lstrcat(path,"XTPAN.EXE");
 CopyArg(arg,cmd,sizeof(arg));kind=PanCmdParse(arg);
 if(kind==PS_CMD_SETTINGS){
  /* Settings never touch load= or Enabled: only reach the running owner. */
  h=FindWindow("XTPan",NULL);
  if(!h && (h2=FindWindow("XYOverviewControl",NULL))!=NULL){PostMessage(h2,RegisterWindowMessage(PS_MSG_XY),0,0L);return 0;}
  switch(PanRoute(h!=NULL,GetProfileInt("XTPan","Enabled",1)!=0)){
  case PS_ROUTE_POST:PostMessage(h,RegisterWindowMessage(PS_MSG_VERT),0,0L);return 0;
  case PS_ROUTE_START:lstrcpy(run,path);lstrcat(run," " PS_ARG_SETTINGS);
   if(WinExec(run,SW_SHOWNORMAL)<32)return 4;return 0;
  }
  MessageBox(NULL,"XTPAN panning is turned off. Run PANCFG to turn it on, then PANCFG SETTINGS.","Panning settings",MB_OK|MB_ICONINFORMATION);
  return 7;
 }
 off=kind==PS_CMD_OFF;
 if(GetProfileString("windows","load","",old,sizeof(old))>=sizeof(old)-1)return 1;
 while(old[i]){
  while(old[i]==' ' || old[i]=='\t')i++;k=0;
  while(old[i] && old[i]!=' ' && old[i]!='\t')token[k++]=old[i++];token[k]=0;
  if(!k)break;
  if(!lstrcmpi(token,path)){found=1;if(off)continue;}
  if(j)out[j++]=' ';for(k=0;token[k];k++)out[j++]=token[k];
 }
 if(!off && !found){if(j+lstrlen(path)+2>=sizeof(out))return 2;if(j)out[j++]=' ';for(k=0;path[k];k++)out[j++]=path[k];}
 out[j]=0;if(!WriteProfileString("windows","load",out))return 3;
 if(!off && !WriteProfileString("XTPan","Enabled","1"))return 6;
 if(off){h=FindWindow("XTPan",NULL);if(h)PostMessage(h,WM_CLOSE,0,0L);}
 else if(!FindWindow("XTPan",NULL) && WinExec(path,SW_SHOWNORMAL)<32)return 4;
 return 0;
}
