/* MODETEST: real-mode Win3 GDI regression. See MODECHK.PY --help.
 * C:\MODETEST.INI [mode]: width=640, colors=4, bios=10, phases=31.
 * phases: 1 core/BitBlt, 2 DIB imports, 4 DIB readback, 8 fonts/cursor, 16 raw aliases (2/4-color). palette=1 selects red/green; palette=0 CGA.
 * Only PROBEASM BIOS AH=0F metadata is used; never BIOS pixel reads.
 */
#define WINVER 0x0300
#include <windows.h>
#define DW 37
#define DH 11
#define SW 64
#define SH 32
extern unsigned FAR PASCAL BiosMode(void);
struct INFO256 { BITMAPINFOHEADER h; RGBQUAD c[256]; };
struct CASE { int dx,dy,w,h,sx,sy,start,scans,clip; };
static struct CASE dibCases[10]={
 {16,8,37,11,0,0,0,11,0}, {-3,20,37,11,0,0,0,11,0},
 {50,-4,37,11,0,0,0,11,0}, {0,40,37,11,0,0,0,11,0},
 {50,195,37,11,0,0,0,11,0}, {70,70,19,6,3,2,0,11,0},
 {100,90,37,11,0,0,3,5,0}, {100,90,19,8,2,1,3,5,0},
 {80,60,37,11,0,0,0,11,1}, {0,193,29,7,7,0,0,11,0}
};
static struct INFO256 info, query;
static BYTE bits[4096], original[4096], raw[4096];
static HFILE logFile;
static HDC dc;
static int width,phases,numColors,paletteKind;
static COLORREF colors[22]={
 RGB(0,0,0), RGB(0,0,128), RGB(0,128,0), RGB(0,128,128),
 RGB(128,0,0), RGB(128,0,128), RGB(128,128,0), RGB(128,128,128),
 RGB(64,64,64), RGB(0,0,255), RGB(0,255,0), RGB(0,255,255),
 RGB(255,0,0), RGB(255,0,255), RGB(255,255,0), RGB(255,255,255),
 RGB(0,127,128), RGB(0,128,127), RGB(127,127,255),
 RGB(128,128,255), RGB(255,127,128), RGB(255,128,127)
};
static void line(char *key,LONG value)
{
 char out[100],digits[12];int n=0,d=0;DWORD v;
 while(*key)out[n++]=*key++;out[n++]='=';
 if(value<0){out[n++]='-';v=(DWORD)(-value);}else v=(DWORD)value;
 do{digits[d++]=(char)('0'+v%10);v/=10;}while(v);
 while(d)out[n++]=digits[--d];out[n++]='\r';out[n++]='\n';
 _lwrite(logFile,out,n);
}
static void flushlog(void)
{
 _lclose(logFile);logFile=_lopen("C:\\MODETEST.LOG",OF_WRITE);
 _llseek(logFile,0L,2);
}
static void dump(char *name,void FAR *p,UINT n)
{
 HFILE f;UINT written=0;f=_lcreat(name,0);
 if(f!=HFILE_ERROR){written=_lwrite(f,p,n);_lclose(f);}
 if(written!=n)line("DUMP_ERROR",n);
}
static void frame(int n,char kind)
{
 char name[]="C:\\MD000.BIN";
 name[4]=kind;name[5]=(char)('0'+n/100);
 name[6]=(char)('0'+n/10%10);name[7]=(char)('0'+n%10);
 dump(name,(void FAR *)0xb8000000L,32768U);
}
static void begin(int n,int kind)
{
 line("CASE",n);line("KIND",kind);flushlog();frame(n,'B');
}
static void endcase(int n)
{
 frame(n,'D');line("ENDCASE",n);flushlog();
}
static void fill(HDC target,int l,int t,int r,int b,COLORREF color)
{
 HBRUSH br;RECT rc;rc.left=l;rc.top=t;rc.right=r;rc.bottom=b;
 br=CreateSolidBrush(color);
 if(!br)line("BRUSH_ERROR",1);
 else {FillRect(target,&rc,br);DeleteObject(br);}
}
static void strips(HDC target,int grid)
{
 int i,j,rows;rows=grid?10:1;
 for(j=0;j<rows;j++)for(i=0;i<16;i++)
 fill(target,i*(width/16),j*(200/rows),(i+1)*(width/16),
 (j+1)*(200/rows),colors[(i+j*3)&15]);
}
static void parameters(struct CASE *p)
{
 line("DX",p->dx);line("DY",p->dy);line("WIDTH",p->w);
 line("HEIGHT",p->h);line("SX",p->sx);line("SY",p->sy);
 line("START",p->start);line("SCANS",p->scans);line("CLIP",p->clip);
}
static void core(void)
{
 HDC mem;HBITMAP bm,old,big;BITMAP obj;HRGN region;
 int i,x,y,n,count;struct CASE p;DWORD rop;
 count=GetDeviceCaps(dc,NUMCOLORS)==16?16:22;
 begin(0,0);strips(dc,0);endcase(0);
 fill(dc,0,0,width,200,colors[15]);begin(1,1);
 for(i=0;i<count;i++){
  line("INPUT",i);line("SET",SetPixel(dc,i,0,colors[i]));
  line("GET",GetPixel(dc,i,0));
  line("EDGE_SET",SetPixel(dc,width-count+i,199,colors[i]));
  line("EDGE_GET",GetPixel(dc,width-count+i,199));
 }
 endcase(1);
 mem=CreateCompatibleDC(dc);line("CCDC",mem!=NULL);
 big=CreateCompatibleBitmap(dc,width,200);line("FULL_DDB",big!=NULL);
 if(big && mem){
  GetObject(big,sizeof(obj),&obj);
  line("FULL_WIDTH",obj.bmWidth);line("FULL_HEIGHT",obj.bmHeight);
  line("FULL_STRIDE",obj.bmWidthBytes);line("FULL_PLANES",obj.bmPlanes);
  line("FULL_BPP",obj.bmBitsPixel);
  line("FULL_BYTES",(LONG)obj.bmWidthBytes*obj.bmHeight*obj.bmPlanes);
  old=SelectObject(mem,big);strips(mem,1);begin(2,2);
  line("RETURN",BitBlt(dc,0,0,width,200,mem,0,0,SRCCOPY));endcase(2);
  SelectObject(mem,old);DeleteObject(big);
 }
 if(!mem)return;
 bm=CreateCompatibleBitmap(dc,SW,SH);line("SMALL_DDB",bm!=NULL);
 if(!bm){DeleteDC(mem);return;}
 old=SelectObject(mem,bm);
 for(y=0;y<SH;y++)for(x=0;x<SW;x++)SetPixel(mem,x,y,colors[(x*3+y*5)&15]);
 for(i=0;i<count;i++){
  line("MEM_INPUT",i);line("MEM_SET",SetPixel(mem,i,0,colors[i]));
  line("MEM_GET",GetPixel(mem,i,0));
 }
 for(x=0;x<SW;x++)SetPixel(mem,x,0,colors[(x*3)&15]);
 for(i=0;i<12;i++){
  p.dx=7+i*3;p.dy=8+i*9;p.w=47-i;p.h=23-i;
  p.sx=i%8;p.sy=i%5;p.start=0;p.scans=0;p.clip=0;
  if(i==4)p.dx=-9;
  if(i==5)p.dy=-7;
  if(i==6)p.dx=width-13;
  if(i==7)p.dy=195;
  if(i==8){p.dx=0;p.dy=0;p.w=64;p.h=32;p.sx=0;p.sy=0;}
  if(i==9){p.dx=width-64;p.dy=168;p.w=64;p.h=32;p.sx=0;p.sy=0;}
  if(i==10){p.dx=80;p.dy=60;p.clip=1;}
  if(i==11){p.dx=13;p.dy=171;p.w=37;p.h=11;p.sx=7;p.sy=3;}
  fill(dc,0,0,width,200,colors[13]);n=10+i;begin(n,3);parameters(&p);
  region=NULL;
  if(p.clip){region=CreateRectRgn(85,62,103,68);SelectClipRgn(dc,region);}
  rop=(i==11)?SRCINVERT:SRCCOPY;line("XOR",i==11);
  line("RETURN",BitBlt(dc,p.dx,p.dy,p.w,p.h,mem,p.sx,p.sy,rop));
  SelectClipRgn(dc,NULL);if(region)DeleteObject(region);endcase(n);
 }
 SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);
 for(i=0;i<6;i++){
  p.sx=20;p.sy=20;p.dx=23;p.dy=22;p.w=width-50;p.h=155;
  p.start=0;p.scans=0;p.clip=0;
  if(i==1){p.dx=17;p.dy=18;}
  if(i==2){p.dx=20;p.dy=23;}
  if(i==3){p.dx=21;p.dy=20;}
  if(i==4){p.dx=-3;p.dy=198;p.h=8;}
  if(i==5){p.dx=80;p.dy=60;p.clip=1;}
  strips(dc,1);n=30+i;begin(n,4);parameters(&p);region=NULL;
  if(p.clip){region=CreateRectRgn(85,62,103,68);SelectClipRgn(dc,region);}
  line("RETURN",BitBlt(dc,p.dx,p.dy,p.w,p.h,dc,p.sx,p.sy,SRCCOPY));
  SelectClipRgn(dc,NULL);if(region)DeleteObject(region);endcase(n);
 }
}
static void initinfo(struct INFO256 *p,int bpp)
{
 int i;BYTE *v=(BYTE *)p;
 for(i=0;i<sizeof(struct INFO256);i++)v[i]=0;
 p->h.biSize=40L;p->h.biWidth=DW;p->h.biHeight=DH;
 p->h.biPlanes=1;p->h.biBitCount=bpp;p->h.biCompression=BI_RGB;
 if(bpp)p->h.biSizeImage=(LONG)(((DW*bpp+31)/32)*4)*DH;
 for(i=0;i<16;i++){
  p->c[i].rgbRed=GetRValue(colors[i]);p->c[i].rgbGreen=GetGValue(colors[i]);
  p->c[i].rgbBlue=GetBValue(colors[i]);
 }
 if(bpp==1){p->c[1].rgbRed=255;p->c[1].rgbGreen=255;p->c[1].rgbBlue=255;}
}
static void initbits(int bpp)
{
 int i,x,y,v,stride;COLORREF c;
 initinfo(&info,bpp);stride=((DW*bpp+31)/32)*4;
 for(i=0;i<4096;i++)bits[i]=0xa5;
 for(i=0;i<stride*DH;i++)bits[i]=0;
 for(y=0;y<DH;y++)for(x=0;x<DW;x++){
  v=(x*3+(DH-1-y)*5)&15;i=y*stride;
  if(bpp==1){if(v<7)bits[i+x/8]|=(BYTE)(128>>(x%8));}
  else if(bpp==4){if(x&1)bits[i+x/2]|=(BYTE)v;else bits[i+x/2]=(BYTE)(v<<4);}
  else if(bpp==8)bits[i+x]=(BYTE)v;
  else {c=colors[v];i+=x*3;bits[i]=GetBValue(c);bits[i+1]=GetGValue(c);bits[i+2]=GetRValue(c);}
 }
 for(i=0;i<4096;i++)original[i]=bits[i];
}
static void imports(void)
{
 struct CASE p;HRGN region;int k,n,bpp,bpps[4],stride,i,errors,id;DWORD bad[4];
 bpps[0]=1;bpps[1]=4;bpps[2]=8;bpps[3]=24;
 bad[0]=1L;bad[1]=2L;bad[2]=256L;bad[3]=65536L;
 for(k=0;k<56;k++){
  bpp=bpps[k/14];n=k%14;stride=((DW*bpp+31)/32)*4;p=dibCases[n<10?n:0];
  if(n==3)p.dx=width-10;if(n==9)p.dx=width-29;
  fill(dc,0,0,width,200,colors[8]);initbits(bpp);id=40+k;
  begin(id,5);parameters(&p);line("BPP",bpp);
  if(n>=10)info.h.biCompression=bad[n-10];
  line("COMPRESSION",info.h.biCompression);flushlog();region=NULL;
  if(p.clip){region=CreateRectRgn(85,62,103,68);SelectClipRgn(dc,region);}
  line("RETURN",SetDIBitsToDevice(dc,p.dx,p.dy,p.w,p.h,p.sx,p.sy,
   p.start,p.scans,bits+p.start*stride,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
  errors=0;for(i=0;i<4096;i++)if(original[i]!=bits[i])errors++;
  line("INPUT_CHANGED",errors);SelectClipRgn(dc,NULL);
  if(region)DeleteObject(region);endcase(id);
 }
}
static void readback(void)
{
 HDC mem;HBITMAP bm,bm2,bm3,old;BITMAP obj;int i,x,y,errors;
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,DW,DH);
 line("READ_CCDC",mem!=NULL);line("READ_CCBM",bm!=NULL);
 if(!mem || !bm)return;
 GetObject(bm,sizeof(obj),&obj);line("READ_STRIDE",obj.bmWidthBytes);
 old=SelectObject(mem,bm);
 for(y=0;y<DH;y++)for(x=0;x<DW;x++)SetPixel(mem,x,y,colors[(x*3+y*5)&15]);
 SelectObject(mem,old);
 for(i=0;i<4096;i++)raw[i]=0xa5;
 line("READ_BITS",GetBitmapBits(bm,4096L,raw));dump("C:\\MDBITS.BIN",raw,4096);
 initinfo(&query,0);line("QUERY_RETURN",GetDIBits(dc,bm,0,DH,NULL,(LPBITMAPINFO)&query,DIB_RGB_COLORS));
 line("QUERY_BPP",query.h.biBitCount);line("QUERY_PLANES",query.h.biPlanes);
 line("QUERY_SIZE",query.h.biSizeImage);dump("C:\\MDQUERY.BIN",&query,sizeof(query));
 initinfo(&info,4);for(i=0;i<4096;i++)bits[i]=0xa5;
 line("EXPORT_RETURN",GetDIBits(dc,bm,0,DH,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
 dump("C:\\MDEXPORT.BIN",bits,4096);dump("C:\\MDINFO.BIN",&info,sizeof(info));
 fill(dc,0,0,width,200,colors[8]);begin(100,6);
 line("RETURN",SetDIBitsToDevice(dc,width-DW,189,DW,DH,0,0,0,DH,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));endcase(100);
 initinfo(&query,4);for(i=0;i<4096;i++)bits[i]=0xa5;
 line("PARTIAL_RETURN",GetDIBits(dc,bm,3,5,bits,(LPBITMAPINFO)&query,DIB_RGB_COLORS));
 dump("C:\\MDPART.BIN",bits,4096);dump("C:\\MDPINFO.BIN",&query,sizeof(query));
 DeleteObject(bm);
 for(i=0;i<4;i++){
  int bpp;bpp=(i==0)?1:(i==1)?4:(i==2)?8:24;initbits(bpp);
  bm2=CreateCompatibleBitmap(dc,DW,DH);line("SETDIB_BITMAP",bm2!=NULL);
  if(bm2){
   fill(dc,0,0,width,200,colors[8]);begin(101+i*2,7);line("BPP",bpp);
   line("SETDIB_RETURN",SetDIBits(dc,bm2,0,DH,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
   SelectObject(mem,bm2);line("RETURN",BitBlt(dc,width-DW,189,DW,DH,mem,0,0,SRCCOPY));
   endcase(101+i*2);SelectObject(mem,old);DeleteObject(bm2);
  }
  bm3=CreateDIBitmap(dc,&info.h,CBM_INIT,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS);
  line("CREATEDIB_BITMAP",bm3!=NULL);
  if(bm3){
   fill(dc,0,0,width,200,colors[8]);begin(102+i*2,8);line("BPP",bpp);
   SelectObject(mem,bm3);line("RETURN",BitBlt(dc,width-DW,189,DW,DH,mem,0,0,SRCCOPY));
   endcase(102+i*2);SelectObject(mem,old);DeleteObject(bm3);
  }
  errors=0;for(x=0;x<4096;x++)if(bits[x]!=original[x])errors++;
  line("READ_INPUT_CHANGED",errors);
 }
 DeleteDC(mem);flushlog();
}
static void textcursor(void)
{
 HDC mem;HBITMAP bm,old;HFONT font,oldfont;TEXTMETRIC tm;POINT p,save;
 HCURSOR cursor;int i,ret,n;char message[]="Ag09 Win30";
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,128,32);
 line("TEXT_CCDC",mem!=NULL);line("TEXT_CCBM",bm!=NULL);
 if(mem && bm){
  old=SelectObject(mem,bm);font=(HFONT)GetStockObject(SYSTEM_FIXED_FONT);
  oldfont=SelectObject(mem,font);GetTextMetrics(mem,&tm);
  line("FONT_HEIGHT",tm.tmHeight);line("FONT_WIDTH",tm.tmAveCharWidth);
  fill(mem,0,0,128,32,colors[15]);SetTextColor(mem,colors[numColors==2?0:11]);SetBkMode(mem,TRANSPARENT);
  line("MEM_TEXT_RETURN",TextOut(mem,2,2,message,10));
  for(i=0;i<4096;i++)raw[i]=0xa5;
  line("TEXT_BITS",GetBitmapBits(bm,4096L,raw));dump("C:\\MDTEXT.BIN",raw,4096);
  fill(dc,0,0,width,200,colors[0]);begin(110,9);
  line("TEXT_BLT",BitBlt(dc,0,40,128,32,mem,0,0,SRCCOPY));
  fill(dc,width-128,100,width,132,colors[15]);SelectObject(dc,font);
  SetTextColor(dc,colors[numColors==2?0:11]);SetBkMode(dc,TRANSPARENT);
  line("SCREEN_TEXT_RETURN",TextOut(dc,width-126,102,message,10));endcase(110);
  SelectObject(mem,oldfont);SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);
 }
 strips(dc,1);GetCursorPos(&save);cursor=LoadCursor(NULL,IDC_ARROW);
 line("CURSOR_LOADED",cursor!=NULL);SetCursor(cursor);
 line("CURSOR_WIDTH",GetSystemMetrics(SM_CXCURSOR));line("CURSOR_HEIGHT",GetSystemMetrics(SM_CYCURSOR));
 for(i=0;i<5;i++){
  if(i==0){p.x=0;p.y=0;}else if(i==1){p.x=width-1;p.y=199;}
  else if(i==2){p.x=width/2;p.y=100;}else if(i==3){p.x=-20;p.y=-20;}
  else {p.x=width+20;p.y=220;}
  n=120+i;begin(n,10);line("CURSOR_REQ_X",p.x);line("CURSOR_REQ_Y",p.y);
  SetCursorPos(p.x,p.y);GetCursorPos(&p);line("CURSOR_X",p.x);line("CURSOR_Y",p.y);
  ret=ShowCursor(TRUE);line("CURSOR_SHOW_COUNT",ret);frame(n,'V');
  ret=ShowCursor(FALSE);line("CURSOR_HIDE_COUNT",ret);endcase(n);
 }
 SetCursor(NULL);SetCursorPos(save.x,save.y);
}

static char *aliasBits[4]={"C:\\MAE1.BIN","C:\\MAE4.BIN","C:\\MAE8.BIN","C:\\MAE24.BIN"};
static char *aliasInfo[4]={"C:\\MAI1.BIN","C:\\MAI4.BIN","C:\\MAI8.BIN","C:\\MAI24.BIN"};
static char *aliasMono[4]={"C:\\MAM0.BIN","C:\\MAM1.BIN","C:\\MAM2.BIN","C:\\MAM3.BIN"};
static void aliasraw(int flood)
{
 int x,y,k,i,v,base;
 for(i=0;i<4096;i++)raw[i]=0xa5;
 for(i=0;i<264;i++)raw[i]=0;
 for(y=0;y<DH;y++)for(x=0;x<DW;x++){
  v=(x+y)&15;
  if(flood){
   if(numColors==2){base=(x==0 || y==0 || x==DW-1 || y==DH-1)?0:1;v=base+(((x+y)&7)<<1);}
   else {base=(x==0 || y==0 || x==DW-1 || y==DH-1)?3:0;v=base+(((x+y)&3)<<2);}
  }
  for(k=0;k<4;k++)if(v&(1<<k))raw[y*24+k*6+x/8]|=(BYTE)(128>>(x%8));
 }
}
static void aliases(void)
{
 HDC mem,mono;HBITMAP bm,mbm,old,mold;HBRUSH brush,oldbrush;
 int i,bpp,k;COLORREF four[4];
 four[0]=RGB(0,0,0);four[1]=RGB(0,255,255);four[2]=RGB(255,0,255);four[3]=RGB(255,255,255);
 if(paletteKind==1){four[1]=RGB(255,0,0);four[2]=RGB(0,255,0);}
 if(numColors==2)four[1]=RGB(255,255,255);
 if(numColors!=4 && numColors!=2){line("ALIASES_WRONG_PROFILE",1);return;}
 mem=CreateCompatibleDC(dc);mono=CreateCompatibleDC(dc);
 bm=CreateCompatibleBitmap(dc,DW,DH);mbm=CreateBitmap(DW,DH,1,1,NULL);
 line("ALIAS_DCS",mem!=NULL && mono!=NULL);line("ALIAS_BITMAPS",bm!=NULL && mbm!=NULL);
 if(!mem || !mono || !bm || !mbm)return;
 aliasraw(0);line("ALIAS_SETBITS",SetBitmapBits(bm,264L,raw));
 old=SelectObject(mem,bm);mold=SelectObject(mono,mbm);
 for(i=0;i<16;i++){line("ALIAS_INDEX",i);line("ALIAS_GETPIXEL",GetPixel(mem,i,0));}
 fill(dc,0,0,width,200,colors[8]);begin(130,11);
 line("RETURN",BitBlt(dc,width-DW,189,DW,DH,mem,0,0,SRCCOPY));endcase(130);
 SelectObject(mem,old);for(i=0;i<4096;i++)bits[i]=0xa5;
 line("ALIAS_GETBITS",GetBitmapBits(bm,4096L,bits));dump("C:\\MALIAS.BIN",bits,4096);
 for(k=0;k<4;k++){
  bpp=(k==0)?1:(k==1)?4:(k==2)?8:24;initinfo(&info,bpp);
  for(i=0;i<4096;i++)bits[i]=0xa5;
  line("ALIAS_EXPORT_BPP",bpp);
  line("ALIAS_EXPORT_RETURN",GetDIBits(dc,bm,0,DH,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
  dump(aliasBits[k],bits,4096);dump(aliasInfo[k],&info,sizeof(info));
 }
 SelectObject(mem,bm);
 for(k=0;k<numColors;k++){
  SetBkColor(mem,four[k]);line("ALIAS_MONO_BG",k);
  line("ALIAS_MONO_RETURN",BitBlt(mono,0,0,DW,DH,mem,0,0,SRCCOPY));
  for(i=0;i<4096;i++)bits[i]=0xa5;
  line("ALIAS_MONO_GETBITS",GetBitmapBits(mbm,4096L,bits));dump(aliasMono[k],bits,4096);
 }
 SelectObject(mem,old);aliasraw(1);line("FLOOD_SETBITS",SetBitmapBits(bm,264L,raw));SelectObject(mem,bm);
 brush=CreateSolidBrush(four[1]);oldbrush=SelectObject(mem,brush);
 line("FLOOD_RETURN",FloodFill(mem,1,1,four[numColors==2?0:3]));SelectObject(mem,oldbrush);DeleteObject(brush);
 fill(dc,0,0,width,200,colors[8]);begin(131,12);
 line("RETURN",BitBlt(dc,width-DW,189,DW,DH,mem,0,0,SRCCOPY));endcase(131);
 for(i=0;i<4096;i++)bits[i]=0xa5;
 line("FLOOD_GETBITS",GetBitmapBits(bm,4096L,bits));dump("C:\\MAFLOOD.BIN",bits,4096);
 SelectObject(mem,old);SelectObject(mono,mold);DeleteObject(bm);DeleteObject(mbm);DeleteDC(mem);DeleteDC(mono);
 flushlog();
}

int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 int wantedColors,wantedBIOS,hidden,ret;TEXTMETRIC tm;
 logFile=_lcreat("C:\\MODETEST.LOG",0);if(logFile==HFILE_ERROR)return 1;
 width=GetPrivateProfileInt("mode","width",640,"C:\\MODETEST.INI");
 wantedColors=GetPrivateProfileInt("mode","colors",4,"C:\\MODETEST.INI");
 wantedBIOS=GetPrivateProfileInt("mode","bios",10,"C:\\MODETEST.INI");
 phases=GetPrivateProfileInt("mode","phases",31,"C:\\MODETEST.INI");
 numColors=wantedColors;
 paletteKind=GetPrivateProfileInt("mode","palette",(width==640 && numColors==4)?1:0,"C:\\MODETEST.INI");
 dc=GetDC(NULL);line("VERSION",2);line("PHASES",phases);line("PALETTE_KIND",paletteKind);
 line("HORZRES",GetDeviceCaps(dc,HORZRES));line("VERTRES",GetDeviceCaps(dc,VERTRES));
 line("BITSPIXEL",GetDeviceCaps(dc,BITSPIXEL));line("PLANES",GetDeviceCaps(dc,PLANES));
 line("NUMCOLORS",GetDeviceCaps(dc,NUMCOLORS));line("BIOS",BiosMode()&255);
 line("RASTERCAPS",GetDeviceCaps(dc,RASTERCAPS));
 line("LOGPIXELSX",GetDeviceCaps(dc,LOGPIXELSX));line("LOGPIXELSY",GetDeviceCaps(dc,LOGPIXELSY));
 line("NUMPENS",GetDeviceCaps(dc,NUMPENS));GetTextMetrics(dc,&tm);
 line("SYSTEM_FONT_HEIGHT",tm.tmHeight);line("SYSTEM_FONT_WIDTH",tm.tmAveCharWidth);
 if(GetDeviceCaps(dc,HORZRES)!=width || GetDeviceCaps(dc,VERTRES)!=200 ||
 GetDeviceCaps(dc,NUMCOLORS)!=wantedColors || (int)(BiosMode()&255)!=wantedBIOS){
  line("WRONG_DISPLAY",1);_lclose(logFile);ReleaseDC(NULL,dc);return 2;
 }
 hidden=0;do{ret=ShowCursor(FALSE);hidden++;}while(ret>=0 && hidden<32);SetCursor(NULL);
 if(phases&1)core();if(phases&2)imports();if(phases&4)readback();if(phases&8)textcursor();if(phases&16)aliases();
 line("COMPLETE",1);_lclose(logFile);ReleaseDC(NULL,dc);
 while(hidden>0){ShowCursor(TRUE);hidden--;}
 return 0;
}
