/* Host-only validation of the exact shared streaming decoder. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned long U32;
#include "SZSTREAM.H"
static unsigned char ring[4096],buf[4096];
static FILE *out;
static unsigned calls,failat;
static int emit(unsigned char *p,unsigned n,void *ctx)
{
 ctx=ctx;calls++;
 if(calls==failat){if(n>1)fwrite(p,1,n/2,out);return 1;}
 return fwrite(p,1,n,out)!=n;
}
int main(int argc,char **argv)
{
 FILE *f;char *error;int bad;
 if(argc!=5||sizeof(U32)!=4)return 2;
 f=fopen(argv[1],"rb");if(!f)return 2;
 out=fopen(argv[2],"wb");if(!out){fclose(f);return 2;}
 failat=(unsigned)atoi(argv[4]);
 error=szdd_stream(f,strtoul(argv[3],NULL,10),ring,buf,emit,NULL);
 bad=ferror(f);if(fclose(f))bad=1;if(fclose(out))bad=1;
 if(error||bad){remove(argv[2]);if(error)puts(error);return 1;}
 return 0;
}
