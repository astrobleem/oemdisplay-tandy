"""Stage optional fixed modes atop the private saver candidate; no acceptance."""
from pathlib import Path
import argparse,ast,hashlib,importlib.machinery,re,shutil,zlib
HERE=Path(__file__).resolve().parent
F=importlib.machinery.SourceFileLoader('combined_fixed',str(HERE.parent/'FIXDFLT/STAGE.PY')).load_module()
MODES=('TNDY6404.DRV','TNDY3204.DRV','TNDY160.DRV','TNDY6402.DRV')

def once(text,old,new):return F.once(text,old,new)
def write(path,text):F.write(path,text)

def insert_operations(header,stock,old,new):
    # The mode transformer must insert one contiguous block and preserve all old bytes.
    pos=next((i for i,(a,b) in enumerate(zip(old,new)) if a!=b),len(old))
    extra=len(new)-len(old)
    assert extra>0 and new[:pos]==old[:pos] and new[pos+extra:]==old[pos:]
    insertion=new[pos:pos+extra].decode('ascii')
    start=header.index('static struct patch_op operations[]={')+len('static struct patch_op operations[]={')
    end=header.index('\n};',start)
    rows=re.findall(r'\{(\d+),(\d+),(NULL|"(?:[^"\\]|\\.)*")\},',header[start:end])
    result=[];offset=0;inserted=False
    for a,b,text in rows:
        a=int(a);b=int(b);value=stock[a:b] if text=='NULL' else ast.literal_eval(text).encode('ascii')
        if not inserted and offset<=pos<=offset+len(value):
            cut=pos-offset
            if cut:
                result.append('{%d,%d,%s},'%(a,a+cut,'NULL') if text=='NULL' else '{0,0,%s},'%F.ctext(value[:cut].decode('ascii')))
            result.append('{0,0,%s},'%F.ctext(insertion))
            if cut<len(value):
                result.append('{%d,%d,NULL},'%(a+cut,b) if text=='NULL' else '{0,0,%s},'%F.ctext(value[cut:].decode('ascii')))
            inserted=True
        else:result.append('{%d,%d,%s},'%(a,b,text))
        offset+=len(value)
    assert inserted
    header=header[:start]+'\n'+'\n'.join(result)+header[end:]
    assert F.setup_bytes(header,stock)==new
    return header

def finisher_sizes(native,payload,metadata):
    source=(native/'FIXXT.C').read_text();match=re.search(r'static const char \*names\[\]=\{(.*?)\};',source)
    names=re.findall(r'"([A-Z0-9.]+)"',match[1]);m=re.search(r'static unsigned long sizes\[\]=\{(.*?)\};',source);sizes=m[1].split(',')
    for n,b in payload.items():
        if n in names:sizes[names.index(n)]=str(len(b))+'UL'
    sizes[names.index('SETUP.INF')]=str(len(metadata))+'UL'
    write(native/'FIXXT.C',source[:m.start(1)]+','.join(sizes)+source[m.end(1):])

def guides(readme,display):
    readme=readme.decode('ascii').replace('\r\n','\n')
    display=display.decode('ascii').replace('\r\n','\n')
    readme=once(readme,
        'choose Display, Other, enter that folder and select fixed 320x200\n16 colors or the optional Tandy EX/HX HPXY panning display.',
        'choose Display, Other, enter that folder and select a fixed display:\n'
        '320x200 16 colors, 640x200 4 colors, 320x200 4 colors,\n'
        '160x200 16 colors or 640x200 2 colors. HPXY panning is also optional.')
    readme=once(readme,'DRIVERS ONLY (DOS 3.20+; existing Windows)',
        'SCREEN SAVERS\n'
        'Tandy Start includes Cube, Starfield, Matrix and Ovals. Select one in\n'
        'System > Screen saver. The default idle delay remains five minutes;\n'
        'updates preserve your existing settings.\n\n'
        'DRIVERS ONLY (DOS 3.20+; existing Windows)')
    display=once(display,
        '3. Select Tandy EX/HX HPXY 640x256 hardware pan and Complete Changes.',
        '3. Select a Tandy EX/HX fixed display: 320x200 16 colors,\n'
        '   640x200 4 colors, 320x200 4 colors, 160x200 16 colors or\n'
        '   640x200 2 colors. HPXY 640x256 hardware pan is also optional.\n'
        '   Choose Complete Changes. Full desktop Setup defaults to fixed\n'
        '   320x200 16 colors; these optional choices are selected here.')
    display=once(display,
        '   Inside Windows run XYCTL.EXE from that folder for viewport controls.',
        '   For HPXY, run XYCTL.EXE inside Windows for viewport controls.')
    return tuple(x.replace('\n','\r\n').encode('ascii') for x in (readme,display))

