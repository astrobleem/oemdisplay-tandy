#define WINVER 0x0300
#include <windows.h>
#define W 37
#define H 11
struct INFO256 { BITMAPINFOHEADER h; RGBQUAD c[256]; };
struct CASE { int dx,dy,w,h,sx,sy,start,scans,clip; };
static struct CASE cases[10]={
 {16,8,37,11,0,0,0,11,0}, {-3,20,37,11,0,0,0,11,0},
 {50,-4,37,11,0,0,0,11,0}, {310,40,37,11,0,0,0,11,0},
 {50,195,37,11,0,0,0,11,0}, {70,70,19,6,3,2,0,11,0},
 {120,90,37,11,0,0,3,5,0}, {150,90,19,8,2,1,3,5,0},
 {80,60,37,11,0,0,0,11,1}, {200,120,29,7,7,0,0,11,0}
};
static struct INFO256 info;
static BYTE bits[4096],original[4096];
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

static void flushlog(void)
{
 _lclose(logFile);logFile=_lopen("C:\\ROUND4.LOG",OF_WRITE);_llseek(logFile,0L,2);
}
static int ci(int x,int y,int bpp)
{
 if(bpp==1)return (((x*3+y*5)&15)<7)?15:0;return (x*3+y*5)&15;
}
static void init(int bpp,int stride)
{
 int i,x,y,index,v;BYTE *p=(BYTE *)&info;COLORREF c;
 for(i=0;i<sizeof(info);i++)p[i]=0;
 info.h.biSize=40L;info.h.biWidth=W;info.h.biHeight=H;info.h.biPlanes=1;
 info.h.biBitCount=bpp;info.h.biCompression=BI_RGB;info.h.biSizeImage=(LONG)stride*H;
 for(i=0;i<16;i++){
 info.c[i].rgbRed=GetRValue(colors[i]);info.c[i].rgbGreen=GetGValue(colors[i]);info.c[i].rgbBlue=GetBValue(colors[i]);}
 if(bpp==1){info.c[1].rgbRed=255;info.c[1].rgbGreen=255;info.c[1].rgbBlue=255;}
 for(i=0;i<4096;i++)bits[i]=0xa5;
 for(i=0;i<stride*H;i++)bits[i]=0;
 for(y=0;y<H;y++)for(x=0;x<W;x++){
 v=ci(x,H-1-y,bpp);index=y*stride;
 if(bpp==1){if(v)bits[index+x/8]|=(BYTE)(128>>(x%8));}
 else if(bpp==4){if(x&1)bits[index+x/2]|=(BYTE)v;else bits[index+x/2]=(BYTE)(v<<4);}
 else if(bpp==8)bits[index+x]=(BYTE)v;
 else {c=colors[v];index+=x*3;bits[index]=GetBValue(c);bits[index+1]=GetGValue(c);bits[index+2]=GetRValue(c);}
 }
 for(i=0;i<4096;i++)original[i]=bits[i];
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 HDC dc;HRGN region;struct CASE *c;int bpps[4],k,bpp,n,stride,i,errors,hidden,ret,limit;
 DWORD bad[4];char fname[]="C:\\R4D00.BIN";
 bpps[0]=1;bpps[1]=4;bpps[2]=8;bpps[3]=24;
 bad[0]=1L;bad[1]=2L;bad[2]=256L;bad[3]=65536L;
 logFile=_lcreat("C:\\ROUND4.LOG",0);if(logFile==HFILE_ERROR)return 1;
 line("VERSION",4);dc=GetDC(NULL);line("HORZRES",GetDeviceCaps(dc,HORZRES));line("VERTRES",GetDeviceCaps(dc,VERTRES));line("RASTERCAPS",GetDeviceCaps(dc,RASTERCAPS));
 if((GetDeviceCaps(dc,HORZRES)!=320 && GetDeviceCaps(dc,HORZRES)!=640) || GetDeviceCaps(dc,VERTRES)!=200){line("WRONG_DISPLAY",1);_lclose(logFile);return 2;}
 hidden=0;do{ret=ShowCursor(FALSE);hidden++;}while(ret>=0 && hidden<32);SetCursor(NULL);
 limit=(cmd[0]=='M'||cmd[0]=='m')?10:56;
 for(k=0;k<limit;k++){
 bpp=bpps[k/14];n=k%14;stride=((W*bpp+31)/32)*4;c=&cases[n<10?n:0];
 SelectClipRgn(dc,NULL);fill(dc,0,0,320,200,colors[8]);init(bpp,stride);
 fname[6]=(char)('0'+k/10);fname[7]=(char)('0'+k%10);fname[5]='B';
 dump(fname,(void FAR *)0xb8000000L,32768U);
 region=NULL;if(c->clip){region=CreateRectRgn(85,62,103,68);SelectClipRgn(dc,region);}
 if(n>=10)info.h.biCompression=bad[n-10];
 line("CASE",k);line("BPP",bpp);line("DX",c->dx);line("DY",c->dy);line("WIDTH",c->w);line("HEIGHT",c->h);
 line("SX",c->sx);line("SY",c->sy);line("START",c->start);line("SCANS",c->scans);line("CLIP",c->clip);line("COMPRESSION",info.h.biCompression);flushlog();
 ret=SetDIBitsToDevice(dc,c->dx,c->dy,c->w,c->h,c->sx,c->sy,c->start,c->scans,bits+c->start*stride,(LPBITMAPINFO)&info,DIB_RGB_COLORS);
 line("RETURN",ret);errors=0;for(i=0;i<4096;i++)if(original[i]!=bits[i])errors++;
 line("INPUT_CHANGED_BYTES",errors);fname[5]='D';dump(fname,(void FAR *)0xb8000000L,32768U);flushlog();
 SelectClipRgn(dc,NULL);if(region)DeleteObject(region);
 }
 line("COMPLETE",1);_lclose(logFile);ReleaseDC(NULL,dc);while(hidden>0){ShowCursor(TRUE);hidden--;}return 0;
}
