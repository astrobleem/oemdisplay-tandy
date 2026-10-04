#!/usr/bin/env python3
"""Compile the exact native cursor rasterizer in an instrumented C89 host harness."""
from pathlib import Path
import os,subprocess,tempfile
src=Path(__file__).resolve().parent
code=(src/'SWAT.C').read_text();a=code.index('static void rawCursor(void)');b=code.index('static int initClientCursor',a)
head='''#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n#include "SWATCUR.H"\nstatic int screenW,stride,cursorX,cursorY;\nstatic unsigned char mono[16000];\n'''
body=r'''
int main(void){int widths[3]={160,320,640},bg,wi,k,x,y,cx,cy,n;unsigned bit;unsigned char expected[16000];
 for(y=0;y<16;y++){assert((curWhite[y]&~curMask[y])==0);for(x=0;x<16;x++)if(curMask[y]&(0x8000U>>x)){assert(x-CURHOT>=-6&&x-CURHOT<8);assert(y-CURHOT>=-6&&y-CURHOT<11);}}
 for(wi=0;wi<3;wi++){screenW=widths[wi];stride=screenW/8;
  for(bg=0;bg<2;bg++)for(k=0;k<6;k++){cursorX=k==0?0:k==1?screenW-1:k==2?-4:k==3?screenW+4:screenW/2;cursorY=k==0?0:k==1?199:k==2?-4:k==3?203:k==4?100:6;
   memset(mono,bg?255:0,sizeof mono);memcpy(expected,mono,sizeof mono);
   for(y=0;y<16;y++)for(x=0;x<16;x++){bit=0x8000U>>x;cx=cursorX-CURHOT+x;cy=cursorY-CURHOT+y;if(!(curMask[y]&bit)||cx<0||cx>=screenW||cy<0||cy>=200)continue;n=cy*stride+(cx>>3);if(curWhite[y]&bit)expected[n]|=128>>(cx&7);else expected[n]&=~(128>>(cx&7));}
   rawCursor();assert(memcmp(mono,expected,sizeof mono)==0);
  }
 }
 puts("PASS exact native rasterizer: black/white contrast, clipping, all widths, dirty bounds");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='swat-cursor-') as td:
 p=Path(td)/'cursor.c';p.write_text(head+code[a:b]+body);exe=Path(td)/'test'
 subprocess.run(['gcc','-x','c','-std=c89','-Wall','-Wextra','-fsanitize=address,undefined','-g','-I',str(src),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'},check=True)
