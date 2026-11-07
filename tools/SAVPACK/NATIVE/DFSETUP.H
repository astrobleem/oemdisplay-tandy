/* Private exact-metadata migration; no owned input is embedded. */
static void default_setup(unsigned size){
 unsigned o=0;
 if(size==49848U){
  memcpy(setup_result+o,setup_bytes+0U,3309U);o+=3309U;
  memcpy(setup_result+o,"cga = a:TANDY88.DRV, \"Tandy EX/HX 320x200 16 colors (no panning)\", \"133,96,72\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\n",130U);o+=130U;
  memcpy(setup_result+o,setup_bytes+3431U,2088U);o+=2088U;
  memcpy(setup_result+o,"fixed = a:TANDY88.DRV, \"Tandy EX/HX 320x200 16 colors (no panning)\", \"133,96,72\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed6404 = a:TNDY6404.DRV, \"Tandy EX/HX 640x200 4 colors (red/green/white)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed3204 = a:TNDY3204.DRV, \"Tandy EX/HX 320x200 4 colors (cyan/magenta/white)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed160 = a:TNDY160.DRV, \"Tandy EX/HX 160x200 16 colors (no panning)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed6402 = a:TNDY6402.DRV, \"Tandy EX/HX 640x200 monochrome (no panning)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\n",690U);o+=690U;
  memcpy(setup_result+o,setup_bytes+5519U,24828U);o+=24828U;
  memcpy(setup_result+o,"        fixed\r\n",15U);o+=15U;
  memcpy(setup_result+o,setup_bytes+30361U,19487U);o+=19487U;
 }
 else if(size==49840U){
  memcpy(setup_result+o,setup_bytes+0U,3309U);o+=3309U;
  memcpy(setup_result+o,"cga = a:TANDY88.DRV, \"Tandy EX/HX 320x200 16 colors (no panning)\", \"133,96,72\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\n",130U);o+=130U;
  memcpy(setup_result+o,setup_bytes+3427U,2088U);o+=2088U;
  memcpy(setup_result+o,"fixed = a:TANDY88.DRV, \"Tandy EX/HX 320x200 16 colors (no panning)\", \"133,96,72\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed6404 = a:TNDY6404.DRV, \"Tandy EX/HX 640x200 4 colors (red/green/white)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed3204 = a:TNDY3204.DRV, \"Tandy EX/HX 320x200 4 colors (cyan/magenta/white)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed160 = a:TNDY160.DRV, \"Tandy EX/HX 160x200 16 colors (no panning)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed6402 = a:TNDY6402.DRV, \"Tandy EX/HX 640x200 monochrome (no panning)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nhpxy = a:HPXY.DRV, \"Tandy EX/HX HPXY 640x256 hardware pan\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\n",813U);o+=813U;
  memcpy(setup_result+o,setup_bytes+5634U,24705U);o+=24705U;
  memcpy(setup_result+o,"        fixed\r\n",15U);o+=15U;
  memcpy(setup_result+o,setup_bytes+30353U,19487U);o+=19487U;
 }
 else if(size==49989U){
  memcpy(setup_result+o,setup_bytes+0U,5659U);o+=5659U;
  memcpy(setup_result+o,"fixed6404 = a:TNDY6404.DRV, \"Tandy EX/HX 640x200 4 colors (red/green/white)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed3204 = a:TNDY3204.DRV, \"Tandy EX/HX 320x200 4 colors (cyan/magenta/white)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed160 = a:TNDY160.DRV, \"Tandy EX/HX 160x200 16 colors (no panning)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\nfixed6402 = a:TNDY6402.DRV, \"Tandy EX/HX 640x200 monochrome (no panning)\", \"200,96,48\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\n",558U);o+=558U;
  memcpy(setup_result+o,setup_bytes+5659U,44330U);o+=44330U;
 }
 else stop("Unsupported prior Setup metadata","");
 if(o!=SETUP_BYTES||(crc_add(0xffffffffUL,setup_result,o)^0xffffffffUL)!=SETUP_OUTPUT_CRC)
  stop("Fixed-default Setup metadata conversion failed","");
 setup_used=o;
}
