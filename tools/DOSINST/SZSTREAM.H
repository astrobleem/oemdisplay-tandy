/* Original bounded SZDD stream decoder. U32 must be a 32-bit unsigned type.
 * Caller supplies fixed 4096-byte ring and output buffers; no allocation,
 * seeks or 16-bit totals. emit returns zero on success. */
static char *szdd_stream(FILE *f,U32 want,unsigned char *ring,
 unsigned char *buf,int (*emit)(unsigned char *,unsigned,void *),void *ctx)
{
 unsigned char h[14]; U32 declared,pos=0;
 unsigned cursor=4080,used=0,flags,bit,off,len,j; int a,b,c;
 if(fread(h,1,14,f)!=14)return "Truncated SZDD header.";
 if(memcmp(h,"SZDD\210\360\047\063",8)||h[8]!='A'||h[9])
  return "Unsupported SZDD header.";
 declared=(U32)h[10]|((U32)h[11]<<8)|((U32)h[12]<<16)|((U32)h[13]<<24);
 if(!want||declared!=want)return "SZDD expanded size differs from its pin.";
 memset(ring,' ',4096);
 while(pos<want){
  c=fgetc(f);if(c==EOF)return "Truncated SZDD flags.";flags=(unsigned)c;
  for(bit=1;bit<256&&pos<want;bit<<=1){
   if(flags&bit){
    a=fgetc(f);if(a==EOF)return "Truncated SZDD literal.";
    ring[cursor]=(unsigned char)a;cursor=(cursor+1)&4095;
    buf[used++]=(unsigned char)a;pos++;
    if(used==4096){if(emit(buf,used,ctx))return "SZDD output callback failed.";used=0;}
   }else{
    a=fgetc(f);b=fgetc(f);if(a==EOF||b==EOF)return "Truncated SZDD reference.";
    off=(unsigned)a|(((unsigned)b&240)<<4);len=((unsigned)b&15)+3;
    if((U32)len>want-pos)return "SZDD reference exceeds declared length.";
    for(j=0;j<len;j++){
     c=ring[(off+j)&4095];ring[cursor]=(unsigned char)c;cursor=(cursor+1)&4095;
     buf[used++]=(unsigned char)c;pos++;
     if(used==4096){if(emit(buf,used,ctx))return "SZDD output callback failed.";used=0;}
    }
   }
  }
 }
 if(fgetc(f)!=EOF||ferror(f))return "Trailing bytes or read error after SZDD stream.";
 if(used&&emit(buf,used,ctx))return "SZDD output callback failed.";
 return NULL;
}
