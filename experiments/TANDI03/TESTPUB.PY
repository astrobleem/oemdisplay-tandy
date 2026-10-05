#!/usr/bin/env python3
"""Read-only artifact, fallback and headline-accounting checks; no install."""
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parent
EXES={'TANDI03/RUN/TANDI.EXE','TANDI03/BASE128/TANDI.EXE',
      'TANDI03/SOURCE/build/BASE128.EXE'}
UNCHANGED={
 'SOURCE/data/BASE128.JSON':'06d8bce4c3aab93f9271f566f42b5fdcbcc51afcfc374ae86715597996c9cf4d',
 'SOURCE/src/ENGINE.C':'970f9ff2c1750f71aa392d36e801067a1aca7709fbc64837dfaee4fa86ed4b99',
 'SOURCE/src/DB.C':'e3f078fc5d9534b78b30e102390da98324dce345ec2a3261393a1ae0ebf4a788',
 'SOURCE/src/ART.H':'be14f7ca4c2963c8feae8332e6ec286845a94af9873fb4f731e3bed4ee72c07f',
 'SOURCE/art/CABINET.PNG':'960fb2033e3aeaa7c0d550e228e8fcf69cdad6dace8a13571a9b5f068bf5251b',
 'SOURCE/art/PARTS.PNG':'6ae9d955e6feaf6bd0585e82fd7ed5cda6b743b929913fede5ac0cb951ebbcb1',
}

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 pins=json.loads((ROOT/'SHA256.JSN').read_text())
 data=(ROOT/'TANDI03.ZIP').read_bytes();pin=pins.pop('TANDI03.ZIP')
 assert len(data)==pin['bytes'] and sha(data)==pin['sha256']
 with zipfile.ZipFile(ROOT/'TANDI03.ZIP') as z:
  names=z.namelist();assert len(names)==len(set(names))==247
  assert z.testzip() is None;found=set()
  for n in names:
   p=PurePosixPath(n);data=z.read(n)
   assert n.startswith('TANDI03/') and not p.is_absolute() and '..' not in p.parts
   assert not any(x.lower() in {'windows','guest','ddk','include','lib','.git','library-helpers'} for x in p.parts)
   assert p.suffix.lower() not in {'.drv','.dll','.com','.sys','.fon','.obj','.lib','.zip'}
   assert data[:4]!=b'\x7fELF'
   if data[:2]==b'MZ' or p.suffix.lower()=='.exe':found.add(n)
  assert found==EXES
  rows=z.read('TANDI03/SHA256.TXT').decode().splitlines();assert len(rows)==246
  for row in rows:
   expected,n=row.split(None,1);assert sha(z.read('TANDI03/'+n.strip()))==expected,n
  for n,pin in pins.items():
   data=z.read('TANDI03/'+n);assert len(data)==pin['bytes'] and sha(data)==pin['sha256'],n
  for n,expected in UNCHANGED.items():assert sha(z.read('TANDI03/'+n))==expected,n
  assert z.read('TANDI03/BASE128/TANDI.EXE')==z.read('TANDI03/SOURCE/build/BASE128.EXE')
  for local,inside in [('QA.TXT','QA.TXT'),('CHANGES.TXT','CHANGES.TXT'),
                       ('NOTICE.TXT','NOTICE.TXT'),('ROSTER.TXT','ROSTER.TXT'),
                       ('FALLBACK.TXT','BASE128/README.TXT'),
                       ('PREVIEW.PNG','EVIDENCE/320x200x16/GUESS.PNG'),
                       ('EVIDENCE/REVIEW.JSON','EVIDENCE/REVIEW.JSON'),
                       ('EVIDENCE/HUMANSIM.JSON','EVIDENCE/HUMANSIM.JSON'),
                       ('EVIDENCE/ROSTERAUDIT.JSON','EVIDENCE/ROSTERAUDIT.JSON'),
                       ('EVIDENCE/COVERAGE.JSON','SOURCE/data/COVERAGE.JSON')]:
   assert (ROOT/local).read_bytes()==z.read('TANDI03/'+inside),local
 coverage=json.loads((ROOT/'EVIDENCE/COVERAGE.JSON').read_text())
 tiers=coverage['cohorts']['all']['tiers']
 assert coverage['cohorts']['all']['cells']==33280 and sum(tiers.values())==33280
 assert tiers['unknown']==13115
 assert tiers['legacy_general_unverified']+tiers['curated_general_unverified']==18926
 assert coverage['cohorts']['added']['tiers']['unknown']==12839
 audit=json.loads((ROOT/'EVIDENCE/ROSTERAUDIT.JSON').read_text())
 assert audit['characters']==256 and audit['questions']==130
 assert len(audit['zero_opposing_pairs'])==200 and not audit['identical_profiles']
 report=json.loads((ROOT/'EVIDENCE/HUMANSIM.JSON').read_text())['runs']
 for name,first,eventual,total in [('matrix_exact',235,256,256),
       ('uncertain_soft',2696,3061,3072),('mixed_noise',2095,2881,3072),
       ('single_flip_each_early_position',1722,2534,2560)]:
  r=report[name]['all']
  assert (r['first_guess_success'],r['success'],r['cases'])==(first,eventual,total)
 assert report['matrix_exact']['original']['first_guess_success']==128
 sparse=report['independent_sparse_answers']['results']
 assert len(sparse)==19 and all(r['cohort']=='original' for r in sparse)
 print('PASS: 247 entries, 246 internal hashes, runtime/fallback/art pins, public evidence identities and disclosed dataset/simulation counts')

if __name__=='__main__':main()
