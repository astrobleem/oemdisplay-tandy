#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "GIFCORE.H"
int main(int argc,char **argv){unsigned char b[4096],m[4096];FILE *f;size_t n,k;int i,j;unsigned state=17;if(argc!=4)return 2;f=fopen(argv[1],"rb");if(!f)return 2;n=fread(b,1,sizeof(b),f);fclose(f);if(!n)return 2;for(i=0;i<10000;i++){memcpy(m,b,n);k=n;state=state*1664525U+1013904223U;if(i%5==0)k=state%(n+1);else for(j=0;j<1+i%8;j++){state=state*1664525U+1013904223U;m[state%n]^=(unsigned char)(state>>17);}f=fopen(argv[2],"wb");fwrite(m,1,k,f);fclose(f);remove(argv[3]);gifconvert(argv[2],argv[3],16);}printf("PASS 10000 mutations\n");return 0;}
