/* Accepted previous/current font identities used before native replacement. */
static struct font_id {const char *name;unsigned long size,crc,oldcrc,narrowcrc;} fontid[]={
{"XTCSYS.FON",4592UL,0x8163a7eeUL,0x221afeaeUL,0xbe8c12adUL},
{"XTCFIX.FON",4208UL,0xa9e5a6feUL,0x00000000UL,0x00000000UL},
{"XTCOEM.FON",4560UL,0x0824b6daUL,0x00000000UL,0x00000000UL},
{"XTESYS.FON",5680UL,0xb7e664b6UL,0x00000000UL,0x00000000UL},
{"XTEFIX.FON",4656UL,0xd7fe66e1UL,0x00000000UL,0x00000000UL},
{"XTEOEM.FON",4560UL,0x0824b6daUL,0x00000000UL,0x00000000UL},
};
#define NFONTID (sizeof(fontid)/sizeof(fontid[0]))
