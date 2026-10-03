#define WINVER 0x0300
#include <windows.h>
#include <stdio.h>
#include <string.h>
static HINSTANCE instance;static HWND shell,pb,paint,tool;static int state,ticks,waitticks,bad;static char output[64]="C:\\ART\\TEST.BMP";
static void event(char *s){FILE *f=fopen("C:\\PBTEST.LOG","at");if(f){fprintf(f,"%lu %s\n",GetTickCount(),s);fclose(f);}}
static int copyfile(char *a,char *b){FILE *i,*o;int c,ok=1;i=fopen(a,"rb");if(!i)return 0;o=fopen(b,"wb");if(!o){fclose(i);return 0;}while((c=getc(i))!=EOF)if(putc(c,o)==EOF){ok=0;break;}if(ferror(i))ok=0;fclose(i);if(fclose(o))ok=0;return ok;}
static HWND child(HWND p,char *want){HWND w;char c[40];for(w=GetWindow(p,GW_CHILD);w;w=GetWindow(w,GW_HWNDNEXT)){GetClassName(w,c,sizeof(c));if(!lstrcmp(c,want))return w;}return NULL;}
static int layout(HWND w){HWND c;RECT r,p;POINT q;int n=0;GetWindowRect(w,&p);if(p.left<0||p.right>GetSystemMetrics(SM_CXSCREEN))return 0;GetClientRect(w,&p);for(c=GetWindow(w,GW_CHILD);c;c=GetWindow(c,GW_HWNDNEXT)){GetWindowRect(c,&r);q.x=r.left;q.y=r.top;ScreenToClient(w,&q);if(q.x<0||q.y<0||q.x+(r.right-r.left)>p.right||q.y+(r.bottom-r.top)>p.bottom)return 0;n++;}return n==7;}
static int pastepatch(void){HDC dc,mem;HBITMAP bmp,old;int ok;dc=GetDC(NULL);mem=CreateCompatibleDC(dc);bmp=CreateCompatibleBitmap(dc,8,8);if(!mem||!bmp){if(mem)DeleteDC(mem);if(bmp)DeleteObject(bmp);ReleaseDC(NULL,dc);return 0;}old=SelectObject(mem,bmp);PatBlt(mem,0,0,8,8,WHITENESS);SelectObject(mem,old);DeleteDC(mem);ReleaseDC(NULL,dc);if(!OpenClipboard(shell)){DeleteObject(bmp);return 0;}EmptyClipboard();ok=SetClipboardData(CF_BITMAP,bmp)!=NULL;CloseClipboard();if(!ok)DeleteObject(bmp);return ok;}
static void stop(HWND w,char *why){event(why);KillTimer(w,1);DestroyWindow(w);}
long FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){HWND ui,dialog;char text[160];RECT r;
 if(m==WM_TIMER){KillTimer(w,1);ticks++;if(ticks>120){stop(w,"FAIL timeout");return 0;}
  switch(state){
  case 0:event("START helper");state++;if(WinExec("C:\\GIFLOAD.EXE",SW_SHOWNORMAL)<32)stop(w,"FAIL launch helper");break;
  case 1:ui=FindWindow("GifImport",NULL);if(!ui)break;if(!layout(ui)){stop(w,"FAIL helper layout");break;}event("PASS helper controls fit");SendMessage(GetDlgItem(ui,101),WM_SETTEXT,0,(LONG)(LPSTR)"C:\\TEST.GIF");SendMessage(GetDlgItem(ui,102),WM_SETTEXT,0,(LONG)(LPSTR)output);SendMessage(ui,WM_COMMAND,103,0L);if(!copyfile(output,"C:\\BEFORE.BMP")){stop(w,"FAIL conversion output");break;}event("PASS native conversion");state++;break;
  case 2:ui=FindWindow("GifImport",NULL);if(!ui){stop(w,"FAIL missing helper");break;}SendMessage(ui,WM_COMMAND,104,0L);state++;break;
  case 3:dialog=FindWindow("#32770","Paintbrush");if(dialog){GetWindowText(child(dialog,"Static"),text,sizeof(text));event(text);stop(w,"FAIL Paintbrush dialog");break;}pb=FindWindow("pbParent",NULL);if(!pb)break;GetWindowText(pb,text,sizeof(text));event(text);if(!strstr(text,"TEST.BMP")){stop(w,"FAIL Paintbrush title");break;}paint=child(pb,"pbPaint");tool=child(pb,"pbTool");if(!paint||!tool){stop(w,"FAIL Paintbrush children");break;}GetClientRect(paint,&r);sprintf(text,"PAINT_CLIENT %d %d",r.right,r.bottom);event(text);event("PASS opened BMP");state++;break;
  case 4:if(!pastepatch()){stop(w,"FAIL clipboard patch");break;}SendMessage(pb,WM_COMMAND,204,0L);event("EDIT native Paste of 8x8 white bitmap");state++;break;
  case 5:SendMessage(pb,WM_COMMAND,103,0L);event("SAVE command");state++;break;
  case 6:if(!copyfile(output,"C:\\EDITED.BMP")){stop(w,"FAIL saved output");break;}SendMessage(pb,WM_CLOSE,0,0L);event("CLOSE after save");state++;break;
  case 7:if(FindWindow("pbParent",NULL))break;state++;if(WinExec("C:\\GIFLOAD.EXE",SW_SHOWNORMAL)<32)stop(w,"FAIL launch helper");break;
  case 8:ui=FindWindow("GifImport",NULL);if(!ui)break;SendMessage(GetDlgItem(ui,102),WM_SETTEXT,0,(LONG)(LPSTR)output);SendMessage(ui,WM_COMMAND,104,0L);state++;break;
  case 9:if(FindWindow("#32770","Paintbrush")){stop(w,"FAIL reopen dialog");break;}pb=FindWindow("pbParent",NULL);if(!pb)break;GetWindowText(pb,text,sizeof(text));event(text);if(!strstr(text,"TEST.BMP")){stop(w,"FAIL reopen title");break;}event("PASS reopened edited BMP");state++;break;
  case 10:if(++waitticks<3)break;SendMessage(pb,WM_COMMAND,103,0L);event("SAVE reopened BMP");state++;break;
  case 11:SendMessage(pb,WM_CLOSE,0,0L);state++;break;
  case 12:if(FindWindow("pbParent",NULL))break;stop(w,"PASS workflow; verify pixels externally");break;
  }if(IsWindow(w))SetTimer(w,1,100,NULL);return 0;}
 if(m==WM_DESTROY){PostQuitMessage(0);return 0;}return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;MSG msg;FILE *f;char guard[32];instance=inst;f=fopen("C:\\GIFTEST.TAG","rt");if(!f)return 3;guard[0]=0;fgets(guard,sizeof(guard),f);fclose(f);if(strncmp(guard,"ISOLATED GIF TEST",17))return 3;if(cmd[0]=='R')lstrcpy(output,"C:\\TEST.BMP");if(cmd[0]=='D')output[0]='D';f=fopen("C:\\PBTEST.LOG","wt");if(!f)return 1;fclose(f);event("BEGIN automated native UI test");wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="GifPBTest";if(!RegisterClass(&wc))return 2;shell=CreateWindow("GifPBTest","GIF Paintbrush Test",WS_OVERLAPPED,0,0,10,10,NULL,NULL,inst,NULL);SetTimer(shell,1,100,NULL);while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return 0;}
