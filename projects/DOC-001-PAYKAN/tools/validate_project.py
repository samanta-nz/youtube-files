#!/usr/bin/env python3
"""Deterministic editorial / data-structure checks; does not certify history or media rights."""
import json,re,sys,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1]
files=['manifest','source_register','verified_facts','disputed_claims','script','storyboard','assets_manifest','selected_shots','timeline','youtube','qc_report']
errors=[];d={}
for f in files:
 p=r/(f+'.json')
 if not p.is_file(): errors.append('MISSING: '+str(p));continue
 try:d[f]=json.loads(p.read_text(encoding='utf8'))
 except Exception as ex:errors.append('JSON_FAIL '+f+': '+str(ex))
if errors:
 print('\n'.join(errors));sys.exit(1)
a=d['manifest'];ss=d['script']['segments'];sb=d['storyboard']['segments'];tt=d['timeline']['segments'];src=d['source_register']['sources'];facts=d['verified_facts']['facts']
src_ids={x['id'] for x in src};fact_ids={x['id'] for x in facts};sid=[x['id'] for x in ss]
def check(ok,msg):
 if not ok:errors.append(msg)
check(len(sid)==10 and len(sid)==len(set(sid)), 'Expected 10 unique script segments')
check([x['id'] for x in sb]==sid==[x['id'] for x in tt], 'Segment id mismatch across script, storyboard and timeline')
check(all(x['source_ids'] and set(x['source_ids'])<=src_ids for x in ss),'Untraceable segment sources')
check(all(x['fact_ids'] and set(x['fact_ids'])<=fact_ids for x in ss),'Untraceable segment facts')
check(all(x['source_ids'] and set(x['source_ids'])<=src_ids for x in facts), 'Untraceable fact sources')
check(all(s['url'].startswith('https://') for s in src), 'Invalid source URL')
for x in ss:
 txt=(r/'tts'/(x['id']+'.txt')).read_text(encoding='utf8').strip()
 check(x['text_fa'].strip()==txt,'TTS divergence: '+x['id'])
 check(x['word_count']==len(txt.split()), 'Word count mismatch: '+x['id'])
check(sum(x['word_count'] for x in ss)==d['script']['total_words'],'Total word count mismatch')
check(1200<=d['script']['estimated_duration_seconds_at_132_wpm']<=1500,'Estimated audio duration outside 20-25min')
check(sum(x['target_seconds'] for x in sb)==d['timeline']['total_estimated_seconds'],'Total storyboard duration not aligned')
check(sum(x['duration_s'] for x in tt)==d['timeline']['total_estimated_seconds'],'Total timeline duration not aligned')
check(all(b['start_estimated_seconds']==t['start_s'] and b['target_seconds']==t['duration_s'] for b,t in zip(sb,tt)), 'Timeline positions mismatch')
biz=sum(x['target_seconds'] for x in sb if x['business_failure_focus'])/d['timeline']['total_estimated_seconds']
check(biz>=.65, f'business-focus flag duration only {biz:.1%}')
first=ss[0]['text_fa'].splitlines()[0]
first_four=re.split(r'(?<=[.؟!])\s+',first)
check(len(first_four)==4,'Hook is not four sentences')
check(45<=len(first.split())<=65, 'Hook word count out of range')
check(a['gates']['script_approved_by_user'] is False, 'Script wrongly marked approved')
check(a['gates']['tts_audio_received'] is False, 'TTS audio wrongly marked received')
check(a['current_stage']=='SCRIPT_APPROVAL_REQUESTED','Incorrect pipeline stage')
check(a['pipeline'][0]['status']=='DONE' and a['pipeline'][1]['status']=='DONE' and a['pipeline'][2]['status']=='DONE','Research stages not done')
check(a['pipeline'][3]['status']=='NEEDS_REVIEW','Must wait for user script approval')
check(all(z['rights_status']!='CLEARED' for z in d['assets_manifest']['media_entries']),'Imagery incorrectly cleared')
check(len({z['id'] for z in d['assets_manifest']['media_entries']})==len(d['assets_manifest']['media_entries']),'Duplicate asset id')
check(d['youtube']['video_visibility']=='PRIVATE_ONLY_AFTER_WORK_HANDOFF','Unsafe publishing setting')
check(a['gates']['publish'] is False,'Unsafe publication gate')
print('QC STRUCTURE:', 'PASS' if not errors else 'FAIL')
print('Segments:',len(ss),'Words:',sum(x['word_count'] for x in ss),'Hook words:',len(first.split()))
print('Estimated audio minutes:',round(d['timeline']['total_estimated_seconds']/60,2),'Business-focus storyboard duration:',round(biz*100,1),'%')
print('Verified research facts:',len(facts),'Sources:',len(src),'License-clear archival assets:',0)
print('Text SHA256:',hashlib.sha256((r/'tts/script_draft.txt').read_bytes()).hexdigest())
for e in errors:print('ERROR:',e)
sys.exit(0 if not errors else 1)
