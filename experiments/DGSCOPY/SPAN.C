#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define HOST_TEST 1
#define _far
#define _pascal
#define range base_range
#define memory base_memory
#define span base_span
#define row base_row
#define GenDrawKernel base_draw
#include BASE_SOURCE
#undef range
#undef memory
#undef span
#undef row
#undef GenDrawKernel
#define range cand_range
#define memory cand_memory
#define span cand_span
#define row cand_row
#define GenDrawKernel cand_draw
#include CAND_SOURCE
#undef range
#undef memory
#undef span
#undef row
#undef GenDrawKernel
int GenFarPrepare(int width,int height,int *work,GenWalk *walk) { (void)width;(void)height;(void)work;(void)walk; return 0; }
int GenFarNext(GenWalk *walk,int *work,GenPair *pair) { (void)walk;(void)work;(void)pair; return 0; }
#define STRIDE (WIDTH/2)
#define SIZE (STRIDE*200)
#define GUARD 32
static unsigned char a[SIZE+2*GUARD], b[SIZE+2*GUARD], expected[SIZE+2*GUARD];
static unsigned long tests;
static uint32_t seed=0x7c6a1f35;
static uint32_t rng(void) { seed=seed*1664525u+1013904223u; return seed; }
static void oracle(GenDraw *c,int y,int l,int r,int color,int invert) {
 if(y<0||y>=200||y<c->clipTop||y>=c->clipBottom)return;
 if(l<0)l=0;if(r>WIDTH)r=WIDTH;
 if(l<c->clipLeft)l=c->clipLeft;if(r>c->clipRight)r=c->clipRight;
 for(int x=l;x<r;x++) for(int plane=0;plane<4;plane++) {
  unsigned at=GUARD+y*STRIDE+plane*(WIDTH/8)+x/8;
  unsigned char mask=(unsigned char)(0x80u>>(x%8));
  if(invert==2&&!(color&(1<<plane)))continue;
  if(invert)expected[at]^=mask;
  else if(color&(1<<plane))expected[at]|=mask;
  else expected[at]&=(unsigned char)~mask;
 }
}
static void check(GenDraw *ctx,int y,int l,int r,int color,int invert,int pattern,int full) {
 if(full){memset(a,pattern,sizeof(a));memset(b,pattern,sizeof(b));memset(expected,pattern,sizeof(expected));}
 else{memset(a+GUARD+100*STRIDE,pattern,STRIDE);memset(b+GUARD+100*STRIDE,pattern,STRIDE);memset(expected+GUARD+100*STRIDE,pattern,STRIDE);}
 GenDraw ca=*ctx,cb=*ctx;ca.shadow=a+GUARD;cb.shadow=b+GUARD;
 base_span(&ca,y,l,r,color,invert);cand_span(&cb,y,l,r,color,invert);oracle(ctx,y,l,r,color,invert);
 size_t start=full?0:GUARD+100*STRIDE, len=full?sizeof(a):STRIDE;
 if(memcmp(a+start,expected+start,len)||memcmp(b+start,expected+start,len)){
  fprintf(stderr,"FAIL width=%d test=%lu y=%d l=%d r=%d color=%d invert=%d clip=%d,%d,%d,%d\n",WIDTH,tests,y,l,r,color,invert,ctx->clipLeft,ctx->clipTop,ctx->clipRight,ctx->clipBottom);exit(1);
 }
 tests++;
}
int main(void){
 GenDraw c={0};c.clipRight=WIDTH;c.clipBottom=200;
 int pats[]={0,85,170,255};
 for(int byte=0;byte<WIDTH/8;byte++)for(int l=0;l<8;l++)for(int r=l+1;r<=8;r++)for(int color=0;color<16;color++)for(int inv=0;inv<3;inv++)for(int p=0;p<4;p++)check(&c,100,byte*8+l,byte*8+r,color,inv,pats[p],0);
 unsigned long exhaustive=tests;
 for(int i=0;i<100000;i++){
  int x1=(int)(rng()%(WIDTH+1)),x2=(int)(rng()%(WIDTH+1));c.clipLeft=x1<x2?x1:x2;c.clipRight=x1>x2?x1:x2;
  int y1=(int)(rng()%201),y2=(int)(rng()%201);c.clipTop=y1<y2?y1:y2;c.clipBottom=y1>y2?y1:y2;
  int y=(int)(rng()%204)-2,l=(int)(rng()%(WIDTH+32))-16,r=(int)(rng()%(WIDTH+32))-16,color=(int)(rng()%16),inv=(int)(rng()%3);
  check(&c,y,l,r,color,inv,(int)(rng()&255),1);
 }
 printf("{\"width\":%d,\"status\":\"PASS_NATIVE_SPAN_ONLY\",\"exhaustive_single_byte_cases\":%lu,\"random_clip_multi_byte_guard_cases\":100000,\"total_cases\":%lu,\"seed\":\"0x7c6a1f35\",\"oracle\":\"independent_pixel_model\",\"sanitizers\":\"address,undefined\"}\n",WIDTH,exhaustive,tests);
 return 0;
}
