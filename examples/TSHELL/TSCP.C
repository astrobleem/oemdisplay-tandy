/* Windows 3.0 Control Panel has built-in applets, not Win3.1 CPL files.
   Its WinMain ignores lpCmdLine. Use the installed native Settings menu,
   checking both caption and enabled state before posting its command. */
#define WINVER 0x0300
#include <windows.h>
#include "TNOTICE.H"
#include "TSCP.H"
static char *cpNames[]={"&Color...","&Desktop...","Date/&Time...",
 "&Fonts...","&International...","&Keyboard...","&Mouse...",
 "P&orts...","&Printers...","&Sound..."};
static WORD cpCommands[]={0,8,7,2,3,5,6,4,1,9};
/* Match CONTROL.EXE KEYBOARDDLG's read-only capability test exactly:
   loaded KEYBOARD module, SetSpeed export, argument -1, -1 means absent.
   Never set a repeat rate or load an extra driver to probe support. */
typedef int (FAR PASCAL *CPKEYSPEED)(int);
BOOL TSKeyboardAvailable(void)
{
 HANDLE keyboard;CPKEYSPEED speed;
 keyboard=GetModuleHandle("KEYBOARD");
 if(!keyboard)return FALSE;
 speed=(CPKEYSPEED)GetProcAddress(keyboard,"SetSpeed");
 return speed && (*speed)(-1)!=-1;
}
void TSControlMenu(HMENU menu)
{
 int i;BOOL keyboard=TSKeyboardAvailable();
 AppendMenu(menu,MF_STRING,CP_OPEN,"Control &Panel...");
 AppendMenu(menu,MF_SEPARATOR,0,NULL);
 for(i=0;i<CP_COUNT;i++)
  AppendMenu(menu,MF_STRING|((i==5 && !keyboard)?MF_GRAYED:0),CP_FIRST+i,cpNames[i]);
}
void TSControlPanel(HWND owner,HINSTANCE instance,int applet)
{
 HWND panel;HMENU settings;OFSTRUCT of;UINT result;WORD state;int length,count,pos,found;
 char path[144],caption[48],message[80];
 if(applet < -1 || applet>=CP_COUNT)return;
 panel=FindWindow("CtlPanelClass",NULL);
 if(!panel){
  /* Use this installation's CONTROL.EXE, never a command-line CPL guess. */
  length=GetWindowsDirectory(path,128);
  if(!length || length>=128){
   TinyNotice(owner,instance,"Settings","Windows path unavailable.");return;
  }
  lstrcat(path,"\\CONTROL.EXE");
  if(OpenFile(path,&of,OF_EXIST)==HFILE_ERROR){
   TinyNotice(owner,instance,"Settings","CONTROL.EXE not found.\nInstall Control Panel.");return;
  }
  result=WinExec(path,SW_SHOWNORMAL);
  if(result<32){
   wsprintf(message,"Control Panel failed.\nError %u.",result);
   TinyNotice(owner,instance,"Settings",message);return;
  }
  /* WinExec yields until the new task calls GetMessage. Win3.0 creates
     CtlPanelClass and its menu before that point. No resident helper. */
  panel=FindWindow("CtlPanelClass",NULL);
 }
 if(!panel){
  TinyNotice(owner,instance,"Settings","Use Control Panel's\nSettings menu.");return;
 }
 /* A stock applet can already be modal: do not queue another behind it. */
 if(!IsWindowEnabled(panel)){
  HWND dialog=GetLastActivePopup(panel);
  TinyNotice(owner,instance,"Settings","Close the open applet,\nthen choose Settings.");
  if(dialog && IsWindowEnabled(dialog)){
   BringWindowToTop(dialog);SetActiveWindow(dialog);
  }
  return;
 }
 ShowWindow(panel,SW_RESTORE);BringWindowToTop(panel);SetActiveWindow(panel);
 if(applet==-1)return;
 if(applet==5 && !TSKeyboardAvailable()){
  TinyNotice(owner,instance,"Settings","Keyboard speed\nunavailable.\nUse Control Panel.");return;
 }
 settings=GetSubMenu(GetMenu(panel),0);
 count=settings?GetMenuItemCount(settings):0;found=0;
 /* Win3.0 ID lookup can return the unnamed separator for Color's ID 0.
    Inspect bounded positions, verifying caption AND command ID together. */
 if(count>0 && count<=32)for(pos=0;pos<count;pos++){
  state=GetMenuState(settings,pos,MF_BYPOSITION);caption[0]=0;
  if(state==0xffff || (state&(MF_GRAYED|MF_DISABLED|MF_POPUP|MF_SEPARATOR)))continue;
  if(GetMenuItemID(settings,pos)!=cpCommands[applet])continue;
  GetMenuString(settings,pos,caption,sizeof(caption),MF_BYPOSITION);
  if(!lstrcmpi(caption,cpNames[applet])){found=1;break;}
 }
 if(!found){
  TinyNotice(owner,instance,"Settings","Applet unavailable.\nUse Control Panel.");return;
 }
 if(!PostMessage(panel,WM_COMMAND,cpCommands[applet],0L))
  TinyNotice(owner,instance,"Settings","Applet could not open.\nUse Control Panel.");
}
