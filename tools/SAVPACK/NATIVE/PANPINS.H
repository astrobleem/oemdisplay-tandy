typedef struct {const char *name;unsigned long size,crc;int system;} PANFILE;
#define PAN_COUNT 7
static PANFILE pan_files[PAN_COUNT]={
 {"XTPAN.EXE",27407UL,0x3b3ce77aUL,0},
 {"XYCTL.EXE",33220UL,0x82a35b29UL,0},
 {"PANCTL.EXE",18591UL,0x419c14a9UL,0},
 {"CGACTL.EXE",25247UL,0x910a1ba4UL,0},
 {"PANCFG.EXE",11985UL,0xd1ce2cdeUL,0},
 {"PAN.EXE",11985UL,0xd1ce2cdeUL,0},
 {"PANKEY.DLL",2085UL,0x15cdf34aUL,1},
};
