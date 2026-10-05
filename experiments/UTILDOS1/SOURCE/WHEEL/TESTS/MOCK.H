#include <stdlib.h>
#define far
#define _KEYBRD_READY 1
#define _KEYBRD_READ 0
#define FP_SEG(p) ((p)?1:0)
#define FP_OFF(p) 0
union REGS { struct { unsigned ax,bx,cx,dx,si,di,cflag; } x; struct { unsigned char al,ah,bl,bh,cl,ch,dl,dh; } h; };
static unsigned char biosarea[256],lcr=3,mcr=0,ier=0,dll=12,dlh=0;
static unsigned clockticks=0,pos=0,writes=0,restored=0;
static unsigned char dummy_handler=0x90;
static const char *scenario;
static void *mock_fp(unsigned s,unsigned o){ (void)s;if(o==0x6c){*(unsigned *)(biosarea+o)=clockticks++;}return biosarea+o; }
static unsigned char *_dos_getvect(unsigned n){if(n==0x33&&!strcmp(scenario,"resident"))return &dummy_handler;return NULL;}
static int int86(int n,union REGS *i,union REGS *o){(void)n;(void)i;(void)o;return 0;}
static int _bios_keybrd(int mode){if(mode==_KEYBRD_READ&&!strcmp(scenario,"changed"))mcr=2;if(!strcmp(scenario,"escape")&&clockticks>20)return mode==_KEYBRD_READY?27:27;return mode==_KEYBRD_READY?0:(!strcmp(scenario,"cancel")?'N':'R');}
static int inp(unsigned p){switch(p-0x3f8){case 0:return(lcr&0x80)?dll:(int)((pos++%4==0)?0x40:((pos-1)%4==3?1:0));case 1:return(lcr&0x80)?dlh:ier;case 3:return lcr;case 4:return mcr;case 5:return !strcmp(scenario,"txbusy")?1:(!strcmp(scenario,"uart")?0x65:0x61);}abort();}
static int outp(unsigned p,int v){++writes;switch(p-0x3f8){case 0:if(!(lcr&0x80))abort();dll=(unsigned char)v;break;case 1:if(lcr&0x80)dlh=(unsigned char)v;else ier=(unsigned char)v;break;case 3:lcr=(unsigned char)v;break;case 4:mcr=(unsigned char)v;break;default:abort();}return v;}
static int stricmp(const char *a,const char *b){return strcmp(a,b);}
