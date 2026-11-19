"""Offline, deterministic expansion from CC0 structured biography facts.
No missing property is interpreted as a negative factual assertion.
"""
import json,unicodedata,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s).lower() if c.isascii() and c.isalnum())
def ascii_name(s):return unicodedata.normalize('NFKD',s.replace('ø','o').replace('Ø','O')).encode('ascii','ignore').decode()
s=json.loads((P/'data/BASE256.JSON').read_text());bio=json.loads((P/'data/BIOGRAPHIES.JSON').read_text());labels=bio['labels'];records=bio['people']
extra=[]
def question(q,text):extra.append({'id':q,'text':text})
for year in [1600,1700,1750,1850,1900]:question('birth_before_'+str(year),'Was this real person born before '+str(year)+'?')
for year in [1800,1900,1950,2000]:question('death_before_'+str(year),'Did this real person die before '+str(year)+'?')
roles={
 'poetry':('write poetry',{'poet'}),
 'novels':('write novels',{'novelist'}),
 'plays':('write plays',{'playwright'}),
 'short_stories':('write short stories',{'short story writer'}),
 'philosophy':('work as a philosopher',{'philosopher'}),
 'economics':('work as an economist',{'economist'}),
 'history':('work as a historian',{'historian'}),
 'physics':('work as a physicist',{'physicist','theoretical physicist','experimental physicist'}),
 'chemistry':('work as a chemist',{'chemist'}),
 'mathematics':('work as a mathematician',{'mathematician'}),
 'astronomy':('work as an astronomer',{'astronomer'}),
 'biology':('work as a biologist',{'biologist','botanist','zoologist','microbiologist'}),
 'painting':('work as a painter',{'painter','portrait painter'}),
 'sculpture':('work as a sculptor',{'sculptor'}),
 'composition':('compose music',{'composer','classical composer','opera composer'}),
 'invention':('work as an inventor',{'inventor'}),
 'journalism':('work as a journalist',{'journalist'}),
 'film_directing':('direct films',{'film director'}),
}
for q,(verb,_) in roles.items():question('bio_'+q,'Is this real person well known for '+{'poetry':'poetry','novels':'novels','plays':'plays','short_stories':'short stories','philosophy':'philosophy','economics':'economics','history':'historical scholarship','physics':'physics','chemistry':'chemistry','mathematics':'mathematics','astronomy':'astronomy','biology':'biology','painting':'painting','sculpture':'sculpture','composition':'composing music','invention':'inventions','journalism':'journalism','film_directing':'directing films'}[q]+'?')
for lang in ['English','French','German','Russian','Italian','Spanish','Japanese','Portuguese']:
 question('language_'+lang.lower(),'Did this real person speak or write '+lang+'?')
question('nobel','Did this real person receive a Nobel Prize?')
for q in extra:
 for c in s['characters']:c['answers'][q['id']]=0 if c['answers']['real']==0 else 2
s['questions']+=extra
original_ids={norm(c['name']):c for c in s['characters']}
baseids={c['id'] for c in s['characters']}
# Real humans cannot have a fictional debut, species, magical powers or costume superhero origin.
nonfiction_no='fictional animal robot alien magical_being monster video_origin animation_origin live_origin comics_origin books_origin folklore old_fiction mid_fiction late_fiction new_fiction unusual_skin fur feathers tail big_ears strength flies magic speed transforms superhero fantasy future'.split()
def entity_ids(r,prop):return {v['id'] for v in r['facts'].get(prop,[]) if isinstance(v,dict) and 'id' in v}
def year(r,prop):
 vs=r['facts'].get(prop,[])
 if len(vs)!=1 or vs[0]['precision']<9:return None
 return int(vs[0]['time'].lstrip('+').split('-',1)[0]) if not vs[0]['time'].startswith('-') else -int(vs[0]['time'][1:].split('-',1)[0])
def dated_answer(r,prop,cutoff):
 values=r['facts'].get(prop,[])
 if not values or any(v['precision']<9 for v in values):return 2
 answers={int(v['time'].lstrip('+').split('-',1)[0])<cutoff if not v['time'].startswith('-') else True for v in values}
 return (4 if True in answers else 0) if len(answers)==1 else 2
