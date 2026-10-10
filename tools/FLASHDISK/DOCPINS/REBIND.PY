"""MIT: reproduce a documentation-only pin refresh of the measured PREPXT.

Native executable code, header, relocations, paths and non-document pins stay
byte-exact. Only three document hashes/sizes and MANIFEST.SHA may change.
This is host data binding, not a claim of a new native compilation or run.
"""
from pathlib import Path
import argparse,hashlib,json,re,struct
HERE=Path(__file__).resolve().parent
BASE_SHA='5817a16b619377307f8f503b379f0d2bfec7b455797ee24f56f4c767e4eb59e5'
ALLOWED={'MODEINFO.TXT','LOGOINFO.TXT','README.TXT','MANIFEST.SHA'}
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(p):return [(n,h,int(z),int(k)) for n,h,z,k in re.findall(r'\{"([^"\r\n]+)","([a-f0-9]{64})",(\d+)UL,([01])\}',p.read_text('ascii'))]
def bind(new_header):
    base=(HERE/'BASE.EXE').read_bytes();assert sha(base)==BASE_SHA
    old=rows(HERE/'BASEPINS.H');new=rows(new_header);assert len(old)==len(new)==59
    mapping=(HERE/'BASE.MAP').read_text('ascii')
    group=int(re.search(r'^ ([0-9A-F]+):0\s+DGROUP$',mapping,re.M)[1],16)*16
    start,end=[int(x,16) for x in re.search(r'^ ([0-9A-F]+)H ([0-9A-F]+)H [0-9A-F]+H _DATA\s+DATA$',mapping,re.M).groups()]
    header=struct.unpack_from('<H',base,8)[0]*16;ds=header+group;data_start=header+start;data_end=header+end+1
    def ztext(blob,p):return blob[p:blob.index(0,p)].decode('ascii')
    n,h,z,k=old[0];name_at=base.index(n.encode()+b'\0');hash_at=base.index(h.encode()+b'\0')
    first=struct.pack('<HHLH',name_at-ds,hash_at-ds,z,k);assert base.count(first)==1;table=base.index(first)
    out=bytearray(base);changes=[];allowed_offsets=set()
    for i,(before,after) in enumerate(zip(old,new)):
        n,h,z,k=before;nn,hh,zz,kk=after;assert (n,k)==(nn,kk)
        at=table+i*10;np,hp,size,kind=struct.unpack_from('<HHLH',base,at)
        assert (ztext(base,ds+np),ztext(base,ds+hp),size,kind)==before
        assert data_start<=at<at+10<=data_end and data_start<=ds+hp<ds+hp+65<=data_end
        if before!=after:
            assert n in ALLOWED,'Non-document pin changed: '+n
            out[ds+hp:ds+hp+64]=hh.encode('ascii');out[at+4:at+8]=struct.pack('<L',zz)
            allowed_offsets.update(range(ds+hp,ds+hp+64));allowed_offsets.update(range(at+4,at+8))
            changes.append({'name':n,'old_sha256':h,'new_sha256':hh,'old_size':z,'new_size':zz,'digest_offset':ds+hp,'size_offset':at+4})
    for i,expected in enumerate(new):
        np,hp,size,kind=struct.unpack_from('<HHLH',out,table+i*10)
        assert (ztext(out,ds+np),ztext(out,ds+hp),size,kind)==expected
    diffs=[i for i,(a,b) in enumerate(zip(base,out)) if a!=b]
    assert set(diffs)<=allowed_offsets and all(data_start<=i<data_end for i in diffs)
    assert out[:data_start]==base[:data_start] and out[data_end:]==base[data_end:]
    result={'binding_kind':'Host documentation data refresh of measured native implementation',
      'refreshed_binary_rerun_in_guest':False,'native_base_sha256':BASE_SHA,'helper_sha256':sha(out),
      'base_header_sha256':sha((HERE/'BASEPINS.H').read_bytes()),'updated_header_sha256':sha(new_header.read_bytes()),
      'all_59_binary_pin_rows_match_source':True,'only_document_data_changed':True,'changed_rows':changes,
      'changed_byte_count':len(diffs),'MZ_header_code_relocations_non_document_data_exact':True,
      'protected_prefix_sha256':sha(base[:data_start]),'protected_suffix_sha256':sha(base[data_end:]),
      'allowed_documents':sorted(ALLOWED),'code_contract':'No function, control flow, buffer, pathname or non-document resource pin changed.'}
    return bytes(out),result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--header',type=Path,default=HERE.parent/'XTPINS.H');p.add_argument('--out',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    b,r=bind(a.header);a.out.write_bytes(b);a.report.write_bytes((json.dumps(r,indent=2)+'\n').replace('\n','\r\n').encode('ascii'));print(json.dumps(r,indent=2))