def stage(candidate,drivers,transformer,stock_path,out):
    assert not out.exists(),'Fresh output required'
    stock=stock_path.read_bytes();old=F.setup_bytes((candidate/'native/SETFILES.H').read_text(),stock)
    transform=importlib.machinery.SourceFileLoader('combined_mode_transform',str(transformer)).load_module().transform
    new=transform(old);body={p.name:p.read_bytes() for p in (candidate/'expanded/WINXT').iterdir() if p.is_file()}
    body['OEMSETUP.INF']=transform(body['OEMSETUP.INF'])
    readme,body['DISPLAY.TXT']=guides((candidate/'expanded/README.TXT').read_bytes(),body['DISPLAY.TXT'])
    for n in ('TANDY88.DRV',*MODES):
        b=(drivers/n).read_bytes();assert b[:2]==b'MZ',n;body[n]=b
    shutil.copytree(candidate,out)
    native=out/'native'
    (out/'expanded/README.TXT').write_bytes(readme)
    for n in ('FIXXT.EXE','SETUP.EXE','CPSET.EXE'):
        p=native/n
        if p.exists():p.unlink()
    header=insert_operations((native/'SETFILES.H').read_text(),stock,old,new)
    crcs=(native/'SETINPUT.H').read_text()
    for n in MODES:
        for prefix in ('WINXT\\\\','WINXT\\\\FILES\\\\','W30\\\\'):
            dest=prefix+n;assert '{"'+dest+'",' not in header
            header=once(header,'};\n#define NFILES','{"%s","%s",%dUL,0},\n};\n#define NFILES'%(dest,n,len(body[n])))
            crcs=once(crcs,'};',' 0x00000000UL, /* '+dest+' */\n};')
    write(native/'SETFILES.H',header);write(native/'SETINPUT.H',crcs)
    # Keep both earlier migration routes and add the exact released fixed-default route.
    hist=F.setup_bytes((HERE.parent/'DOSINST/SETFILES.H').read_text(),stock)
    previous=[(hist,zlib.crc32(hist)),(hist.replace(b'a:TANDYGR.GR2',b'a:CGA.GR2'),0),(old,zlib.crc32(old))]
    previous=[(b,zlib.crc32(b)) for b,_ in previous]
    assert [len(b) for b,_ in previous]==[49848,49840,49989]
    write(native/'DFSETUP.H',F.migration_header(previous,new))
    source=(native/'XRPREP.C').read_text()
    a=source.index('#ifdef EXPANDED_SETUP\n else if(!locate_input("SETUP.INF",49046UL,path)');b=source.index('#endif',a)
    clauses=['#ifdef EXPANDED_SETUP']
    for raw,crc in previous:
        size=len(raw)
        clauses.append(''' else if(!locate_input("SETUP.INF",49046UL,path)&&!locate_input("SETUP.INF",49095UL,path)&&locate_input("SETUP.INF",%dUL,path)){
  memset(&setup_sink,0,sizeof(setup_sink));setup_sink.memory=setup_bytes;setup_sink.limit=%dUL;
  read_stream(path,%dUL,&setup_sink);
  if((crc_add(0xffffffffUL,setup_bytes,%dU)^0xffffffffUL)!=0x%08xUL)stop("Prior canonical Setup metadata differs.",path);
  default_setup(%dU);ready_setup=1;
 }'''%(size,size,size,size,crc,size))
    write(native/'XRPREP.C',source[:a]+'\n'.join(clauses)+'\n'+source[b:])
    source=(native/'CPSET.C').read_text()
    source=once(source,'(on!=49989U||current_metadata_crc()!=0x3fc825efUL))',
                '(on!=49989U||current_metadata_crc()!=0x3fc825efUL)&&\n    (on!=%dU||current_metadata_crc()!=0x%08xUL))'%(len(new),zlib.crc32(new)))
    a=source.index('  marker_text(previous,49840U);',source.index('if(exists(readyfile))'))
    b=source.index('  fd=open(readyfile',a)
    prior_marker=source[a:b]
    source=source[:a]+'''  if(size==%dU&&on==%dU){
  marker_text(previous,49840U);
  if(n!=strlen(previous)||memcmp(names,previous,n)){
   marker_text(previous,49848U);
   if(n!=strlen(previous)||memcmp(names,previous,n)){
    marker_text(previous,49989U);
    if(n!=strlen(previous)||memcmp(names,previous,n))die("Foreign/stale Computer completion marker.");
   }
  }
'''%(len(new),len(new))+'  }else{\n'+prior_marker+'  }\n'+source[b:]
    write(native/'CPSET.C',source)
    source=(native/'FIXXT.C').read_text()
    for declaration,extra in [('static const char *names[]',','.join('"'+n+'"' for n in MODES)),('static unsigned long sizes[]',','.join(str(len(body[n]))+'UL' for n in MODES)),('static int target[]','1,1,1,1')]:
        m=re.search(re.escape(declaration)+r'=\{(.*?)\};',source);assert m
        source=source[:m.end(1)]+','+extra+source[m.end(1):]
    source=re.sub(r'(#define COUNT )(\d+)',lambda m:m[1]+str(int(m[2])+4),source)
    source=re.sub(r'#define FIXED_BYTES \d+UL','#define FIXED_BYTES %dUL'%len(body['TANDY88.DRV']),source)
    source=re.sub(r'#define FIXED_CRC 0x[0-9a-f]+UL','#define FIXED_CRC 0x%08xUL'%zlib.crc32(body['TANDY88.DRV']),source)
    # No new forced modes: KEEP_DISPLAY leaves the live display and its settings intact.
    # Install optional system files without classifying them as skipped profile resources.
    gate=''.join('   if(!stricmp(names[i],"%s")&&!pinned_file(p,%dUL,0x%08xUL))stop("Optional fixed source identity differs",p);\n'%(n,len(body[n]),zlib.crc32(body[n])) for n in MODES)
    source=once(source,'   if(!stricmp(names[i],"TANDY88.DRV")',gate+'   if(!stricmp(names[i],"TANDY88.DRV")')
    anchor='!stricmp(leaf,"TANDY88.DRV"))'
    source=once(source,anchor,'!stricmp(leaf,"TANDY88.DRV")'+''.join('||!stricmp(leaf,"'+n+'")' for n in MODES)+')')
    write(native/'FIXXT.C',source)
    for n,b in body.items():(out/'expanded/WINXT'/n).write_bytes(b)
    finisher_sizes(native,body,new)
    counts=F.aliases(native,{'WINXT/'+n:b for n,b in body.items()},new)
    print('STAGED NOT QUALIFIED; metadata bytes',len(new),'CRC',hex(zlib.crc32(new)),'FRESH/UPDATE',counts)
    print('Build CPSET, bind CPSET; build FIXXT, bind FIXXT; build SETUP. Final combined native tests required.')

def bind(out,component,stock):
    assert component in ('CPSET','FIXXT')
    native=out/'native';name=component+'.EXE';data=(native/name).read_bytes();assert data[:2]==b'MZ'
    (out/'expanded/WINXT'/name).write_bytes(data)
    F.aliases_existing(native,name,data)
    metadata=F.setup_bytes((native/'SETFILES.H').read_text(),stock.read_bytes())
    finisher_sizes(native,{name:data},metadata)

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('phase',choices=('stage','bind'));a.add_argument('--out',type=Path,required=True);a.add_argument('--stock',type=Path,required=True)
    for n in ('candidate','drivers','transformer'):a.add_argument('--'+n,type=Path,default=HERE/'ADDMODES.PY' if n=='transformer' else None)
    a.add_argument('--component',choices=('CPSET','FIXXT'));v=a.parse_args()
    if v.phase=='stage':stage(v.candidate,v.drivers,v.transformer,v.stock,v.out)
    else:bind(v.out,v.component,v.stock)