def apply(r,c,added):
 a=c['answers'];jobs={labels.get(q,'') for q in entity_ids(r,'P106')};langs={labels.get(q,'') for q in entity_ids(r,'P1412')}
 born=year(r,'P569');died=year(r,'P570')
 if added:
  a.update({q:0 for q in nonfiction_no});a.update(real=4,human=4,young=0,athlete=0)
  sex=entity_ids(r,'P21')
  if sex=={'Q6581097'}:a.update(male=4,female=0)
  elif sex=={'Q6581072'}:a.update(male=0,female=4)
  # These are positive facts only; an absent occupation is UNKNOWN.
  if set(r['reviewed_fame'])&{'poetry','novels','plays','short_stories','painting','sculpture'}:a['artist']=4
  if jobs&{'physicist','theoretical physicist','chemist','mathematician','astronomer','biologist','botanist','zoologist','microbiologist','scientist'}:a['scientist']=4
  if 'inventor' in jobs:a['inventor']=4
  if 'composition' in r['reviewed_fame']:a['singer']=4
  if jobs&{'actor','stage actor','film actor','comedian'}:a['performer']=4
  if 'politician' in jobs:a['politician']=4
  if 'university teacher' in jobs or 'professor' in jobs:a['teacher']=4
  countries={labels.get(q,'') for q in entity_ids(r,'P27')}
  for q,terms in {'american':{'United States'},'british':{'United Kingdom','Kingdom of Great Britain','Kingdom of England','England','Scotland'},'french':{'France','Kingdom of France','French Third Republic','First French Empire'},'japanese':set()}.items():
   # Existing japanese question is creation of a fictional version, hence NO for real people.
   if q=='japanese':a[q]=0
   elif countries&terms:a[q]=4
  if born is not None:
   a['born_before1970']=4 if born<1970 else 0;a['pre1800']=4 if born<1800 else 0
  if born is not None and died is not None and (born>=1900 or died<1800):a['nineteenth']=0
 for y in [1600,1700,1750,1850,1900]:a['birth_before_'+str(y)]=dated_answer(r,'P569',y)
 for y in [1800,1900,1950,2000]:a['death_before_'+str(y)]=dated_answer(r,'P570',y)
 for q,(_,terms) in roles.items():
  if added:a['bio_'+q]=4 if q in r['reviewed_fame'] else 0
  # Existing biographies retain UNKNOWN on new fame questions: occupations alone
  # are not proof of what someone is well known for.
 for lang in ['English','French','German','Russian','Italian','Spanish','Japanese','Portuguese']:
  if lang in langs:a['language_'+lang.lower()]=4
 nobel={'Q38104','Q38106','Q44585','Q37922','Q80061','Q47170'}
 if entity_ids(r,'P166')&nobel:a['nobel']=4
 elif died is not None and died<1901:a['nobel']=0
 # Preserve original facts, including original UNKNOWNs, except the new questions.
 if added:
  geo=set(r['reviewed_geography'])
  for q,yes in {'american':'america' in geo,'british':'britain' in geo,'french':'france' in geo,'european':bool(geo&{'france','germany','russia','italy','spain','austria','other_europe'}),'african':False,'asian':'asia' in geo and r['id'] not in {'Q5676','Q5586'}}.items():a[q]=4 if yes else 0
  if 'astronomy' in r['reviewed_fame']:a['space']=4
  if r['id'] in {'Q16867','Q47152'}:a['horror']=4
  if r['id'] in {'Q5816','Q2042','Q33866','Q34296','Q35236','Q8573'}:a.update(politician=4,leader=4)
 if added:c['notes']='Real historical person. CC0 structured biography; missing facts remain UNKNOWN. Dates use recorded year precision.'
 c['sources']=list(dict.fromkeys(c.get('sources',[])+['wikidata_cc0']))
 c['biography']=r['id']
for r in records:
 key=norm(r['name']);c=original_ids.get(key);added=c is None
 if added:
  ident=re.sub('[^a-z0-9]+','_',ascii_name(r['name']).lower()).strip('_')
  if ident in baseids:raise ValueError('Duplicate identity '+ident)
  c={'id':ident,'name':ascii_name(r['name']),'answers':{q['id']:2 for q in s['questions']},'sources':['wikidata_cc0']};baseids.add(ident);s['characters'].append(c)
 apply(r,c,added)
s['sources']['wikidata_cc0']={'url':'https://www.wikidata.org/wiki/Wikidata:Licensing','kind':'CC0 structured facts','scope':'Biographical fields in BIOGRAPHIES.JSON. Absence is not a negative. Offline conversion in tools/EXPAND.PY.'}
s['title']='TANDINATOR Expanded 384 - local development'
s['portrayal_policy']+=' Expansion: new real biographies use only positive occupation/language claims, explicit dates, and logical real-human traits. New questions never fill old UNKNOWN cells.'
assert len(s['characters'])==384
(P/'data/STARTER.JSON').write_text(json.dumps(s,indent=2,ensure_ascii=True)+'\n')
print('Roster',len(s['characters']),'questions',len(s['questions']),'added biographies',len(s['characters'])-256)
