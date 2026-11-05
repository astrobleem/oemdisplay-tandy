#include "GENDECO.H"
#ifdef HOST_TEST
#include <stdint.h>
typedef uintptr_t GenAddress;
#else
typedef unsigned long GenAddress;
#endif
static int range(const void _far *p,unsigned size,GenAddress _far *begin,GenAddress _far *end){GenAddress n;
 if(!p||!size)return 0;
#ifdef HOST_TEST
 n=(GenAddress)p;if(n+size<n)return 0;
#else
 n=(GenAddress)p;if((n&65535UL)+(unsigned long)size>65536UL)return 0;n=(n>>16)*16UL+(n&65535UL);if(n+(unsigned long)size>1048576UL)return 0;
#endif
 *begin=n;*end=n+size;return 1;
}
static unsigned word(const unsigned char _far *p,int n){return (unsigned)p[n]|((unsigned)p[n+1]<<8);}
static int disjoint(GenAddress a,GenAddress b,GenAddress c,GenAddress d){return a>=d||c>=b;}
int _far _pascal GenDecode(const GenObjects _far *in,GenRequest _far *out){GenAddress begin[8],end[8];int i,j,n=0,x2,y2;unsigned p;GenRequest temp;
 if(!range(in,sizeof(GenObjects),(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;
 if(!range(out,sizeof(GenRequest),(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;
 if(!disjoint(begin[0],end[0],begin[1],end[1]))return -1;
 if(in->style!=7||in->count!=2)return -1;
 if(!range(in->device,32,(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;
 if(!range(in->points,8,(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;
 if(!range(in->pen,6,(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;
 /* Reject NULL/unknown physical style before reading the extension. */
 if(word(in->pen,4)!=0)return -1;
 if(!range(in->pen,16,(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;
 if(!range(in->mode,32,(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;
 if(in->brush){if(!range(in->brush,54,(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;}
 if(in->clip){if(!range(in->clip,8,(GenAddress _far *)&begin[n],(GenAddress _far *)&end[n]))return -1;n++;}
 /* Read-only sources may not alias each other or the private output. */
 for(i=0;i<n;i++)for(j=i+1;j<n;j++)if(!disjoint(begin[i],end[i],begin[j],end[j]))return -1;
 if(word(in->device,0)!=1||word(in->device,2)!=160||word(in->device,4)!=200||word(in->device,6)!=20||in->device[8]!=4||in->device[9]!=1||word(in->device,14)!=4000)return -1;
 for(i=10;i<32;i+=2)if(i!=14&&word(in->device,i))return -1;
 if(word(in->pen,6)!=0xe117U||word(in->pen,8)>1||word(in->pen,10)!=0||word(in->pen,12)!=0||word(in->pen,14)!=0x3cc3U)return -1;
 temp.rop=(int)word(in->mode,0);if(word(in->mode,2)!=1&&word(in->mode,2)!=2)return -1;
 p=word(in->pen,0);if(temp.rop==13&&p==0&&in->pen[2]==0&&(in->pen[3]&15)==0)temp.penIndex=0;
 else if(temp.rop==7&&p==65535U&&in->pen[2]==255&&(in->pen[3]&15)==15)temp.penIndex=15;
 /* New COPY admission requires the exact canonical white flags. */
 else if(temp.rop==13&&p==65535U&&in->pen[2]==255&&in->pen[3]==63U)temp.penIndex=15;
 else if(temp.rop==7||temp.rop==13){
  /* Fixed compiled PColorTable consistency; RGB bytes are80/FF, not plane masks. */
  temp.penIndex=in->pen[3]&15;if(temp.penIndex<1||temp.penIndex==15)return -1;
  if((in->pen[3]&240U)!=((temp.penIndex==10||temp.penIndex==11||temp.penIndex==13||temp.penIndex==14)?16U:0U))return -1;
  p=temp.penIndex==8?64U:(temp.penIndex&8)?255U:128U;
  for(i=0;i<3;i++)if((unsigned)in->pen[i]!=(temp.penIndex==8?p:(temp.penIndex&(1U<<i))?p:0U))return -1;
 }
 else return -1;
 /* Initial dispatcher admits outlines only; every filled/pattern brush rejects. */
 if(in->brush&&word(in->brush,40)!=1)return -1;
 temp.x=(short)word(in->points,0);temp.y=(short)word(in->points,2);x2=(short)word(in->points,4);y2=(short)word(in->points,6);
 if(temp.x< -160||temp.x>160||temp.y< -200||temp.y>200||x2< -160||x2>320||y2< -200||y2>400)return -1;
 temp.width=x2-temp.x;temp.height=y2-temp.y;if(temp.width<2||temp.width>160||temp.height<2||temp.height>200)return -1;
 temp.logicalWidth=1;temp.penStyle=0;temp.brushStyle=1;temp.brushIndex=9;temp.complexClip=0;
 temp.clipLeft=temp.clipTop=0;temp.clipRight=160;temp.clipBottom=200;
 if(in->clip){temp.clipLeft=(short)word(in->clip,0);temp.clipTop=(short)word(in->clip,2);temp.clipRight=(short)word(in->clip,4);temp.clipBottom=(short)word(in->clip,6);if(temp.clipLeft<0||temp.clipLeft>temp.clipRight||temp.clipRight>160||temp.clipTop<0||temp.clipTop>temp.clipBottom||temp.clipBottom>200)return -1;}
 for(i=0;i<15;i++)((int _far *)out)[i]=((const int _far *)&temp)[i];return 1;
}
