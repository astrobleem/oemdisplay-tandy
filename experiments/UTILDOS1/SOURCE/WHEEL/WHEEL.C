/* WHEEL 0.1: DOS/8088 wheel diagnostic. Microsoft C 6, /G0 /AS.
 * No resident installation, driver replacement, file writes, UART transmit,
 * PIC programming or vector changes. RAW requires explicit port + key consent.
 * The serial decode is only an IntelliMouse-format candidate interpretation.
 */
#include <stdio.h>
#include <string.h>
#ifndef HOST_TEST
#include <dos.h>
#include <bios.h>
#include <conio.h>
#define MK_FP(s,o) ((void far *)(((unsigned long)(s)<<16)|(unsigned)(o)))
#endif
#define CAP 4096
#define TICKS 364U
struct record { unsigned tick; unsigned char data, status; };
#ifndef HOST_TEST
static struct record records[CAP];
#endif
struct decoder { unsigned n, triples, extensions, changes, errors; int sum; unsigned char first, x; };
static void reset(struct decoder *d) { memset(d,0,sizeof(*d)); }
/* Reset synchronization after line errors or a >~110 ms inter-byte gap. */
static int feed(struct decoder *d,unsigned b,unsigned status,int gap) {
 int z;
 if(gap)d->n=0;
 if(status&0x1e){d->n=0;++d->errors;return 0;}
 if(b&0x80){d->n=0;++d->errors;return 0;}
 if(b&0x40){d->n=1;d->first=(unsigned char)b;return 0;}
 if(d->n==1){d->x=(unsigned char)b;d->n=2;return 0;}
 if(d->n==2){++d->triples;d->n=3;return 0;}
 if(d->n!=3)return 0;
 d->n=0;
 if(b&0x20){++d->errors;return 0;}
 ++d->extensions;
 z=(int)(b&15);if(z&8)z-=16;
 if(z){++d->changes;d->sum+=z;}
 return z;
}
static int tests(void) {
 struct decoder d;unsigned i;int failures=0,z=0;
 #define CHECK(x) do { if(!(x)){++failures;printf("FAIL line %u\n",(unsigned)__LINE__);} } while(0)
 reset(&d);feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);z=feed(&d,1,0,0);
 CHECK(z==1&&d.triples==1&&d.extensions==1&&d.sum==1);
 feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);z=feed(&d,0x0f,0,0);
 CHECK(z==-1&&d.sum==0&&d.changes==2);
 reset(&d);for(i=0;i<16;++i){feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);z=feed(&d,i,0,0);CHECK(z==(i<8?(int)i:(int)i-16));}
 CHECK(d.extensions==16&&d.sum==-8);
 reset(&d);for(i=0;i<10;++i){feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);}
 CHECK(d.triples==10&&d.extensions==0&&d.changes==0);
 reset(&d);feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);CHECK(feed(&d,0x10,0,0)==0);CHECK(d.changes==0&&d.extensions==1);
 reset(&d);feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);CHECK(feed(&d,1,0x04,0)==0);CHECK(d.errors==1&&d.extensions==0);
 reset(&d);feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);CHECK(feed(&d,1,0,1)==0);CHECK(d.extensions==0);
 reset(&d);for(i=0x20;i<0x40;++i){feed(&d,0x40,0,0);feed(&d,0,0,0);feed(&d,0,0,0);CHECK(feed(&d,i,0,0)==0);}
 CHECK(d.extensions==0&&d.changes==0&&d.errors==32);
 reset(&d);for(i=0;i<10000;++i){feed(&d,(i*47U)&255U,0,(i%9)==0);CHECK(d.n<=3);}
 printf("%s packet tests (synthetic data only)\n",failures?"FAIL":"PASS");
 return failures?1:0;
}
#ifndef HOST_TEST
static unsigned ticks(void) { return *(volatile unsigned far *)MK_FP(0x40,0x6c); }
static int key(void) { return _bios_keybrd(_KEYBRD_READY)?(int)(_bios_keybrd(_KEYBRD_READ)&255):-1; }
static int handler(unsigned n) {
 unsigned char far *p=(unsigned char far *)_dos_getvect(n);
 return (FP_SEG(p)||FP_OFF(p))&&*p!=0xcf;
}
static int windows(void) {
 union REGS r;
 if(!handler(0x2f))return 0;
 memset(&r,0,sizeof(r));r.x.ax=0x1600;int86(0x2f,&r,&r);
 if(r.h.al&0x7f)return 1;
 memset(&r,0,sizeof(r));r.x.ax=0x4680;int86(0x2f,&r,&r);
 /* Also rejects the DOS task switcher, conservatively. */
 return r.x.ax==0;
}
static void prompt(const char *s) {fputs(s,stderr);fputc('\n',stderr);fflush(stderr);}
static int api(void) {
 union REGS r;unsigned start,elapsed,events=0;long sum=0;int z;
 if(!handler(0x33)){puts("No active INT 33h mouse handler. No wheel API is available.");return 2;}
 memset(&r,0,sizeof(r));r.x.ax=0x11;int86(0x33,&r,&r);
 printf("Wheel API query: AX=%04X BX=%04X CX=%04X\n",r.x.ax,r.x.bx,r.x.cx);
 if(r.x.ax!=0x574d){puts("Driver does not advertise the CuteMouse wheel API.\nThis does NOT prove the physical wheel is broken or silent.\nNo UART access was made; the driver was not reset.");return 2;}
 if(!(r.x.cx&1)){puts("Wheel API exists, but driver reports no wheel-capable device.\nNo UART access was made; the driver was not reset.");return 2;}
 puts("Wheel API and wheel device reported. Turn wheel up, then down.\nSampling for 20 seconds; Esc stops early. Results appear afterward.\nThis consumes the driver's accumulated wheel count, without resetting the driver.");
 memset(&r,0,sizeof(r));r.x.ax=3;int86(0x33,&r,&r); /* discard prior count */
 start=ticks();do{
  memset(&r,0,sizeof(r));r.x.ax=3;int86(0x33,&r,&r);
  z=(int)(signed char)r.h.bh;if(z){++events;sum+=z;}
  if(key()==27)break;
  elapsed=(unsigned)(ticks()-start);
 }while(elapsed<TICKS);
 printf("Wheel-bearing samples=%u; net delta=%ld (positive means down).\n",events,sum);
 if(!events)puts("No wheel count arrived during this observation window.");
 return 0;
}
static int raw(unsigned com) {
 unsigned port,n=0,begin,elapsed,status,i,errors=0,oldtick=0,shown=0;
 unsigned char oldlcr,oldmcr,oldier,oldlo,oldhi;int c,z,full=0;
 struct decoder d;
 if(windows()){puts("RAW refused: exit Windows/task switching and boot plain DOS first.");return 3;}
 if(handler(0x33)){puts("RAW refused: an INT 33h mouse handler is resident.\nReboot with F5 to skip CONFIG.SYS/AUTOEXEC.BAT; do not load a mouse driver.\nDo not use a Windows DOS prompt. Normal WHEEL /API is safe with the driver.");return 3;}
 port=*((unsigned far *)MK_FP(0x40,(com-1)*2));
 printf("Selected COM%u, BIOS base=%04X.\n",com,port);
 if(port!=0x3f8U&&port!=0x2f8U){puts("RAW refused: port absent or nonstandard BIOS address. No port writes.");return 3;}
 oldlcr=(unsigned char)inp(port+3);oldmcr=(unsigned char)inp(port+4);
 if(oldlcr&0xc0){puts("RAW refused: UART unavailable, break active, or divisor bank selected.");return 3;}
 oldier=(unsigned char)inp(port+1);
 if(oldier||(oldmcr&0x10)){puts("RAW refused: UART interrupts or loopback are active. No port writes.");return 3;}
 prompt("Use ONLY the serial port physically connected to the Genius mouse.\nThis temporarily selects 1200 baud, 7N1 and powers DTR/RTS.\nIt restores divisor/LCR/MCR/IER afterward; mouse power may change/reset.\nDo not use with a modem, printer, or any other serial device.\nPress R to capture, or any other key to cancel.");
 fflush(stdout);c=_bios_keybrd(_KEYBRD_READ)&255;if(c!='r'&&c!='R'){puts("Cancelled; no port writes.");return 0;}
 prompt("Capturing 20 seconds (first 2 seconds settle). Keep mouse still.\nAfter settling, turn wheel UP several clicks, then DOWN several clicks.\nDo not click buttons yet. Esc stops early. Results appear afterward.");
 fflush(stdout);
 /* Consent can take arbitrarily long: re-check immediately before mutation. */
 if((unsigned)inp(port+3)!=oldlcr||(unsigned)inp(port+4)!=oldmcr||
    (unsigned)inp(port+1)!=oldier||!(inp(port+5)&0x40)){
  puts("RAW refused: UART changed or transmitter is not idle. No port writes.");return 3;
 }
 /* No DOS/stdio calls occur while the UART is modified. No IRQ is enabled. */
 outp(port+3,oldlcr|0x80);oldlo=(unsigned char)inp(port);oldhi=(unsigned char)inp(port+1);
 outp(port,96);outp(port+1,0);outp(port+3,2);
 outp(port+4,(oldmcr|3)&~8); /* DTR+RTS on, OUT2 off. */
 begin=ticks();do{
  elapsed=(unsigned)(ticks()-begin);
  status=(unsigned)inp(port+5);
  if(status&1){
   c=inp(port);
   if(n<CAP){records[n].tick=elapsed;records[n].data=(unsigned char)c;records[n].status=(unsigned char)status;++n;}
   else{full=1;break;}
  }
  if(key()==27)break;
 }while(elapsed<TICKS);
 outp(port+3,0x82);outp(port,oldlo);outp(port+1,oldhi);
 outp(port+3,oldlcr);outp(port+1,oldier);outp(port+4,oldmcr);
 printf("UART restored. Captured %u bytes, elapsed ticks=%u%s.\n",n,elapsed,full?", BUFFER FULL":"");
 reset(&d);
 puts("Candidate IntelliMouse wheel events AFTER settling: tick delta byte");
 for(i=0;i<n;++i){
  if(records[i].status&0x1e)++errors;
  if(records[i].tick<36){d.n=0;continue;}
  z=feed(&d,records[i].data,records[i].status,(unsigned)(records[i].tick-oldtick)>2);
  oldtick=records[i].tick;
  if(z&&shown<64){printf("%5u %+3d %02X\n",records[i].tick,z,(unsigned)records[i].data);++shown;}
 }
 puts("Candidate decode only: this is NOT automatic model identification.\nMatching repeated +/- deltas to deliberate wheel motion is the useful test.\nZero candidates do not prove failure: port/protocol/initialization may differ.\nRAW HEX follows: tick: byte(status); first two seconds include startup data.");
 for(i=0;i<n;++i){printf("%u:%02X(%02X)%c",records[i].tick,(unsigned)records[i].data,(unsigned)records[i].status,(i%6==5)?'\n':' ');}
 if(n%6)putchar('\n');
 puts("FINAL RAW SUMMARY (candidate protocol)");
 printf("COM%u %04X | bytes=%u | wheel events=%u | net=%d\n",com,port,n,d.changes,d.sum);
 printf("UART errors=%u | decode errors=%u | triples=%u | fourth=%u\n",errors,d.errors,d.triples,d.extensions);
 if(errors||d.errors)puts("Errors present: inspect the capture before drawing conclusions.");
 else if(d.changes)puts("Wheel candidates seen: compare signs with your deliberate up/down turns.");
 else puts("No wheel candidates: inconclusive; port/protocol/state may differ.");
 puts("UART registers restored; mouse state may differ.");
 puts("Raw packets do not enable Windows scrolling.");
 puts("Reboot normally before using your usual mouse driver or Windows.");
 return 0;
}
int main(int argc,char **argv) {
 puts("WHEEL 0.1 - 8088/DOS mouse wheel diagnostic");
 if(argc==1||(argc==2&&!stricmp(argv[1],"/API")))return api();
 if(argc==2&&!stricmp(argv[1],"/TEST"))return tests();
 if(argc==2&&!stricmp(argv[1],"/RAW1"))return raw(1);
 if(argc==2&&!stricmp(argv[1],"/RAW2"))return raw(2);
 puts("Usage: WHEEL [/API | /TEST | /RAW1 | /RAW2]\n/API: existing driver query; /TEST: synthetic parser checks.\n/RAW1 and /RAW2: clean DOS boot only; no mouse TSR; explicit serial port.\nSee README.TXT. This is a diagnostic, not a Windows scrolling driver.");return 1;
}
#else
int main(void){return tests();}
#endif
