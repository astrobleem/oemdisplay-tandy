#define WINVER 0x0300
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <direct.h>
#include "GIFCORE.H"
static HINSTANCE instance;
static HWND input,output,status;
static int mode;
static char inpath[128]="C:\\TEST.GIF",outpath[128]="C:\\TEST.BMP";
static void label(HWND w,char *s,int x,int y,int width){CreateWindow("STATIC",s,WS_CHILD|WS_VISIBLE,x,y,width,12,w,NULL,instance,NULL);}
static int convert(HWND w) {
 GetWindowText(input,inpath,sizeof(inpath));GetWindowText(output,outpath,sizeof(outpath));
 SetWindowText(status,"Converting...");UpdateWindow(w);
 if(!gifconvert(inpath,outpath,mode)){SetWindowText(status,giferror());return 0;}
 SetWindowText(status,"Saved. Open BMP in Paintbrush.");return 1;
}
/* Paintbrush 3.0 opens the basename in its inherited directory. Resolve both
 * paths, inherit the BMP directory, and then restore the caller's drive state.
 */
static int openbmp(void) {
 char full[128],dir[128],prior[128],cmd[270],*name;int olddrive,drive,result,restored;
 GetWindowText(output,outpath,sizeof(outpath));
 if(strchr(outpath,' ')||strchr(outpath,'"')||!_fullpath(full,outpath,sizeof(full))){SetWindowText(status,"Use a valid DOS path without spaces.");return 0;}
 name=strrchr(full,'\\');if(!name||full[1]!=':'){SetWindowText(status,"Use a full DOS path.");return 0;}
 lstrcpy(dir,full);dir[name-full==2?3:name-full]=0;name++;
 olddrive=_getdrive();drive=(full[0]&~32)-'A'+1;
 if(!_getdcwd(drive,prior,sizeof(prior))){SetWindowText(status,"Cannot read drive directory.");return 0;}
 if(_chdrive(drive)||chdir(dir)){_chdrive(olddrive);SetWindowText(status,"Cannot enter BMP directory.");return 0;}
 GetWindowsDirectory(cmd,128);lstrcat(cmd,"\\PBRUSH.EXE ");lstrcat(cmd,name);
 result=WinExec(cmd,SW_SHOWNORMAL);
 restored=chdir(prior)==0;restored=(_chdrive(olddrive)==0)&&restored;
 if(!restored){SetWindowText(status,"Could not restore directory.");return 0;}
 if(result<32){SetWindowText(status,"Paintbrush could not start.");return 0;}
 return 1;
}
long FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){
 HDC dc;int colors,width,cw;RECT r;
 switch(m){
 case WM_CREATE:
 dc=GetDC(w);colors=GetDeviceCaps(dc,NUMCOLORS);width=GetDeviceCaps(dc,HORZRES);ReleaseDC(w,dc);
 mode=colors==2?2:colors==4?(width==640?5:4):16;
 GetClientRect(w,&r);cw=r.right-6;
 label(w,"GIF input path:",3,3,cw);
 input=CreateWindow("EDIT",inpath,WS_CHILD|WS_VISIBLE|WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP,3,17,cw,19,w,(HMENU)101,instance,NULL);
 label(w,"New BMP path:",3,40,cw);
 output=CreateWindow("EDIT",outpath,WS_CHILD|WS_VISIBLE|WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP,3,54,cw,19,w,(HMENU)102,instance,NULL);
 SendMessage(input,EM_LIMITTEXT,127,0L);SendMessage(output,EM_LIMITTEXT,127,0L);
 CreateWindow("BUTTON","Convert",WS_CHILD|WS_VISIBLE|WS_TABSTOP,3,80,70,22,w,(HMENU)103,instance,NULL);
 CreateWindow("BUTTON","Open BMP",WS_CHILD|WS_VISIBLE|WS_TABSTOP,76,80,70,22,w,(HMENU)104,instance,NULL);
 status=CreateWindow("STATIC","GIF single image, max 320x200",WS_CHILD|WS_VISIBLE,3,108,cw,32,w,NULL,instance,NULL);
 return 0;
 case WM_COMMAND:
 if(wp==103)convert(w);
 if(wp==104&&openbmp())DestroyWindow(w);
 return 0;
 case WM_DESTROY:PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){
 WNDCLASS wc;HWND w;MSG msg;FILE *f;long before,after;int n,expect,want,got,failures=0;FILE *manifest;char line[80],src[32],dst[32];
 instance=inst;
 /* Automated native core verification without desktop input. */
 if(cmd[0]=='/'&&cmd[1]=='T'){
 before=GetFreeSpace(0);manifest=fopen("C:\\CASES.TXT","rt");f=fopen("C:\\GIFTEST.LOG","wt");
 if(!manifest||!f)return 3;
 while(fgets(line,sizeof(line),manifest)){
  if(sscanf(line,"%d %d %d",&n,&want,&expect)!=3){failures++;break;}
  sprintf(src,"C:\\F%03d.GIF",n);sprintf(dst,"C:\\O%03d.BMP",n);
  got=gifconvert(src,dst,want);if(got!=expect)failures++;
  fprintf(f,"CASE %d %d %d %s\n",n,got,expect,giferror());
 }
 fclose(manifest);after=GetFreeSpace(0);
 fprintf(f,"%s\nFREE_BEFORE=%ld\nFREE_AFTER=%ld\n",failures?"FAIL":"PASS",before,after);fclose(f);return failures?1:0;}

 if(!prev){wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="GifImport";if(!RegisterClass(&wc))return 1;}
 w=CreateWindow("GifImport","GIF to BMP",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,0,0,GetSystemMetrics(SM_CXSCREEN)<310?GetSystemMetrics(SM_CXSCREEN):310,175,NULL,NULL,inst,NULL);if(!w)return 2;ShowWindow(w,show);UpdateWindow(w);SetFocus(input);
 while(GetMessage(&msg,NULL,0,0)){if(!IsDialogMessage(w,&msg)){TranslateMessage(&msg);DispatchMessage(&msg);}}return msg.wParam;
}
