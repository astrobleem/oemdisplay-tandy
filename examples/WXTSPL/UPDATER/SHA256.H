/* Existing first-party WXTSPL SHA implementation. */
typedef struct { U32 h[8], bytes; unsigned n; unsigned char b[64]; } SHA;
static const U32 K[64]={
0x428a2f98UL,0x71374491UL,0xb5c0fbcfUL,0xe9b5dba5UL,0x3956c25bUL,0x59f111f1UL,0x923f82a4UL,0xab1c5ed5UL,
0xd807aa98UL,0x12835b01UL,0x243185beUL,0x550c7dc3UL,0x72be5d74UL,0x80deb1feUL,0x9bdc06a7UL,0xc19bf174UL,
0xe49b69c1UL,0xefbe4786UL,0x0fc19dc6UL,0x240ca1ccUL,0x2de92c6fUL,0x4a7484aaUL,0x5cb0a9dcUL,0x76f988daUL,
0x983e5152UL,0xa831c66dUL,0xb00327c8UL,0xbf597fc7UL,0xc6e00bf3UL,0xd5a79147UL,0x06ca6351UL,0x14292967UL,
0x27b70a85UL,0x2e1b2138UL,0x4d2c6dfcUL,0x53380d13UL,0x650a7354UL,0x766a0abbUL,0x81c2c92eUL,0x92722c85UL,
0xa2bfe8a1UL,0xa81a664bUL,0xc24b8b70UL,0xc76c51a3UL,0xd192e819UL,0xd6990624UL,0xf40e3585UL,0x106aa070UL,
0x19a4c116UL,0x1e376c08UL,0x2748774cUL,0x34b0bcb5UL,0x391c0cb3UL,0x4ed8aa4aUL,0x5b9cca4fUL,0x682e6ff3UL,
0x748f82eeUL,0x78a5636fUL,0x84c87814UL,0x8cc70208UL,0x90befffaUL,0xa4506cebUL,0xbef9a3f7UL,0xc67178f2UL};
#define RR(x,n) (((x)>>(n))|((x)<<(32-(n))))
static void transform(SHA *s) {
 U32 w[64],a,b,c,d,e,f,g,h,t,u; unsigned i;
 for(i=0;i<16;i++)w[i]=((U32)s->b[i*4]<<24)|((U32)s->b[i*4+1]<<16)|((U32)s->b[i*4+2]<<8)|s->b[i*4+3];
 for(i=16;i<64;i++){a=w[i-15];b=w[i-2];w[i]=w[i-16]+(RR(a,7)^RR(a,18)^(a>>3))+w[i-7]+(RR(b,17)^RR(b,19)^(b>>10));}
 a=s->h[0];b=s->h[1];c=s->h[2];d=s->h[3];e=s->h[4];f=s->h[5];g=s->h[6];h=s->h[7];
 for(i=0;i<64;i++){t=h+(RR(e,6)^RR(e,11)^RR(e,25))+((e&f)^((~e)&g))+K[i]+w[i];u=(RR(a,2)^RR(a,13)^RR(a,22))+((a&b)^(a&c)^(b&c));h=g;g=f;f=e;e=d+t;d=c;c=b;b=a;a=t+u;}
 s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static void init(SHA *s){static const U32 h[8]={0x6a09e667UL,0xbb67ae85UL,0x3c6ef372UL,0xa54ff53aUL,0x510e527fUL,0x9b05688cUL,0x1f83d9abUL,0x5be0cd19UL};memcpy(s->h,h,sizeof(h));s->n=0;s->bytes=0;}
static void update(SHA *s,const unsigned char *p,unsigned n){s->bytes+=n;while(n--){s->b[s->n++]=*p++;if(s->n==64){transform(s);s->n=0;}}}
static void finish(SHA *s,char *out){unsigned i,j;U32 bits=s->bytes*8;static const char hex[]="0123456789abcdef";s->b[s->n++]=128;if(s->n>56){while(s->n<64)s->b[s->n++]=0;transform(s);s->n=0;}while(s->n<60)s->b[s->n++]=0;for(i=0;i<4;i++)s->b[60+i]=(unsigned char)(bits>>(24-i*8));transform(s);for(i=0;i<8;i++)for(j=0;j<4;j++){unsigned v=(unsigned)((s->h[i]>>(24-j*8))&255);*out++=hex[v>>4];*out++=hex[v&15];}*out=0;}
static int selftest(void){SHA s;char h[65];init(&s);finish(&s,h);if(strcmp(h,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"))return 0;init(&s);update(&s,(const unsigned char *)"abc",3);finish(&s,h);return !strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");}
