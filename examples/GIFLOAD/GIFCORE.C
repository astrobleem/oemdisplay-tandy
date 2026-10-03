/* Original implementation from the published GIF grammar; no third-party codec.
 * C89, 16-bit unsigned/32-bit long safe, fixed storage, no full image buffer.
 */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#ifdef HOSTCLI
#include <unistd.h>
#ifndef O_BINARY
#define O_BINARY 0
#endif
#else
#include <io.h>
#endif
#include "GIFCORE.H"
static FILE *infile,*outfile;
static unsigned short prefix[4096];
static unsigned char suffix[4096],stackbuf[4096],pal[768],map[256],row[160];
static unsigned char target[48];
static unsigned width,height,stride,colors,depth,palcount,x,y,pass,interlace;
static unsigned remain,nbits;
static unsigned long bits,pixels;
static long offset;
static const char *error;
const char *giferror(void) { return error; }
static int fail(const char *s) { error=s;return 0; }
static int byte(void) { return getc(infile); }
static int getbytes(unsigned char *b,unsigned n) { return fread(b,1,n,infile)==n; }
static int skipblocks(void) { int n,i;while((n=byte())>0)for(i=0;i<n;i++)if(byte()<0)return 0;return n==0; }
static int putbyte(unsigned n) { return putc(n&255,outfile)!=EOF; }
static int putword(unsigned n) { return putbyte(n)&&putbyte(n>>8); }
static int putlong(unsigned long n) { return putword((unsigned)n)&&putword((unsigned)(n>>16)); }
static void palette(int mode) {
 unsigned i;static unsigned char ega[48]={0,0,0,0,0,128,0,128,0,0,128,128,128,0,0,128,0,128,128,128,0,128,128,128,64,64,64,0,0,255,0,255,0,0,255,255,255,0,0,255,0,255,255,255,0,255,255,255};
 static unsigned char cm[12]={0,0,0,0,255,255,255,0,255,255,255,255};
 static unsigned char rg[12]={0,0,0,255,0,0,0,255,0,255,255,255};
 memset(target,0,sizeof(target));colors=16;depth=4;
 if(mode==2){colors=2;depth=1;target[3]=target[4]=target[5]=255;}
 else if(mode==4||mode==5){colors=4;memcpy(target,mode==4?cm:rg,12);}
 else for(i=0;i<48;i++)target[i]=ega[i];
}
static void makemap(void) {
 unsigned i,j,k,best;long d,v,min;
 for(i=0;i<palcount;i++){min=200000L;best=0;for(j=0;j<colors;j++){d=0;for(k=0;k<3;k++){v=(long)pal[i*3+k]-target[j*3+k];d+=v*v;}if(d<min){min=d;best=j;}}map[i]=(unsigned char)best;}
}
static int bmpheader(void) {
 unsigned i,n;stride=((width*depth+31)/32)*4;offset=54L+(long)colors*4;
 if(!putword(0x4d42)||!putlong(offset+(long)stride*height)||!putlong(0)||!putlong(offset)||!putlong(40)||!putlong(width)||!putlong(height)||!putword(1)||!putword(depth)||!putlong(0)||!putlong((long)stride*height)||!putlong(0)||!putlong(0)||!putlong(colors)||!putlong(colors))return 0;
 for(i=0;i<colors;i++)if(!putbyte(target[i*3+2])||!putbyte(target[i*3+1])||!putbyte(target[i*3])||!putbyte(0))return 0;
 memset(row,0,sizeof(row));for(n=0;n<height;n++)if(fwrite(row,1,stride,outfile)!=stride)return 0;
 return 1;
}
static int pixel(unsigned v) {
 static unsigned starts[4]={0,4,2,1},steps[4]={8,8,4,2};
 if(v>=palcount)return fail("Pixel outside palette");
 if(pixels>=(unsigned long)width*height)return fail("Too many pixels");
 v=map[v];if(depth==1)row[x>>3]|=(unsigned char)(v<<(7-(x&7)));else row[x>>1]|=(unsigned char)(v<<((x&1)?0:4));
 x++;pixels++;
 if(x==width){if(y>=height)return fail("Invalid row");if(fseek(outfile,offset+(long)(height-1-y)*stride,SEEK_SET)||fwrite(row,1,stride,outfile)!=stride)return fail("Cannot write BMP");memset(row,0,sizeof(row));x=0;
 if(!interlace)y++;else {y+=steps[pass];while(y>=height&&pass<3)y=starts[++pass];}}
 return 1;
}
/* GIF data bytes are little-bit-endian and may cross sub-block boundaries. */
static int code(unsigned size) {
 int b;unsigned v;
 while(nbits<size){if(!remain){b=byte();if(b<=0)return -1;remain=(unsigned)b;}b=byte();if(b<0)return -1;remain--;bits|=(unsigned long)b<<nbits;nbits+=8;}
 v=(unsigned)(bits&((1U<<size)-1));bits>>=size;nbits-=size;return (int)v;
}
static int decode(void) {
 int c,min=byte(),firstcode;unsigned clear,end,next,size,old=0,first=0,cur,n,i;int have=0;
 if(min<2||min>8)return fail("Invalid LZW minimum");
 clear=1U<<min;end=clear+1;next=end+1;size=min+1;remain=nbits=0;bits=0;pixels=0;x=y=pass=0;
 firstcode=code(size);if(firstcode!=(int)clear)return fail("Missing initial clear");
 for(;;){c=code(size);if(c<0)return fail("Truncated LZW stream");
 if(c==(int)clear){next=end+1;size=min+1;have=0;continue;}
 if(c==(int)end)break;
 if(!have){if((unsigned)c>=clear)return fail("Invalid first LZW code");first=old=(unsigned)c;if(!pixel(first))return 0;have=1;continue;}
 cur=(unsigned)c;n=0;
 if(cur==next){stackbuf[n++]=(unsigned char)first;cur=old;}else if(cur>next)return fail("Invalid LZW code");
 while(cur>=clear){if(cur>=next||cur<=end||n>=4095)return fail("Invalid LZW chain");stackbuf[n++]=suffix[cur];cur=prefix[cur];}
 first=cur;stackbuf[n++]=(unsigned char)first;
 for(i=n;i;i--)if(!pixel(stackbuf[i-1]))return 0;
 if(next<4096){prefix[next]=(unsigned short)old;suffix[next]=(unsigned char)first;next++;if(next==(1U<<size)&&size<12)size++;}
 old=(unsigned)c;
 }
 if(pixels!=(unsigned long)width*height)return fail("Wrong pixel count");
 /* End code may leave padding bits, but no extra image-data bytes. */
 while(remain){if(byte()<0)return fail("Truncated data block");remain--;}
 if(byte()!=0)return fail("Data after LZW end");
 return 1;
}
static int parse(void) {
 unsigned char h[6],d[7],id[9],gce[4];int tag,label;unsigned flags;int seen=0,gct=0;
 if(!getbytes(h,6)||(memcmp(h,"GIF87a",6)&&memcmp(h,"GIF89a",6)))return fail("Not GIF87a/GIF89a");
 if(!getbytes(d,7))return fail("Truncated screen");
 width=d[0]+((unsigned)d[1]<<8);height=d[2]+((unsigned)d[3]<<8);
 if(!width||width>320||!height||height>200)return fail("Limit is 320 by 200");
 if(d[4]&128){palcount=2U<<(d[4]&7);if(!getbytes(pal,palcount*3))return fail("Truncated palette");gct=1;}
 while((tag=byte())!=0x3b){if(tag<0)return fail("Missing GIF trailer");
 if(tag==0x21){label=byte();if(label==0xf9){if(seen)return fail("Control after image");if(byte()!=4||!getbytes(gce,4)||byte()!=0)return fail("Invalid control block");if(gce[0]&1)return fail("Transparency unsupported");if((gce[0]&0xe2)||((gce[0]>>2)&7)>3)return fail("Unsupported control flags");}
 else if(label==0xfe){if(!skipblocks())return fail("Truncated comment");}
 else return fail("Application/text extensions unsupported");
 }else if(tag==0x2c){if(seen)return fail("Multiple images unsupported");seen=1;if(!getbytes(id,9))return fail("Truncated image descriptor");
 if(id[0]||id[1]||id[2]||id[3]||id[4]+((unsigned)id[5]<<8)!=width||id[6]+((unsigned)id[7]<<8)!=height)return fail("Subrect images unsupported");
 flags=id[8];if(flags&0x18)return fail("Reserved image flags");interlace=flags&64;
 if(flags&128){palcount=2U<<(flags&7);if(!getbytes(pal,palcount*3))return fail("Truncated local palette");}else if(!gct)return fail("Missing palette");
 makemap();if(!bmpheader())return fail("Cannot write BMP");if(!decode())return 0;
 }else return fail("Unknown GIF block");}
 if(!seen)return fail("No image");
 if(byte()!=EOF)return fail("Trailing data");
 return 1;
}
int gifconvert(const char *input,const char *output,int mode) {
 long size;int ok,fd;
 error="OK";infile=outfile=NULL;
 if(mode!=2&&mode!=4&&mode!=5&&mode!=16)return fail("Invalid output mode");
 /* Refuse any existing destination, including the input itself. */
 infile=fopen(input,"rb");if(!infile)return fail("Cannot open GIF");
 if(fseek(infile,0,SEEK_END)||(size=ftell(infile))<0||size>262144L||fseek(infile,0,SEEK_SET)){fclose(infile);return fail("Input exceeds 256 KB");}
 fd=open(output,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);
 if(fd<0){fclose(infile);return fail("Output exists or cannot create");}
 outfile=fdopen(fd,"wb");if(!outfile){close(fd);remove(output);fclose(infile);return fail("Cannot open BMP stream");}
 palette(mode);ok=parse();if(ferror(infile))ok=fail("Cannot read GIF");fclose(infile);
 if(fclose(outfile))ok=fail("Cannot close BMP");
 if(!ok&&remove(output))fail("Failed; cannot remove output");
 return ok;
}
#ifdef HOSTCLI
#include <stdlib.h>
int main(int argc,char **argv){if(argc!=4){fprintf(stderr,"gifconvert input.gif output.bmp mode[2,4,5,16]\n");return 2;}if(!gifconvert(argv[1],argv[2],atoi(argv[3]))){fprintf(stderr,"%s\n",giferror());return 1;}return 0;}
#endif
