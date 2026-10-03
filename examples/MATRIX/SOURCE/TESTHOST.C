#define MATRIX_HOST
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "MATRIX.C"
static unsigned char marked[MAXCELL];
static void dirty(int c,int r){assert(c>=0&&c<columns&&r>=0&&r<ROWS);marked[r*columns+c]=1;}
static int pixel(unsigned char *p,int x,int k){if(k==0)return (p[x/2]>>((1-x%2)*4))&15;if(k==1)return(p[x/4]>>((3-x%4)*2))&3;if(k==2)return((p[0]>>(7-x))&1)|(((p[1]>>(7-x))&1)<<1);return(p[0]>>(7-x))&1;}
int main(int argc,char **argv){int cols,c,r,t,n,h,d,expected,k,s,y,b,x,banks,w,count;unsigned off;unsigned char before[MAXCELL],prev[MAXCELL],row[4],frame[32768];FILE *f;
 for(cols=20;cols<=80;cols*=2){resetRain(cols);for(t=0;t<10000;t++){memcpy(before,level,MAXCELL);memcpy(prev,glyph,MAXCELL);memset(marked,0,MAXCELL);stepRain();for(c=0;c<cols;c++)for(r=0;r<ROWS;r++){n=r*cols+c;h=head[c];d=h-r;expected=d<0||d>=length[c]?0:d==0?3:d<length[c]/2?2:1;assert(level[n]==expected);assert(glyph[n]<32);if(level[n]!=before[n]||glyph[n]!=prev[n])assert(marked[n]);}}}
 for(k=0;k<4;k++)for(s=0;s<4;s++)for(y=0;y<8;y++)for(b=0;b<256;b++){memset(row,0,4);packedRow(row,b,s,k,y);for(x=0;x<8;x++){expected=s==0?0:k==0?(s==3?15:s==2?10:2):k==1?(s==3?3:1):k==2?(s==3?3:2):1;d=b;if(k!=0&&s==1)d&=(y&1)?0xAA:0x55;if(k==3&&s==2)d&=(y&1)?0xFF:0xDD;if(!(d&(128>>x)))expected=0;assert(pixel(row,x,k)==expected);}}
 for(w=160;w<=640;w*=2)for(banks=2;banks<=4;banks+=2){if((banks==4&&w==160)||(banks==2&&w!=160))continue;for(y=0;y<200;y++){off=rowOffset(y,banks);assert(off+(banks==4?160:80)<=(unsigned)(banks==4?32768:16384));assert(off%8192+(banks==4?160:80)<=8000);}}
 puts("PASS: 30,000 rain ticks; exact shade/glyph/dirty invariants; 262,144 packed pixels; visible row bounds/padding.");
 if(argc==4){w=atoi(argv[2]);k=atoi(argv[3]);banks=(k==2||(k==0&&w==320))?4:2;resetRain(w/8);for(t=0;t<40;t++)stepRain();memset(frame,0,32768);count=k==0?4:k==3?1:2;for(r=0;r<25;r++)for(c=0;c<columns;c++){n=r*columns+c;for(y=0;y<8;y++){packedRow(row,font[glyph[n]][y],level[n],k,y);off=rowOffset(r*8+y,banks)+c*count;for(x=0;x<count;x++)frame[off+x]=row[x];}}f=fopen(argv[1],"wb");assert(f);fwrite(frame,1,banks==4?32768:16384,f);fclose(f);}
 return 0;}
