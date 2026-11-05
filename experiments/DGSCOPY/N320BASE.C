#include "GENDRAW.H"
#ifdef HOST_TEST
#include <stdint.h>
typedef uintptr_t GenAddress;
#else
typedef unsigned long GenAddress;
#endif
static int range(const void _far *ptr,unsigned size,GenAddress _far *start,GenAddress _far *end){GenAddress u;
 if(!ptr||!size)return 0;
#ifdef HOST_TEST
 u=(GenAddress)ptr;
 if(u+size<u)return 0;
#else
 u=(GenAddress)ptr;
 if((u&65535UL)+(unsigned long)size>65536UL)return 0;
 u=(u>>16)*16UL+(u&65535UL);
 if(u+(unsigned long)size>1048576UL)return 0;
#endif
 *start=u;*end=u+size;return 1;
}
static int memory(const GenDraw _far *ctx,int _far *work,GenWalk _far *walk,GenPair _far *pair){GenAddress begin[5],end[5];int i,j;
 if(!range(ctx,sizeof(GenDraw),(GenAddress _far *)&begin[0],(GenAddress _far *)&end[0]))return 0;
 if(!range(ctx->shadow,32000U,(GenAddress _far *)&begin[1],(GenAddress _far *)&end[1])||!range(work,320U*sizeof(int),(GenAddress _far *)&begin[2],(GenAddress _far *)&end[2])||!range(walk,sizeof(GenWalk),(GenAddress _far *)&begin[3],(GenAddress _far *)&end[3])||!range(pair,sizeof(GenPair),(GenAddress _far *)&begin[4],(GenAddress _far *)&end[4]))return 0;
 for(i=0;i<5;i++)for(j=i+1;j<5;j++)if(begin[i]<end[j]&&begin[j]<end[i])return 0;
 return 1;
}
static void span(const GenDraw _far *c,int y,int l,int r,int color,int invert){unsigned first,last,n,plane,offset,mask;unsigned char value;
 if(y<0||y>=200||y<c->clipTop||y>=c->clipBottom)return;
 if(l<0)l=0;
 if(r>320)r=320;
 if(l<c->clipLeft)l=c->clipLeft;
 if(r>c->clipRight)r=c->clipRight;
 if(l>=r)return;
 first=(unsigned)l>>3;last=(unsigned)(r-1)>>3;
 for(plane=0;plane<4;plane++){
  if(invert==2&&!(color&(1U<<plane)))continue;
  for(n=first;n<=last;n++){
  mask=255U;
 if(n==first)mask&=255U>>((unsigned)l&7U);
 if(n==last)mask&=(255U<<(7U-((unsigned)(r-1)&7U)))&255U;
  offset=(unsigned)y*160U+plane*40U+n;value=c->shadow[offset];
  if(invert)value=(unsigned char)(value^mask);
  else if(color&(1U<<plane))value=(unsigned char)(value|mask);
  else value=(unsigned char)(value&~mask);
  c->shadow[offset]=value;
  }
 }
}
static void row(const GenDraw _far *c,const GenPair _far *p,int y){int l=c->x+p->left,r=c->x+p->right,il,ir,invert=c->rop==7?(c->penIndex==15?1:2):0;
 if(!p->innerRight)span(c,y,l,r,c->penIndex,invert);
 else{
  il=c->x+p->innerLeft;ir=c->x+p->innerRight;
  span(c,y,l,il,c->penIndex,invert);span(c,y,ir,r,c->penIndex,invert);
  if(c->brushStyle==0)span(c,y,il,ir,c->brushIndex,0);
 }
}
int _far _pascal GenDrawKernel(const GenDraw _far *c,int _far *work,GenWalk _far *walk,GenPair _far *pair){int mode,status;
 if(!memory(c,work,walk,pair))return -1;
 if(c->deviceWidth!=320||c->deviceHeight!=200||c->colors!=16||c->target!=1||c->enabled!=1||c->complexClip||c->logicalWidth!=1||c->penStyle!=0)return -1;
 if(c->width<2||c->width>320||c->height<2||c->height>200||c->x< -320||c->x>320||c->y< -200||c->y>200)return -1;
 if(c->clipLeft<0||c->clipLeft>c->clipRight||c->clipRight>320||c->clipTop<0||c->clipTop>c->clipBottom||c->clipBottom>200)return -1;
 mode=c->rop==13&&c->penIndex==0&&(c->brushStyle==1||(c->brushStyle==0&&c->brushIndex==9));
 if(!mode)mode=c->rop==7&&c->penIndex>=1&&c->penIndex<=15&&c->brushStyle==1;
 /* Preserve old XOR/black-fill contracts; new colored COPY is outline-only. */
 if(!mode)mode=c->rop==13&&c->penIndex>=1&&c->penIndex<=15&&c->brushStyle==1;
 if(!mode)return -1;
 if(c->clipLeft==c->clipRight||c->clipTop==c->clipBottom||c->x+c->width<=c->clipLeft||c->x>=c->clipRight||c->y+c->height<=c->clipTop||c->y>=c->clipBottom)return 1;
 if(!GenFarPrepare(c->width,c->height,work,walk))return -1;
 while((status=GenFarNext(walk,work,pair))>0){
  row(c,pair,c->y+pair->top);
  if(pair->mirror!=pair->top)row(c,pair,c->y+pair->mirror);
 }
 return status<0?0:1;
}
