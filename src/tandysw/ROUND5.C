#define WINVER 0x0300
#include <windows.h>
#define W 37
#define H 11
struct INFO16 { BITMAPINFOHEADER h; RGBQUAD c[16]; };
static struct INFO16 info;
static BYTE bits[220];
static HFILE logFile;
static COLORREF colors[16]={
 RGB(0,0,0), RGB(0,0,128), RGB(0,128,0), RGB(0,128,128),
 RGB(128,0,0), RGB(128,0,128), RGB(128,128,0), RGB(128,128,128),
 RGB(64,64,64), RGB(0,0,255), RGB(0,255,0), RGB(0,255,255),
 RGB(255,0,0), RGB(255,0,255), RGB(255,255,0), RGB(255,255,255)
};
static void line(char *key, LONG value)
{
 char out[100],digits[12]; int n=0,d=0; DWORD v;
 while(*key)out[n++]=*key++;out[n++]='=';
 if(value<0){out[n++]='-';v=(DWORD)(-value);}else v=(DWORD)value;
 do{digits[d++]=(char)('0'+v%10);v/=10;}while(v);
 while(d)out[n++]=digits[--d];out[n++]='\r';out[n++]='\n';
 _lwrite(logFile,out,n);
}
static void dump(char *name,void FAR *p,UINT n)
{
 HFILE f;f=_lcreat(name,0);if(f!=HFILE_ERROR){_lwrite(f,p,n);_lclose(f);}
}
static void fill(HDC dc,int l,int t,int r,int b,COLORREF c)
{
 HBRUSH br;RECT rc;rc.left=l;rc.top=t;rc.right=r;rc.bottom=b;
 br=CreateSolidBrush(c);FillRect(dc,&rc,br);DeleteObject(br);
}

int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 HDC dc;int i,x,y,v,ret,hidden,failures=0;BYTE *p=(BYTE *)&info;
 logFile=_lcreat("C:\\ROUND5.LOG",0);if(logFile==HFILE_ERROR)return 1;
 line("VERSION",5);dc=GetDC(NULL);
 for(i=0;i<sizeof(info);i++)p[i]=0;
 info.h.biSize=40L;info.h.biWidth=W;info.h.biHeight=H;info.h.biPlanes=1;
 info.h.biBitCount=4;info.h.biCompression=BI_RGB;info.h.biSizeImage=220L;
 for(i=0;i<16;i++){info.c[i].rgbRed=GetRValue(colors[i]);info.c[i].rgbGreen=GetGValue(colors[i]);info.c[i].rgbBlue=GetBValue(colors[i]);}
 for(i=0;i<220;i++)bits[i]=0;
 for(y=0;y<H;y++)for(x=0;x<W;x++){v=(x*3+(H-1-y)*5)&15;i=y*20+x/2;if(x&1)bits[i]|=(BYTE)v;else bits[i]=(BYTE)(v<<4);}
 hidden=0;do{ret=ShowCursor(FALSE);hidden++;}while(ret>=0 && hidden<32);SetCursor(NULL);
 for(i=0;i<8;i++)SetDIBitsToDevice(dc,16,16,W,H,0,0,0,H,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS);
 line("WARMUP_CALLS",8);line("LARGEST_BEFORE",GlobalCompact(0L));line("FREE_BEFORE",GetFreeSpace(0));
 dump("C:\\R5BEFORE.BIN",(void FAR *)0xb8000000L,32768U);
 for(i=0;i<64;i++){
 ret=SetDIBitsToDevice(dc,16,16,W,H,0,0,0,H,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS);
 if(ret!=H)failures++;
 if((i&15)==15){line("CALLS",i+1);line("LARGEST_AFTER",GlobalCompact(0L));line("FREE_AFTER",GetFreeSpace(0));}
 }
 dump("C:\\R5AFTER.BIN",(void FAR *)0xb8000000L,32768U);
 line("CALL_FAILURES",failures);line("COMPLETE",1);_lclose(logFile);ReleaseDC(NULL,dc);
 while(hidden>0){ShowCursor(TRUE);hidden--;}return 0;
}
