"""Assemble the one current release from qualified ZIPs and preserved inputs.

No network, compiler, installer or emulator is used. The main producer keeps
its native qualification gate; this assembler cannot override it.
"""
import argparse,hashlib,importlib.machinery,io,json,re,struct,tempfile,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def identity(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def text(data):return data.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')
def exact(path,pin):
 data=path.read_bytes()
 if identity(data)!=pin:raise ValueError('Qualified input differs: '+str(path))
 return data
def spec():return json.loads((HERE/'PRODUCTS.JSN').read_bytes())

def verify_alternatives(files):
 # Verify the new fresh packet separately, then let the unchanged historical
 # gate verify its own compact base. Never substitute into the output mapping.
 native=importlib.machinery.SourceFileLoader('current_fresh_legacy_gate',str(ROOT/'tools/HPDIB/PUBLISH.PY')).load_module()
 base=exact(ROOT/'downloads/COMPACT/CGA.ZIP',{'bytes':297312,'sha256':'84a1992803d1bd022318ddb001490b66494aba1e61ca09eef2fbc445fb469cc4'})
 fresh=importlib.machinery.SourceFileLoader('current_fresh_cga_gate',str(ROOT/'tools/CGAFRESH/VERIFY.PY')).load_module()
 fresh.verify(files['CGA.ZIP'])
 qualified=dict(files);qualified['CGA.ZIP']=base
 native.verify_alternatives(qualified)
 return {n:identity(files[n]) for n in ('CGA.ZIP','CPPAN.ZIP','JRPAN.ZIP','PAN.ZIP')}
def archive(files):
 stream=io.BytesIO()
 with zipfile.ZipFile(stream,'w',zipfile.ZIP_STORED) as z:
  for name,data in sorted(files.items()):
   info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=0;info.external_attr=0x20
   z.writestr(info,data)
 return stream.getvalue()
def zip_files(data):
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  names=z.namelist()
  if len(names)!=len(set(names)) or z.testzip():raise ValueError('Duplicate or corrupt ZIP members')
  return {n:z.read(n) for n in names if not n.endswith('/')}
def input_archive(config):
 files={n:exact(HERE/'INPUTS'/n,pin) for n,pin in config['developer_inputs'].items()}
 files['INPUTS.JSN']=text(json.dumps(config['developer_inputs'],indent=2)+'\n')
 files['README.TXT']=text('DEVELOPER BUILD INPUTS\n\nThese original public app/driver archives are retained for source reproduction.\nThey are not consumer installation prerequisites. Current installations use\nthe product ZIPs and expanded files linked from the main README.\n\nT2INPUT.ZIP is the accepted Video II packet read by src/tga2/T2PACK.PY.\nMML3AUTH.ZIP and PITEXPR.ZIP are the immutable original sound-app inputs\nread by the sound PITPACK/recut builder. Their current consumer packets\nare separate qualified products; use the original names here for rebuilding.\n')
 return archive(files)
def ancillary(sound,main_zip):
 config=spec();files={n:exact(ROOT/row['source'],row['identity']) for n,row in config['local'].items()}
 for name,row in config.get('documentation_overlays',{}).items():
  original=zip_files(files[name]);updated=dict(original)
  guide=(ROOT/row['source']).read_bytes()
  if row['member']!='INSTALL.TXT' or row['member'] not in original:raise ValueError('Unexpected documentation overlay')
  if b'\n' in guide.replace(b'\r\n',b''):raise ValueError('Guide must retain CRLF')
  updated[row['member']]=guide
  if {n:b for n,b in updated.items() if n!=row['member']}!={n:b for n,b in original.items() if n!=row['member']}:raise ValueError('Documentation refresh changed runtime')
  files[name]=archive(updated)
 for name,row in config['sound'].items():files[name]=exact(sound/name,row['identity'])
 verify_alternatives(files)
 files['BUILDIN.ZIP']=input_archive(config)
 files['TANDYLAB.ZIP']=collection(config,main_zip)
 for name,data in files.items():
  if not name.endswith('.ZIP'):raise ValueError('Consumer alternatives must be ZIPs: '+name)
  zip_files(data)
 if set(files)&set(config['excluded_consumer_alternatives']):raise ValueError('Obsolete raw installer alternative included')
 return files
def collection(config,main_zip):
 original=zip_files(exact(ROOT/config['collection']['source'],config['collection']['identity']))
 files={n:b for n,b in original.items() if not n.startswith('TANDYLAB/DRIVERS/') and n not in ['TANDYLAB/README.TXT','TANDYLAB/CHECK.TXT','TANDYLAB/MANIFEST.SHA']}
 # The exact already-qualified movable source, including every OEM INF reference
 # and its unchanged launch guards. No toolkit staging or nested ZIP is retained.
 main=main_product(main_zip)
 files.update({'TANDYLAB/DRIVERS/'+n:b for n,b in main.items() if n.startswith('WINXT/')})
 files['TANDYLAB/README.TXT']=(HERE/'GUIDES/TANDYLAB.TXT').read_bytes()
 files['TANDYLAB/CHECK.TXT']=(HERE/'GUIDES/TANDYLAB.TXT').read_bytes()
 catalog=original['TANDYLAB/CATALOG.TXT'].decode('ascii')
 marker='DISPLAY TOOLKIT (OPTIONAL, MODERN PC PREPARATION ONLY)'
 if catalog.count(marker)!=1:raise ValueError('TANDYLAB driver catalog section changed')
 files['TANDYLAB/CATALOG.TXT']=text(catalog[:catalog.index(marker)]+'OPTIONAL WINDOWS XT DISPLAY SOURCE\n  Change to DRIVERS\\WINXT in plain DOS and run DISPLAY. Select that same\n  full path in Windows Setup, choose HPXY and complete changes. For each\n  launch change to that folder and run DISPWIN. Both entries reserve video\n  memory automatically. Fonts, grabber and logos are included; read DISPLAY.TXT.\n')
 files['TANDYLAB/DRIVERS/README.TXT']=text('WINDOWS XT DISPLAY SOURCE\n\nChange to DRIVERS\\WINXT in DOS and read DISPLAY.TXT. Run DISPLAY for\nWindows Setup and DISPWIN for each launch; reservation is automatic.\nUse installed Windows 3.0 real mode on an original EX/HX with normal 640 KB.\nThe folder includes all driver fonts, grabber, logos and helpers.\n')
 files['TANDYLAB/MANIFEST.SHA']=text(''.join(identity(b)['sha256']+'  '+n[len('TANDYLAB/'):]+'\n' for n,b in sorted(files.items())))
 return archive(files)

def main_product(data):
 files=zip_files(data)
 if set(n.split('/')[0] for n in files)!={'SETUP.EXE','README.TXT','WINXT'}:raise ValueError('Expected SETUP.EXE, README.TXT and one WINXT folder')
 setup=files['SETUP.EXE']
 if setup[:2]!=b'MZ' or len(setup)<28:raise ValueError('Missing native SETUP image')
 last,pages=struct.unpack_from('<HH',setup,2)
 if pages*512-(512-last if last else 0)!=len(setup):raise ValueError('SETUP contains an appended archive')
 if any(n.upper().endswith(('.ZIP','.PY')) for n in files):raise ValueError('Nested archive or host preparation in product')
 descriptor=files['WINXT/OEMSETUP.INF']
 if b'a = .,' not in descriptor or b'C:\\WINXT' in descriptor:raise ValueError('Ordinary OEM source is not movable')
 for name in re.findall(rb'a:([A-Z0-9]+\.[A-Z0-9]+)',descriptor):
  if 'WINXT/'+name.decode('ascii') not in files:raise ValueError('OEM support missing: '+name.decode('ascii'))
 native=json.loads((ROOT/'tools/XROEM/NATIVE.JSN').read_bytes())
 if native['packet']!=identity(data):
  core=importlib.machinery.SourceFileLoader('current_panui_gate',str(ROOT/'tools/HPDIB/PUBLISH.PY')).load_module()
  core.verify_core(data)
  return files
 if native['complete'] is not True or native['packet']!=identity(data) or not all(native['checks'].values()):raise ValueError('Exact ordinary OEM qualification missing')
 for name,pin in native['sources'].items():
  if identity(files['WINXT/'+name])!=pin:raise ValueError('Ordinary OEM source changed: '+name)
 return files
def build(output,sound,core_input,commit):
 if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Full source commit required')
 config=spec()
 core=importlib.machinery.SourceFileLoader('current_native_producer',str(ROOT/'tools/HPDIB/PUBLISH.PY')).load_module()
 if set(core.ASSETS)!=set(config['core_assets']):raise ValueError('Expanded native producer is not installed in this source snapshot')
 supplied={n:exact(core_input/n,config['core_identities'][n]) for n in config['core_assets']}
 producer_commit=json.loads(supplied['WINXT.JSN'])['source_commit']
 if producer_commit!=config['core_source_commit']:raise ValueError('Core producer commit differs from live qualified core')
 # The producer refuses output until exact full FRESH/UPDATE/negative records
 # are complete. Never substitute a caller-supplied SFX or bypass that gate.
 with tempfile.TemporaryDirectory(prefix='winxt-current-') as tmp:
  folder=Path(tmp)/'core';core.build(folder,producer_commit)
  files={n:(folder/n).read_bytes() for n in config['core_assets']}
  if files!=supplied:raise ValueError('Supplied core artifacts differ from the native-gated producer')
 main_product(files['WINXT.ZIP'])
 files.update(ancillary(sound,files['WINXT.ZIP']))
 record={'schema':1,'repository':config['repository'],'tag':config['tag'],'title':config['title'],
         'source_commit':commit,'core_source_commit':producer_commit,'primary_download':'WINXT.ZIP',
         'main_layout':['SETUP.EXE','README.TXT','WINXT/'],
         'install_paths':{'full':'SETUP.EXE','drivers':'Windows Setup / Other / expanded WINXT folder'},
         'developer_assets':config['developer_assets'],
         'qualified_source_assets':config['local'],
         'documentation_overlays':config.get('documentation_overlays',{}),
         'assets':{n:identity(b) for n,b in sorted(files.items())}}
 files['CURRENT.JSN']=text(json.dumps(record,indent=2)+'\n')
 files['CURRENT.SHA']=text(''.join(identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items())))
 output.mkdir(parents=True,exist_ok=False)
 for name,data in files.items():(output/name).write_bytes(data)
 print(json.dumps({'tag':config['tag'],'assets':{n:identity(b) for n,b in sorted(files.items())}},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--out',type=Path,required=True);p.add_argument('--sound',type=Path,required=True);p.add_argument('--core',type=Path,required=True);p.add_argument('--commit',required=True)
 a=p.parse_args();build(a.out,a.sound,a.core,a.commit)
