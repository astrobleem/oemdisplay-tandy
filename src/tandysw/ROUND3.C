#define WINVER 0x0300
#include <windows.h>
#define W 37
#define H 11
struct INFO256 { BITMAPINFOHEADER h; RGBQUAD c[256]; };
static struct INFO256 info;
static BYTE bits[4096];
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
 _lwrite(logFile,out,n);_lclose(logFile);
 logFile=_lopen("C:\\ROUND3.LOG",OF_WRITE);_llseek(logFile,0L,2);
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

static char *gfiles[4]={"C:\\R3G1.BIN","C:\\R3G4.BIN","C:\\R3G8.BIN","C:\\R3G24.BIN"};
static char *ifiles[4]={"C:\\R3I1.BIN","C:\\R3I4.BIN","C:\\R3I8.BIN","C:\\R3I24.BIN"};
static void init(int bpp)
{
 int i;BYTE *p=(BYTE *)&info;
 for(i=0;i<sizeof(info);i++)p[i]=0;
 info.h.biSize=40L;info.h.biWidth=W;info.h.biHeight=H;info.h.biPlanes=1;
 info.h.biBitCount=bpp;info.h.biCompression=BI_RGB;
 info.h.biSizeImage=(LONG)(((W*bpp+31)/32)*4)*H;
 for(i=0;i<16;i++){
 info.c[i].rgbRed=GetRValue(colors[i]);info.c[i].rgbGreen=GetGValue(colors[i]);info.c[i].rgbBlue=GetBValue(colors[i]);}
 if(bpp==1){info.c[1].rgbRed=255;info.c[1].rgbGreen=255;info.c[1].rgbBlue=255;}
}
static int ci(int x,int y,int bpp)
{
 if(bpp==1)return ((x+y)&1)?15:0;return (x*3+y*5)&15;
}
static int check(HDC dc,int bpp,int top)
{
 int x,y,errors=0;
 for(y=0;y<H;y++)for(x=0;x<W;x++)if(GetPixel(dc,x,y+top)!=colors[ci(x,y,bpp)])errors++;
 return errors;
}
static int checkScreen(int bpp,int top)
{
 int x,y,sy,errors=0,v;BYTE FAR *video=(BYTE FAR *)0xb8000000L;
 for(y=0;y<H;y++)for(x=0;x<W;x++){
 sy=y+top;v=video[(sy%4)*8192+(sy/4)*160+x/2];
 v=(x&1)?(v&15):(v>>4);if(v!=ci(x,y,bpp))errors++;}
 return errors;
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 HDC dc,mem,rest;HBITMAP bm,bm2,bm3,old,old2;
 int bpps[4],k,bpp,x,y,hidden,r;
 bpps[0]=1;bpps[1]=4;bpps[2]=8;bpps[3]=24;
 logFile=_lcreat("C:\\ROUND3.LOG",0);if(logFile==HFILE_ERROR)return 1;
 line("VERSION",3);dc=GetDC(NULL);mem=CreateCompatibleDC(dc);rest=CreateCompatibleDC(dc);
 hidden=0;do{r=ShowCursor(FALSE);hidden++;}while(r>=0 && hidden<32);SetCursor(NULL);
 for(k=0;k<4;k++){
 bpp=bpps[k];line("BPP",bpp);bm=CreateCompatibleBitmap(dc,W,H);old=SelectObject(mem,bm);
 for(y=0;y<H;y++)for(x=0;x<W;x++)SetPixel(mem,x,y,colors[ci(x,y,bpp)]);
 line("SOURCE_MISMATCHES",check(mem,bpp,0));
 SelectObject(mem,old);init(bpp);for(x=0;x<4096;x++)bits[x]=0xa5;
 line("GETDIB",GetDIBits(dc,bm,0,H,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
 dump(gfiles[k],bits,4096);dump(ifiles[k],&info,sizeof(info));
 bm2=CreateCompatibleBitmap(dc,W,H);
 line("SETDIB_START",1);line("SETDIB",SetDIBits(dc,bm2,0,H,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
 old2=SelectObject(rest,bm2);line("SETDIB_MISMATCHES",check(rest,bpp,0));SelectObject(rest,old2);
 line("CREATEDIB_START",1);bm3=CreateDIBitmap(dc,&info.h,CBM_INIT,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS);
 line("CREATEDIB",bm3!=NULL);if(bm3){SelectObject(rest,bm3);line("CREATEDIB_MISMATCHES",check(rest,bpp,0));SelectObject(rest,old2);DeleteObject(bm3);}
 line("DIRECTDIB_START",1);line("DIRECTDIB",SetDIBitsToDevice(dc,0,k*24,W,H,0,0,0,H,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
 line("DIRECTDIB_MISMATCHES",checkScreen(bpp,k*24));DeleteObject(bm2);DeleteObject(bm);
 }
 line("COMPLETE",1);_lclose(logFile);DeleteDC(mem);DeleteDC(rest);ReleaseDC(NULL,dc);
 while(hidden>0){ShowCursor(TRUE);hidden--;}return 0;
}
