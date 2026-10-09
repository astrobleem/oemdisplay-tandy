#ifndef TSCP_H
#define TSCP_H
#define CP_OPEN 59
#define CP_FIRST 60
#define CP_COUNT 10
BOOL TSKeyboardAvailable(void);
void TSControlMenu(HMENU menu);
void TSControlPanel(HWND owner,HINSTANCE instance,int applet);
#endif
