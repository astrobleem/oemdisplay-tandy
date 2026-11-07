#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HWND shell,dialog,saver;static int phase,index,failed,busy,tries;
static char *classes[]={"TandyCubeSaver","TandyStarfieldSaver","TandyMatrixSaver","TandyOrbitsSaver","TandyCubeSaver"};
static char *modules[]={"CUBE","STARFLD","MATRIX","ORBITS","CUBE"};
static int ids[]={127,119,120,121,127};
static void ck(char *name,int ok){char b[160];HFILE f;wsprintf(b,"CHECK %s cycle=%d pass=%d\r\n",(LPSTR)name,index,ok!=0);f=_lopen("C:\\SAVERQA.LOG",OF_WRITE);if(f==HFILE_ERROR)f=_lcreat("C:\\SAVERQA.LOG",0);_llseek(f,0,2);_lwrite(f,b,lstrlen(b));_lclose(f);if(!ok)failed++;}
static void frame(void){char name[]="C:\\SAVER0.BIN";HFILE f;name[8]=(char)('0'+index);f=_lcreat(name,0);if(f!=HFILE_ERROR){_lwrite(f,(LPCSTR)MAKELONG(0,0xb800),32768U);_lclose(f);}}
static void wake(void){char b=(char)('A'+index);HFILE f=_lcreat("C:\\KEYREQ.TXT",0);if(f!=HFILE_ERROR){_lwrite(f,&b,1);_lclose(f);}}
static void finish(void){char b[70];HFILE f;wsprintf(b,"FINAL failures=%d\r\nCOMPLETE=1\r\n",failed);f=_lopen("C:\\SAVERQA.LOG",OF_WRITE);_llseek(f,0,2);_lwrite(f,b,lstrlen(b));_lclose(f);ExitWindows(0,0);}
LONG FAR PASCAL Proc(HWND w,UINT m,WPARAM wp,LPARAM lp){char b[60];int j;HWND child;
 if(m==WM_TIMER){if(busy)return 0;busy=1;
 switch(phase){
 case 0:shell=FindWindow("TandyStart",NULL);if(!shell&&++tries<12)break;ck("shell_loaded",shell!=0);ck("matching_input_loaded",GetModuleHandle("TSINPUT")!=0);PostMessage(shell,WM_COMMAND,48,0L);phase++;break;
 case 1:dialog=FindWindow(NULL,"Screen saver");if(!dialog&&++tries<18)break;ck("settings_open",dialog!=0);if(!dialog){finish();break;}
 for(j=0;j<4;j++){GetDlgItemText(dialog,ids[j],b,sizeof(b));ck("four_labels_present",b[0]!=0&&strstr(b,"Maze")==0);}phase++;break;
 case 2:SendMessage(dialog,WM_COMMAND,ids[index],MAKELONG(GetDlgItem(dialog,ids[index]),BN_CLICKED));child=GetDlgItem(dialog,124);SetActiveWindow(dialog);SetFocus(child);PostMessage(dialog,WM_COMMAND,124,MAKELONG(child,BN_CLICKED));tries=0;phase++;break;
 case 3:saver=FindWindow(classes[index],NULL);if(!saver&&++tries<12)break;ck("preview_created",saver!=0);ck("saver_module_loaded",GetModuleHandle(modules[index])!=0);ck("saver_owns_capture",saver&&GetCapture()==saver);phase++;break;
 case 4:frame();if(saver)wake();tries=0;phase++;break;
 case 5:if(GetModuleHandle(modules[index])&&++tries<12)break;ck("saver_unloaded",GetModuleHandle(modules[index])==0);ck("capture_released",GetCapture()==0);ck("settings_survive",IsWindow(dialog));ck("shell_survives",IsWindow(shell));ck("settings_restored",GetActiveWindow()==dialog);index++;if(index<5)phase=2;else{PostMessage(dialog,WM_COMMAND,IDCANCEL,0L);phase++;tries=0;}break;
 case 6:ck("settings_closed",!FindWindow(NULL,"Screen saver"));ck("shell_enabled",IsWindowEnabled(shell));tries=0;phase++;break;
 case 7:saver=FindWindow("TandyCubeSaver",NULL);if(!saver&&++tries<20)break;ck("automatic_idle_rearmed",saver!=0);ck("idle_capture_owned",saver&&GetCapture()==saver);wake();phase++;tries=0;break;
 case 8:if(GetModuleHandle("CUBE")&&++tries<12)break;ck("idle_wake_unloaded",GetModuleHandle("CUBE")==0);ck("idle_capture_released",GetCapture()==0);ck("idle_shell_survives",IsWindow(shell)&&IsWindowEnabled(shell));finish();break;
 }busy=0;return 0;}return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE i,HINSTANCE p,LPSTR c,int s){WNDCLASS wc;MSG msg;HWND w;HFILE f;f=_lcreat("C:\\SAVERQA.LOG",0);_lclose(f);memset(&wc,0,sizeof(wc));wc.lpfnWndProc=Proc;wc.hInstance=i;wc.lpszClassName="SaverQA";if(!RegisterClass(&wc))return 1;w=CreateWindow("SaverQA","",WS_POPUP,0,0,1,1,0,0,i,0);ck("primary_shell_running",FindWindow("TandyStart",NULL)!=0);SetTimer(w,1,1000,0);while(GetMessage(&msg,0,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return 0;}
