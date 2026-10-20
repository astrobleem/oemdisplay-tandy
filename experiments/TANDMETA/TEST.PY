#!/usr/bin/env python3
"""Tests run offline. HTTP mock is transport coverage, not model evidence."""
import copy
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest

loader=importlib.machinery.SourceFileLoader('curate',str(Path(__file__).with_name('CURATE.PY')))
spec=importlib.util.spec_from_loader(loader.name,loader)
m=importlib.util.module_from_spec(spec)
loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        self.base=m.read(m.BASE)
        self.original=copy.deepcopy(self.base)
        self.batch=m.package(self.base,m.simulate(),'simulation')
        self.review={'batch_sha256':m.digest(self.batch),'reviewer':'TEST FIXTURE, not real curation',
                     'decisions':{e['id']:{'decision':'approve','evidence':'Synthetic test approval only.'} for e in self.batch['entries']}}

    def test_roundtrip_and_original_unchanged(self):
        candidate,blob,report=m.build(self.base,self.batch,self.review)
        info=m.db.validate_binary(blob)
        self.assertEqual((info['nchars'],info['nquestions']),(128,129))
        self.assertEqual(self.base,self.original)
        self.assertEqual(report['mode'],'simulation')
        self.assertEqual(report['unmodeled_characters_per_new_question'],124)
        for c in candidate['characters']:
            self.assertEqual({k:v for k,v in c['answers'].items() if k!='wears_cap'},
                             next(x for x in self.base['characters'] if x['id']==c['id'])['answers'])
            if c['id'] not in m.SAMPLE:self.assertEqual(c['answers']['wears_cap'],2)

    def test_pending_blocked(self):
        for v in self.review['decisions'].values():v['decision']='pending'
        with self.assertRaises(ValueError):m.build(self.base,self.batch,self.review)

    def test_no_evidence_blocked(self):
        for v in self.review['decisions'].values():v['evidence']=''
        with self.assertRaises(ValueError):m.build(self.base,self.batch,self.review)

    def test_no_reviewer_blocked(self):
        self.review['reviewer']=' '
        with self.assertRaises(ValueError):m.build(self.base,self.batch,self.review)

    def test_stale_review_blocked(self):
        self.batch['model']='changed'
        with self.assertRaises(ValueError):m.build(self.base,self.batch,self.review)

    def test_stale_base_blocked(self):
        self.base['title']='changed'
        with self.assertRaises(ValueError):m.build(self.base,self.batch,self.review)

    def test_changed_entry_blocked(self):
        self.batch['entries'][0]['proposal']['text']='Changed?'
        self.review['batch_sha256']=m.digest(self.batch)
        with self.assertRaises(ValueError):m.build(self.base,self.batch,self.review)

    def test_reject_all_no_database(self):
        for v in self.review['decisions'].values():v['decision']='reject'
        with self.assertRaises(ValueError):m.build(self.base,self.batch,self.review)

    def test_structural_rejections(self):
        for field,value in [('text','x'*80),('text','Caf\u00e9?'),('id','real'),('id','BAD')]:
            with self.subTest(field=field,value=value):
                result=m.simulate();result['questions'][0][field]=value
                with self.assertRaises(ValueError):m.validate(self.base,result)
        for code in [True,5,-1,'4',None]:
            result=m.simulate();result['questions'][0]['answers']['mario']=code
            with self.assertRaises(ValueError):m.validate(self.base,result)

    def test_missing_unknown_duplicate_targets(self):
        result=m.simulate();del result['questions'][0]['answers']['mario']
        with self.assertRaises(ValueError):m.validate(self.base,result)
        result=m.simulate();result['questions'][0]['answers']['unknown']=2
        with self.assertRaises(ValueError):m.validate(self.base,result)
        result=m.simulate();result['questions'].append(copy.deepcopy(result['questions'][0]))
        with self.assertRaises(ValueError):m.validate(self.base,result)

    def test_finding_requires_separate_review(self):
        result=m.simulate()
        old=self.base['characters'][0]['answers']['real']
        result['findings']=[{'character_id':'mario','question_id':'real','proposed_answer':4-old,
                             'reason':'Deliberately FALSE audit suggestion for rejection test.'}]
        batch=m.package(self.base,result,'simulation')
        review={'batch_sha256':m.digest(batch),'reviewer':'TEST','decisions':{
            e['id']:{'decision':'approve' if e['kind']=='question' else 'reject',
                     'evidence':'Synthetic decision; Mario is fictional.'} for e in batch['entries']}}
        candidate,_,_=m.build(self.base,batch,review)
        self.assertEqual(candidate['characters'][0]['answers']['real'],old)

    def test_finding_invalid_and_duplicate(self):
        result=m.simulate()
        f={'character_id':'mario','question_id':'real','proposed_answer':True,'reason':'Test'}
        result['findings']=[f]
        with self.assertRaises(ValueError):m.validate(self.base,result)
        f['proposed_answer']=4
        result['findings']=[f,copy.deepcopy(f)]
        with self.assertRaises(ValueError):m.validate(self.base,result)

    def test_no_nonmeta_model(self):
        with self.assertRaises(ValueError):m.local_call('qwen:latest','test')
        with self.assertRaises(ValueError):m.local_call('llama3.2:3b-cloud','test')

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):json.loads('{"a":1,"a":2}',object_pairs_hook=m.db.unique_json)

    def test_mock_http_transport(self):
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.assertEqual(self.path,'/api/chat')
                owner.assertEqual(request['model'],'llama3.2:3b')
                owner.assertFalse(request['stream'])
                self.send_response(200);self.end_headers()
                self.wfile.write(json.dumps({'model':'llama3.2:3b','done':True,
                    'message':{'content':json.dumps(m.simulate())}}).encode())
        server=HTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            result,raw=m.local_call('llama3.2:3b',m.prompt(self.base),server.server_port)
            self.assertEqual(result,m.simulate());self.assertTrue(raw['done'])
        finally:
            server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main(verbosity=2)
