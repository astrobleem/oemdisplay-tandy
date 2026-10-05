#!/usr/bin/env python3
"""Standard-library source, format, corruption, and seed-content tests."""
import argparse
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import random
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('dbbuild', str(ROOT / 'tools' / 'DBBUILD.PY'))
spec = importlib.util.spec_from_loader(loader.name, loader)
db = importlib.util.module_from_spec(spec)
loader.exec_module(db)
RESULTS = []

def test(name, callback):
    started = time.monotonic()
    try:
        detail = callback()
        RESULTS.append({'name': name, 'status': 'passed', 'seconds': round(time.monotonic()-started, 4), 'detail': detail})
    except Exception as exc:
        RESULTS.append({'name': name, 'status': 'FAILED', 'error': repr(exc)})

def expect_error(callback):
    try:
        callback()
    except (db.DatabaseError, json.JSONDecodeError):
        return
    raise AssertionError('Invalid input was accepted')

def fixture(nc=3, nq=9):
    qs = [{'id': 'q_' + str(q), 'text': 'Test question ' + str(q) + '?'} for q in range(nq)]
    return {'format_version':1, 'questions':qs,
            'characters':[{'id':'c_' + str(c), 'name':'Test character ' + str(c),
                           'answers':{q['id']:(c*7+i*3)%5 for i,q in enumerate(qs)}} for c in range(nc)]}

