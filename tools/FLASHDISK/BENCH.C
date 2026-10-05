/* Developer-only fixed-size SHA timing probe; no Windows bytes. */
#define main prepxt_main
#include "PREPXT.C"
#undef main
static U32 ticks(void){union REGS a,b;a.h.ah=0;int86(0x1a,&a,&b);return ((U32)b.x.cx<<16)|b.x.dx;}
int main(void){U32 before,after;unsigned i;char hex[65];memset(io,'a',sizeof(io));before=ticks();sha_init(&state);for(i=0;i<16;i++)sha_add(&state,io,sizeof(io));sha_end(&state,hex);after=ticks();printf("65536 bytes SHA256: %s\nBIOS ticks: %lu\n",hex,after-before);return 0;}
