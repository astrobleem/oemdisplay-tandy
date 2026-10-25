/* Enable/remove the helper without asking users to edit WIN.INI. */
#include <windows.h>
static char path[128];
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 char old[512],out[512],token[512];int i=0,j=0,k,off,found=0;HWND h;
 if(!GetModuleFileName(inst,path,sizeof(path)))return 5;
 for(k=lstrlen(path)-1;k>=0 && path[k]!='\\';k--);path[k+1]=0;lstrcat(path,"XTPAN.EXE");
 off=lstrcmpi(cmd,"OFF")==0;
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
