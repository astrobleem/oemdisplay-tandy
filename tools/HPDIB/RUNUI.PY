"""Existing native UI transport plus owned watchdog and bounded raw Setup input."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tools/PAN/EMU86.PY';s=source.read_text()
def once(a,b):
 global s
 if s.count(a)!=1:raise ValueError('UI transport anchor changed: '+a[:50])
 s=s.replace(a,b)
once('import struct\n','import struct,threading\n')
once('keyserial=0;rom_ack=False','keyserial=0;rawserial=0;rom_ack=False')
anchor="       if g.read_memory(0x449,1)==b'\\x03':(out/'DOS-CURRENT.TXT').write_text(g.read_memory(0xb8000,4000)[::2].decode('cp437'),encoding='utf-8')"
once(anchor,"       if g.read_memory(0x449,1)==b'\\x03':\n        rawtext=g.read_memory(0xb8000,4000);(out/'DOS-RAW.BIN').write_bytes(rawtext);(out/'DOS-CURRENT.TXT').write_text(rawtext[::2].decode('cp437'),encoding='utf-8')")
anchor="     child={'pid':p.pid,'bound_seconds':args.seconds};runner.state['children'].append(child);runner.save()"
once(anchor,anchor+"\n     watch=threading.Timer(args.seconds+5,lambda:p.kill() if p.poll() is None else None);watch.daemon=True;watch.start()")
once("      child['stopped']=True;runner.save()","      watch.cancel();child['stopped']=True;runner.save()")
anchor="       if (c/'KEYS.JSON').exists():"
raw='''        if (c/'RAWKEYS.JSON').exists():
         request=json.loads((c/'RAWKEYS.JSON').read_text())
         if request['id']>rawserial:
          text=request.get('text','');taps=request.get('taps',[])
          assert isinstance(text,str) and len(text)<=128 and text.isascii()
          assert isinstance(taps,list) and len(taps)<=32 and all(type(n) is int and 0<n<128 for n in taps)
          def raw_input():
           if text:type_string(ctl,text)
           for scan in taps:
            ctl.key(True,scan);time.sleep(.15);ctl.key(False,scan);time.sleep(.15)
          g.run_while(raw_input,settle_seconds=2,start_delay=.05)
          rawserial=request['id'];(c/'RAWACK.JSON').write_text(json.dumps({'id':rawserial}))
          keytimes.append(dict(raw_id=rawserial,text=text,taps=taps,bios_ticks=int.from_bytes(g.read_memory(0x46c,4),'little')));(out/'RAWKEYS-LOG.JSON').write_text(json.dumps(keytimes,indent=2))
          (out/(stage+'-RAW'+str(rawserial)+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
'''
raw=''.join(line[1:] if line.startswith(' ') else line for line in raw.splitlines(keepends=True))
once(anchor,raw+anchor)
exec(compile(s,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
