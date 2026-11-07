#ifndef TSCP_H
#define TSCP_H
#define CP_OPEN 59
#define CP_FIRST 60
#define CP_COUNT 10
void FAR TSControlNotice(HWND owner,HINSTANCE instance,char *title,char *text);
BOOL FAR TSKeyboardAvailable(void);
void FAR TSControlMenu(HMENU menu);
void FAR TSControlPanel(HWND owner,HINSTANCE instance,int applet);
#endif
