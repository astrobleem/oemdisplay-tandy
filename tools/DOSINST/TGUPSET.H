/* Accept only the exact immediately preceding canonical Setup metadata.
 * Replace its two Tandy display grabber fields; no other bytes are edited. */
static void grabber_setup(void){
 unsigned i=0,o=0,count=0;
 while(i<49840U){
  if(i<=49840U-9U&&!memcmp(setup_bytes+i,"a:CGA.GR2",9)){
   if(o>SETUP_BYTES-13U)stop("Tandy Setup metadata overflow","");
   memcpy(setup_result+o,"a:TANDYGR.GR2",13);i+=9;o+=13;count++;
  }else{if(o>=SETUP_BYTES)stop("Tandy Setup metadata overflow","");setup_result[o++]=setup_bytes[i++];}
 }
 if(count!=2||o!=SETUP_BYTES||(crc_add(0xffffffffUL,setup_result,o)^0xffffffffUL)!=SETUP_OUTPUT_CRC)
  stop("Tandy Setup metadata conversion failed","");
 setup_used=o;
}