def repaired(blob):
    struct.pack_into('<I',blob,44,sum(blob[64:])&0xffffffff)
    return bytes(blob)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=ROOT/'data'/'STARTER.JSON')
    ap.add_argument('--binary',type=Path,default=ROOT/'build'/'TANDY.DAT')
    ap.add_argument('--report',type=Path,default=ROOT/'build'/'DBTEST.JSON')
    args=ap.parse_args()
    source=db.load_source(args.source)
    blob=args.binary.read_bytes()
    parsed=db.validate_binary(blob)
    test('canonical binary matches editable source',lambda: _assert(blob==db.compile_source(source),'Rebuild mismatch'))
    test('128 by 128 starter dimensions',lambda: _assert((parsed['nchars'],parsed['nquestions'])==(128,128),'Wrong starter dimensions'))
    test('answer codes and known bit vector',lambda: _assert(db.pack_values([0,1,2,3,4])==bytes([0x88,0x46]),'Incorrect little-bit packing'))
    def roundtrip():
        sizes=[(1,1),(1,256),(256,1),(3,7),(7,3),(7,8),(8,9),(9,8),(127,129),(128,128),(129,127),(255,256),(256,255),(256,256)]
        for nc,nq in sizes:
            f=fixture(nc,nq)
            got=db.validate_binary(db.compile_source(f))
            assert got['rows']==[[c['answers'][q['id']] for q in f['questions']] for c in f['characters']]
        return {'rectangular_and_boundary_fixtures':len(sizes),'max_dimensions':[256,256]}
    test('row and column bit boundaries',roundtrip)
    def random_pack():
        rng=random.Random(0x8088)
        for count in range(1,257):
            for _ in range(4):
                values=[rng.randrange(5) for _ in range(count)]
                assert db.unpack_values(db.pack_values(values),count)==values
        return {'deterministic_vectors':1024}
    test('random all-code packing round trips',random_pack)
    mutations={
      'duplicate character ids':lambda s:s['characters'][1].update(id=s['characters'][0]['id']),
      'duplicate question ids':lambda s:s['questions'][1].update(id=s['questions'][0]['id']),
      'duplicate names':lambda s:s['characters'][1].update(name=s['characters'][0]['name']),
      'duplicate question text':lambda s:s['questions'][1].update(text=s['questions'][0]['text']),
      'missing answer target':lambda s:s['characters'][0]['answers'].pop('q_0'),
      'unknown answer target':lambda s:s['characters'][0]['answers'].update(absent_question=4),
      'negative answer':lambda s:s['characters'][0]['answers'].update(q_0=-1),
      'answer five':lambda s:s['characters'][0]['answers'].update(q_0=5),
      'boolean answer':lambda s:s['characters'][0]['answers'].update(q_0=True),
      'string answer':lambda s:s['characters'][0]['answers'].update(q_0='YES'),
      'float answer':lambda s:s['characters'][0]['answers'].update(q_0=4.0),
      'long name':lambda s:s['characters'][0].update(name='A'*40),
      'long question':lambda s:s['questions'][0].update(text='A'*80),
      'unbreakable question word':lambda s:s['questions'][0].update(text='A'*27),
      'unbreakable name word':lambda s:s['characters'][0].update(name='A'*27),
      'question exceeds UI lines':lambda s:s['questions'][0].update(text=' '.join(['A'*13]*5)),
      'nonASCII name':lambda s:s['characters'][0].update(name='Ren\u00e9'),
      'nonASCII question':lambda s:s['questions'][0].update(text='Qu\u00e9?'),
      'empty name':lambda s:s['characters'][0].update(name=''),
      'embedded NUL':lambda s:s['characters'][0].update(name='A\0B'),
      'newline question':lambda s:s['questions'][0].update(text='Two\nlines?'),
      'empty characters':lambda s:s.update(characters=[]),
      'empty questions':lambda s:s.update(questions=[]),
      'bad format version':lambda s:s.update(format_version=2),
      'boolean format version':lambda s:s.update(format_version=True),
      'nonobject answer map':lambda s:s['characters'][0].update(answers=[]),
      'invalid id syntax':lambda s:s['characters'][0].update(id='NOT DOS?'),
    }
    for name, mutate in mutations.items():
        def check(mutate=mutate):
            f=fixture(); mutate(f); expect_error(lambda:db.compile_source(f))
        test('reject source: '+name,check)
    test('reject duplicate JSON object keys',lambda:expect_error(lambda:json.loads('{"id":1,"id":2}',object_pairs_hook=db.unique_json)))
    test('reject more than 2000 characters',lambda:expect_error(lambda:db.compile_source(fixture(2001,3))))
    test('reject more than 256 questions',lambda:expect_error(lambda:db.compile_source(fixture(3,257))))
    def max_strings():
        f=fixture(1,1);f['questions'][0]['text']='Q'*25+' '+'R'*26+' '+'S'*26;f['characters'][0]['name']='N'*19+' '+'M'*19
        got=db.validate_binary(db.compile_source(f))
        assert len(got['names'][0])==39 and len(got['questions'][0])==79
    test('accept exact maximum string lengths',max_strings)
    def duplicate_profile():
        f=fixture(2,9); f['characters'][1]['answers']=copy.deepcopy(f['characters'][0]['answers'])
        r=db.report_for(f,db.compile_source(f))
        assert r['duplicate_profiles']==[['c_0','c_1']]
    test('report identical profiles honestly',duplicate_profile)
    test('starter has no identical profiles',lambda:_assert(not db.report_for(source,blob)['duplicate_profiles'],'Duplicate profile'))
    test('starter has no constant questions',lambda:_assert(not db.report_for(source,blob)['constant_questions'],'Constant question'))
    def header():
        for offset in range(64):
            b=bytearray(blob);b[offset]^=0x80
            expect_error(lambda:db.validate_binary(bytes(b)))
        return {'header_bytes_mutated':64}
    test('reject every single-byte header mutation',header)
    def all_bytes():
        for offset in range(64,len(blob)):
            b=bytearray(blob); b[offset]^=0x80
            expect_error(lambda:db.validate_binary(bytes(b)))
        return {'payload_bytes_mutated':len(blob)-64}
    test('reject every single-byte payload mutation',all_bytes)
    def truncate():
        offsets=sorted(set([0,1,7,8,19,20,44,48,63,64,len(blob)-1]+[parsed[k] for k in ('nameoffset','rowoffset','coloffset','stringsoffset')]))
        for offset in offsets:expect_error(lambda:db.validate_binary(blob[:offset]))
        return {'truncations':len(offsets)}
    test('reject truncated sections',truncate)
    test('reject appended bytes',lambda:expect_error(lambda:db.validate_binary(blob+b'\0')))
    def corrupt_field(offset,value):
        b=bytearray(blob);struct.pack_into('<I',b,offset,value);expect_error(lambda:db.validate_binary(repaired(b)))
    test('reject invalid question string pointer',lambda:corrupt_field(parsed['qoffset'],0))
    test('reject invalid name string pointer',lambda:corrupt_field(parsed['nameoffset'],0xffffffff))
    def unterminated():
        b=bytearray(blob);p=struct.unpack_from('<I',b,parsed['qoffset'])[0];b[p:p+80]=b'X'*80
        expect_error(lambda:db.validate_binary(repaired(b)))
    test('reject unterminated long string with repaired checksum',unterminated)
    def nonascii():
        b=bytearray(blob);b[parsed['stringsoffset']]=255
        expect_error(lambda:db.validate_binary(repaired(b)))
    test('reject nonASCII binary string with repaired checksum',nonascii)
    def bad_value():
        b=bytearray(blob);b[parsed['rowoffset']]=(b[parsed['rowoffset']]&0xf8)|7
        expect_error(lambda:db.validate_binary(repaired(b)))
    test('reject packed answer seven with repaired checksum',bad_value)
    def mismatch():
        b=bytearray(blob);off=parsed['coloffset'];b[off]=(b[off]&0xf8)|((b[off]+1)%5)
        expect_error(lambda:db.validate_binary(repaired(b)))
    test('reject row column disagreement with repaired checksum',mismatch)
    def padding():
        b=bytearray(db.compile_source(fixture(2,2)))
        row=struct.unpack_from('<I',b,28)[0];b[row]|=0x80
        expect_error(lambda:db.validate_binary(repaired(b)))
    test('reject nonzero padding with repaired checksum',padding)
    def facts():
        chars={c['id']:c['answers'] for c in source['characters']}
        checks=[('mario','red',4),('luigi','green',4),('princess_peach','royal',4),('bowser','villain',4),
                ('link','sword',4),('sonic_the_hedgehog','speed',4),('pac_man','yellow',4),
                ('mega_man','robot',4),('batman','human',4),('superman','alien',4),
                ('darth_vader','human',4),('luke_skywalker','sibling',4),('princess_leia','sibling',4),
                ('yoda','human',0),('colonel_sanders','real',4),('colonel_sanders','food',4),
                ('abraham_lincoln','moustache',0),('albert_einstein','scientist',4),('michael_jackson','dance',4)]
        for c,q,v in checks:assert chars[c][q]==v,(c,q)
        return {'canonical_fact_regressions':len(checks)}
    test('representative canonical trait regressions',facts)
    def no_tricks():
        names=[c['name'].lower() for c in source['characters']]
        for q in source['questions']:
            text=q['text'].lower()
            assert not any(word in text for word in ('alphabet','first letter','last letter','name starts','name ends'))
            assert not any(name in text for name in names if len(name)>4)
        return {'broad_questions_checked':128}
    test('questions avoid identity and alphabet tricks',no_tricks)
    def maximum_scale():
        rng=random.Random(0x808830)
        f=fixture(2000,256)
        for char in f['characters']:
            char['name']='Synthetic test '+char['id'][2:].zfill(4)
            char['answers']={q['id']:rng.randrange(5) for q in f['questions']}
        b=db.compile_source(f)
        info=db.report_for(f,b)
        assert info['nchars']==2000 and info['nquestions']==256
        assert info['rowbytes']==96 and info['colbytes']==750
        assert not info['duplicate_profiles']
        scale_path=ROOT/'build'/'SCALE.DAT'
        scale_path.write_bytes(b)
        db.validate_binary(scale_path.read_bytes())
        scale_report=dict(info, purpose='Synthetic structural/memory fixture only; not a playable knowledge roster.',
                          generator='DBTEST.PY maximum_scale; PRNG seed 0x808830',
                          sha256=hashlib.sha256(b).hexdigest())
        (ROOT/'build'/'SCALE.JSON').write_text(json.dumps(scale_report,indent=2)+'\n',encoding='ascii')
        return scale_report
    test('maximum 2000 by 256 synthetic structural fixture',maximum_scale)
    failures=[r for r in RESULTS if r['status']!='passed']
    report={'suite':'TANDINATOR compiler and database tests','python':sys.version.split()[0],
            'status':'FAILED' if failures else 'passed','tests':len(RESULTS),'passed':len(RESULTS)-len(failures),
            'failed':len(failures),'binary_sha256':hashlib.sha256(blob).hexdigest(),
            'database_report':db.report_for(source,blob),'results':RESULTS}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='ascii')
    print(json.dumps({k:v for k,v in report.items() if k not in ('results','database_report')},indent=2))
    for failure in failures:print(failure)
    return bool(failures)

def _assert(condition,message):
    assert condition,message

if __name__=='__main__':
    sys.exit(main())
