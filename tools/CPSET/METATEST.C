/* Host-only access to the same bounded metadata parser and CRC routine. */
#define main cpset_program_main
#include "CPSET.C"
#undef main
int main(int argc,char **argv)
{
 if(argc!=3)return 2;
 buffers();on=readall(argv[2],orig,MAXINI);
 if(!strcmp(argv[1],"crc"))printf("%08lx\n",(unsigned long)input_crc(orig,on));
 else if(!strcmp(argv[1],"layout")){metadata_layout();puts("PASS");}
 else if(!strcmp(argv[1],"source")){source();puts("PASS");}
 else if(!strcmp(argv[1],"verify")){deep_verify=1;source();puts("PASS");}
 else return 2;
 free(dest);free(cur);free(orig);return 0;
}
