#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static struct {BITMAPINFOHEADER h;RGBQUAD colors[16];} info;
static BYTE bits[34],chunk[8000];static HFILE logf;static int w,h,profile,seq;
static void line(char *s,long v){char b[90];wsprintf(b,"%s=%ld\r\n",(LPSTR)s,v);_lwrite(logf,b,lstrlen(b));}
static void dump(void){HFILE f;char name[32];unsigned at=0,n,total;BYTE FAR *v;
 wsprintf(name,"C:\\R%02d.BIN",seq++);f=_lcreat(name,0);total=profile==2?64000U:32768U;v=(BYTE FAR *)(profile==2?0xa0000000L:0xb8000000L);
 while(at<total){n=total-at;if(n>8000)n=8000;
  _asm pushf
  _asm cli
  _fmemcpy((LPSTR)chunk,(LPSTR)(v+at),n);
  _asm popf
  _lwrite(f,(LPSTR)chunk,n);at+=n;
 }_lclose(f);
}
int PASCAL WinMain(HINSTANCE in,HINSTANCE prev,LPSTR cmd,int show){int i,c,hid=0;HDC dc,mem;HBITMAP bm,old;HGLOBAL block;BYTE FAR *base;BYTE FAR *farbits;BYTE huge *big;RECT r;MSG msg;DWORD t;
 logf=_lcreat("C:\\RLETEST.LOG",0);dc=GetDC(NULL);w=GetSystemMetrics(SM_CXSCREEN);h=GetSystemMetrics(SM_CYSCREEN);profile=w==640?2:(w==320?1:3);
 do{c=ShowCursor(FALSE);hid++;}while(c>=0&&hid<40);SetCursor(NULL);r.left=r.top=0;r.right=w;r.bottom=h;FillRect(dc,&r,GetStockObject(WHITE_BRUSH));
 _fmemset(&info,0,sizeof(info));info.h.biSize=40;info.h.biWidth=8;info.h.biHeight=8;info.h.biPlanes=1;info.h.biBitCount=4;info.h.biCompression=BI_RLE4;info.h.biSizeImage=34;info.h.biClrUsed=16;
 for(i=0;i<16;i++){info.colors[i].rgbRed=(BYTE)((i&4)?255:0);info.colors[i].rgbGreen=(BYTE)((i&2)?255:0);info.colors[i].rgbBlue=(BYTE)((i&1)?255:0);}
 for(i=0;i<8;i++){bits[i*4]=8;bits[i*4+1]=(BYTE)((i+1)*17);bits[i*4+2]=bits[i*4+3]=0;}bits[32]=0;bits[33]=1;
 line("SCREEN_LINES",SetDIBitsToDevice(dc,10,10,8,8,0,0,0,8,(LPSTR)bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));dump();
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,8,8);
 line("MEMORY_LINES",SetDIBits(dc,bm,0,8,(LPSTR)bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));old=SelectObject(mem,bm);line("MEMORY_BLIT",BitBlt(dc,22,22,8,8,mem,0,0,SRCCOPY));dump();SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);
 block=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,70000L);line("ALLOC_70K",block!=NULL);
 if(block){base=GlobalLock(block);big=(BYTE huge *)base;for(i=0;i<34;i++)big[65520L+i]=bits[i];farbits=(BYTE FAR *)MAKELONG(65520U,HIWORD(base));line("START_OFFSET",LOWORD(farbits));line("CROSS_LINES",SetDIBitsToDevice(dc,40,40,8,8,0,0,0,8,(LPSTR)farbits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));dump();GlobalUnlock(block);GlobalFree(block);}
 line("RLE_DONE",1);_lclose(logf);ReleaseDC(NULL,dc);while(hid-->0)ShowCursor(TRUE);
 if(cmd[0]=='/'&&cmd[1]=='R')return 0;
 WinExec("C:\\PROBE.EXE",SW_SHOWNORMAL);t=GetTickCount();while(GetModuleHandle("PROBE")&&GetTickCount()-t<400000UL){while(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}}
 return 0;
}
