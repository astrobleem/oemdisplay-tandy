#define WINVER 0x0300
#include <windows.h>
#include <dos.h>
#include <direct.h>
/* Windows 3.0 searches CWD, not the EXE directory, for CDTEST's import.
   Change only this task's directory around WinExec, then restore both drives. */
static int exists(char *p){HFILE f;f=_lopen(p,OF_READ);if(f==HFILE_ERROR)return 0;_lclose(f);return 1;}
static int error(char *p,int rc){MessageBox(NULL,p,"CDSTART",MB_OK|MB_ICONEXCLAMATION);return rc;}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){
 char dir[144],exe[160],dll[160],old[144],prior[144];
 unsigned olddrive;UINT n,result;int i,drive,restored,entered;
 if(cmd[0])return error("Run CDSTART\nwith no switches.",1);
 if(GetModuleHandle("COMMDLG"))return error("COMMDLG in use.\nClose its apps,\nthen retry.",2);
 n=GetModuleFileName(inst,dir,sizeof(dir));
 if(n==0||n>=sizeof(dir)-1||dir[1]!=':')return error("Cannot locate\nthis folder.",3);
 for(i=n-1;i>=0&&dir[i]!='\\';i--);
 if(i<2)return error("Cannot locate\nthis folder.",3);
 dir[i+1]=0;lstrcpy(exe,dir);lstrcat(exe,"CDTEST.EXE");lstrcpy(dll,dir);lstrcat(dll,"COMMDLG.DLL");if(i>2)dir[i]=0;
 if(!exists(exe)||!exists(dll))return error("Keep these here:\nCDSTART.EXE\nCDTEST.EXE\nCOMMDLG.DLL",4);
 drive=dir[0];if(drive>='a'&&drive<='z')drive-=32;drive=drive-'A'+1;
 if(drive<1||drive>26)return error("Cannot locate\nthis drive.",3);
 _dos_getdrive(&olddrive);
 if(!getcwd(old,sizeof(old))||!_getdcwd(drive,prior,sizeof(prior)))return error("Cannot save\ndirectories.",5);
 entered=(_chdrive(drive)==0);if(entered)entered=(chdir(dir)==0);
 result=entered?WinExec(exe,SW_SHOWNORMAL):0;
 restored=(chdir(prior)==0);restored=(_chdrive((int)olddrive)==0)&&restored;restored=(chdir(old)==0)&&restored;
 if(!restored)return error("Restore failed.\nClose the demo;\ncheck the drive.",6);
 if(!entered)return error("Cannot enter\ndemo folder.",7);
 if(result<32)return error("CDTEST failed.\nCheck its DLL;\nclose other apps.",8);
 return 0;
}
