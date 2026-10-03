#define WINVER 0x0300
#include <windows.h>
extern unsigned FAR PASCAL BiosMode(void);
static HFILE logf;
static HWND window;
static int step;
static HWND notepad,edit;
static BYTE beforeCells[4000];
static void line(char *key,LONG value) {
 char out[100],digits[12];int n=0,d=0;DWORD v;
 while(*key)out[n++]=*key++;out[n++]='=';
 if(value<0){out[n++]='-';v=(DWORD)(-value);}else v=(DWORD)value;
 do{digits[d++]=(char)('0'+v%10);v/=10;}while(v);
 while(d)out[n++]=digits[--d];out[n++]='\r';out[n++]='\n';
 _lwrite(logf,out,n);_lclose(logf);logf=_lopen("C:\\TXPROBE.LOG",OF_WRITE);_llseek(logf,0L,2);
}
static void dump(char *name,void FAR *p,UINT n) {HFILE f=_lcreat(name,0);if(f!=HFILE_ERROR){_lwrite(f,p,n);_lclose(f);}}
static void snapshot(char *name) {dump(name,(void FAR*)0xb8000000L,4000);}
static void restoretest(void){HDC dc,mem;HBITMAP bm,old;HBRUSH br;RECT r;BYTE FAR *v=(BYTE FAR*)0xb8000000L;int i,diff=0;DWORD colors[8];
 dc=GetDC(NULL);mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,128,24);if(!mem||!bm){line("RESTORE_ALLOC",0);return;}
 GetWindowRect(edit,&r);r.right=r.left+128;r.bottom=r.top+24;
 old=SelectObject(mem,bm);BitBlt(mem,0,0,128,24,dc,r.left,r.top,SRCCOPY);
 for(i=0;i<8;i++)colors[i]=GetPixel(dc,r.left+i*7,r.top+7);
 for(i=0;i<4000;i++)beforeCells[i]=v[i];snapshot("C:\\TXSAVE.BIN");
 br=GetStockObject(WHITE_BRUSH);FillRect(dc,&r,br);BitBlt(dc,r.left,r.top,128,24,mem,0,0,SRCCOPY);
 for(i=0;i<8;i++)if(colors[i]!=GetPixel(dc,r.left+i*7,r.top+7))diff++;line("RESTORE_PIXEL_MISMATCHES",diff);diff=0;
 for(i=0;i<4000;i++)if(v[i]!=beforeCells[i])diff++;line("RESTORE_CELL_BYTE_DIFFERENCES",diff);snapshot("C:\\TXREST.BIN");
 SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);ReleaseDC(NULL,dc);
}
static void tests(void) {
 HDC dc,mem;HBITMAP bm,old;TEXTMETRIC tm;DWORD expected[16];int i,bad=0;HBRUSH br,ob;
 dc=GetDC(NULL);GetTextMetrics(dc,&tm);line("SYS_AVG_WIDTH",tm.tmAveCharWidth);line("SYS_MAX_WIDTH",tm.tmMaxCharWidth);line("SYS_FONT_HEIGHT",tm.tmHeight);line("WIDTH",GetDeviceCaps(dc,HORZRES));line("HEIGHT",GetDeviceCaps(dc,VERTRES));
 line("COLORS",GetDeviceCaps(dc,NUMCOLORS));line("MODE",BiosMode()&255);
 line("MEMORY_KB",*((WORD FAR*)0x00400013L));line("BDA_MODE",*((BYTE FAR*)0x00400049L));
 line("COLUMNS",*((WORD FAR*)0x0040004aL));line("PAGE_BYTES",*((WORD FAR*)0x0040004cL));
 dump("C:\\TXROM.BIN",(void FAR*)0xf000fa6eL,1024);
 dump("C:\\TXBDA.BIN",(void FAR*)0x00400000L,256);
 snapshot("C:\\TXDESK.BIN");
 dump("C:\\TXEXT.BIN",(void FAR*)*((DWORD FAR*)0x0000007cL),1024);
 line("PROGMAN_HWND",FindWindow("Progman",NULL));
 line("PROGMAN_MODULE",GetModuleHandle("PROGMAN"));
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,32,16);line("SAVE_DDB",bm!=NULL);
 if(mem&&bm) {
 old=SelectObject(mem,bm);BitBlt(mem,0,0,32,16,dc,0,176,SRCCOPY);
 for(i=0;i<16;i++){SetPixel(dc,i,176+(i%8),(i&1)?RGB(255,255,255):RGB(0,0,0));expected[i]=GetPixel(dc,i,176+(i%8));if(expected[i]!=((i&1)?RGB(255,255,255):RGB(0,0,0)))bad++;}
 line("PIXEL_MISMATCHES",bad);bad=0;
 br=CreateSolidBrush(RGB(255,255,255));ob=SelectObject(dc,br);
 PatBlt(dc,0,176,32,16,PATINVERT);PatBlt(dc,0,176,32,16,PATINVERT);
 for(i=0;i<16;i++)if(GetPixel(dc,i,176+(i%8))!=expected[i])bad++;
 line("DOUBLE_XOR_MISMATCHES",bad);
 SelectObject(dc,ob);DeleteObject(br);
 BitBlt(dc,32,176,32,16,dc,0,176,SRCCOPY);bad=0;
 for(i=0;i<16;i++)if(GetPixel(dc,32+i,176+(i%8))!=expected[i])bad++;
 line("SCREEN_COPY_MISMATCHES",bad);
 BitBlt(dc,0,176,32,16,mem,0,0,SRCCOPY);
 SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);
 }
 ReleaseDC(NULL,dc);line("GDI_DONE",1);
}
LONG FAR PASCAL WndProc(HWND h,UINT m,WPARAM w,LPARAM l) {
 if(m==WM_TIMER){KillTimer(h,1);
  if(step==0){tests();line("NOTEPAD_EXEC",WinExec("C:\\windows\\notepad.exe",SW_SHOW));step=1;SetTimer(h,1,500,NULL);return 0;}
  if(step==1){notepad=FindWindow("Notepad",NULL);line("NOTEPAD_HWND",notepad);line("NOTEPAD_MODULE",GetModuleHandle("NOTEPAD"));
   if(notepad){ShowWindow(notepad,SW_MAXIMIZE);edit=GetWindow(notepad,GW_CHILD);line("EDIT_HWND",edit);if(edit){SendMessage(edit,WM_SETTEXT,0,(LONG)(LPSTR)"80x25 hardware text mode\r\nNotepad is unchanged.");SendMessage(edit,EM_SETSEL,0,MAKELONG(47,47));SendMessage(edit,EM_SETMODIFY,0,0L);}}
   step=2;SetTimer(h,1,500,NULL);return 0;}
  if(step==2){snapshot("C:\\TXNOTE.BIN");line("NOTEPAD_MODE",BiosMode()&255);if(edit)line("EDIT_TEXT_LENGTH",SendMessage(edit,WM_GETTEXTLENGTH,0,0L));
   InvalidateRect(notepad,NULL,TRUE);UpdateWindow(notepad);step=3;SetTimer(h,1,500,NULL);return 0;}
  if(step==3){snapshot("C:\\TXREPT.BIN");ShowWindow(notepad,SW_RESTORE);MoveWindow(notepad,8,8,624,184,TRUE);step=4;SetTimer(h,1,500,NULL);return 0;}
  snapshot("C:\\TXMOVE.BIN");if(edit)restoretest();
  if(notepad)SendMessage(notepad,WM_CLOSE,0,0L);line("DONE",1);_lclose(logf);DestroyWindow(h);return 0;}
 if(m==WM_DESTROY){PostQuitMessage(0);return 0;}
 return DefWindowProc(h,m,w,l);
}
int PASCAL WinMain(HANDLE inst,HANDLE prev,LPSTR cmd,int show) {WNDCLASS wc;MSG msg;
 logf=_lcreat("C:\\TXPROBE.LOG",0);line("START",1);
 if(!prev){wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="TXPROBE";RegisterClass(&wc);}
 window=CreateWindow("TXPROBE","",WS_POPUP,0,0,1,1,NULL,NULL,inst,NULL);line("WINDOW",window);line("TIMER",SetTimer(window,1,3000,NULL));
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return 0;
}
