/* Host address/content model, not a CPU or scanout emulator. C89. */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static unsigned char shadow[256][320], packed[256][320];
static unsigned char hw[32768], before[32768], occupied[32768];
static unsigned char stage[6400];
static unsigned short dest[6400];
static int weight[4]={4,2,1,8}; /* DDK R,G,B,I -> Tandy I,R,G,B */
static unsigned long cases, bank_wraps, safe_writes, unsafe_writes;
static double compared;

static int address(int xbyte,int y) {
    return (y&3)*8192+((y/4*160+xbyte)&8191);
}
static void require(int ok,const char *what) {
    if(!ok){fprintf(stderr,"FAIL %s case %lu\n",what,cases);exit(1);}
}
static void init(void) {
    int x,y,p,b,k; unsigned long n;
    for(y=0;y<256;y++)for(x=0;x<640;x++) {
        n=(unsigned long)(y*640+x)*2654435761UL;
        n^=n>>13;n*=2246822519UL;n^=n>>16;
        k=(int)(n&15);
        if(x&1)packed[y][x/2]|=(unsigned char)k;
        else packed[y][x/2]=(unsigned char)(k<<4);
        for(p=0;p<4;p++) {
            b=x/8+p*80;
            if(k&weight[p])shadow[y][b]|=(unsigned char)(128>>(x&7));
        }
    }
}
/* Same planar-byte -> packed-nibble contract as get_nibble, independently
   expressed per pixel. Checks the shadow band split at row 200. */
static int rect(int x0,int x1,int y0,int y1,int n) {
    int x,y,j,p,v,a,off;
    for(y=y0;y<y1;y++) {
        off=(y<200?y:y-200)*320;
        require(off>=0 && off+320<=(y<200?64000:17920),"shadow band");
        for(x=x0;x<x1;x+=8) {
            a=address(x/2,y);
            require((a&8191)<=8188,"four byte group does not cross bank");
            for(j=0;j<8;j+=2) {
                int q;v=0;
                for(q=0;q<2;q++) {
                    int c;c=0;
                    for(p=0;p<4;p++)if(shadow[y][p*80+x/8]&(128>>(j+q)))c|=weight[p];
                    v=(v<<4)|c;
                }
                require(v==packed[y][(x+j)/2],"conversion");
                require(n<(int)sizeof(stage),"stage allocation");
                dest[n]=(unsigned short)(a+j/2);stage[n++]=(unsigned char)v;
            }
            if((a&8191)==8188)bank_wraps++;
        }
    }
    return n;
}
static int clamp(int x,int hi,int step) {
    if(x<0)x=0;
    if(x>hi)x=hi;
    return x&~(step-1);
}
static void test(int ox,int oy,int nx,int ny,int prewrite) {
    int x,y,n,i,dx,dy,h0,h1,v0,v1,hy0,hy1,safe,unsafe;
    dx=nx-ox;dy=ny-oy;if(!dx&&!dy)return;
    if(100*abs(dx)+160*abs(dy)-abs(dx)*abs(dy)/2>5504)return;
    memset(hw,0x5a,sizeof(hw));memset(occupied,0,sizeof(occupied));
    for(y=oy;y<oy+200;y++)for(x=ox/2;x<ox/2+160;x++) {
        i=address(x,y);require(!occupied[i],"old injective");
        occupied[i]=1;hw[i]=packed[y][x];
    }
    memcpy(before,hw,sizeof(hw));n=0;
    /* Vertical strip owns the corner; horizontal strip covers shared Y. */
    hy0=ny>oy?ny:oy;hy1=ny+200<oy+200?ny+200:oy+200;
    h0=dx>0?ox+320:nx;h1=dx>0?nx+320:ox;
    v0=dy>0?oy+200:ny;v1=dy>0?ny+200:oy;
    if(dx)n=rect(h0,h1,hy0,hy1,n);
    if(dy)n=rect(nx,nx+320,v0,v1,n);
    require(n==100*abs(dx)+160*abs(dy)-abs(dx)*abs(dy)/2,"exact size");
    require(!memcmp(hw,before,sizeof(hw)),"stage has no VRAM side effects");
    safe=unsafe=0;
    for(i=0;i<n;i++) {
        if(!occupied[dest[i]]) {safe++;if(prewrite)hw[dest[i]]=stage[i];}
        else unsafe++;
    }
    if(prewrite)for(i=0;i<32768;i++)if(occupied[i])
        require(hw[i]==before[i],"prewrite preserves old visible bytes");
    /* Unsafe writes are permitted only in this modeled blanked phase. */
    for(i=0;i<n;i++)if(!prewrite||occupied[dest[i]])hw[dest[i]]=stage[i];
    for(y=ny;y<ny+200;y++)for(x=nx/2;x<nx/2+160;x++) {
        require(hw[address(x,y)]==packed[y][x],"new view equals full conversion");
    }
    compared+=32000.0;
    /* Stage canaries modeled by the exact allocation test above. */
    cases++;safe_writes+=safe;unsafe_writes+=unsafe;
}
static void counts(int dx,int dy) {
    int ox,oy,n,i,safe,unsafe,nx,ny;
    ox=dx<0?320:0;oy=dy<0?56:0;nx=ox+dx;ny=oy+dy;
    memset(occupied,0,sizeof(occupied));
    for(i=0;i<200;i++)for(n=0;n<160;n++)occupied[address(ox/2+n,oy+i)]=1;
    n=0;
    if(dx)n=rect(dx>0?ox+320:nx,dx>0?nx+320:ox,
        ny>oy?ny:oy,ny+200<oy+200?ny+200:oy+200,n);
    if(dy)n=rect(nx,nx+320,dy>0?oy+200:ny,dy>0?ny+200:oy,n);
    safe=unsafe=0;
    for(i=0;i<n;i++)if(occupied[dest[i]])unsafe++;else safe++;
    printf("%d,%d,%d,%d,%d\n",dx,dy,n,safe,unsafe);
}
int main(int argc,char **argv) {
    int x,y,dx,dy;init();
    if(argc>1 && !strcmp(argv[1],"counts")) {
        puts("dx,dy,unique_bytes,old_offscreen_bytes,old_visible_bytes");
        for(dy=-32;dy<=32;dy+=4)for(dx=-48;dx<=48;dx+=8)
            if((dx||dy) && 100*abs(dx)+160*abs(dy)-abs(dx)*abs(dy)/2<=5504)
                counts(dx,dy);
        return 0;
    }
    for(y=0;y<=56;y+=4)for(x=0;x<=320;x+=8)
        for(dy=-32;dy<=32;dy+=4)for(dx=-48;dx<=48;dx+=8)
            test(x,y,clamp(x+dx,320,8),clamp(y+dy,56,4),1);
    printf("{\"cases\":%lu,\"compared_bytes\":%.0f,\"bank_end_groups\":%lu,"
        "\"offscreen_prewrite_bytes\":%lu,\"blanked_bytes\":%lu,"
        "\"result\":\"PASS\",\"scope\":\"host content/address model only\"}\n",
        cases,compared,bank_wraps,safe_writes,unsafe_writes);
    return 0;
}
