import json,sys,time,uuid
from pathlib import Path
import httpx
OUT=Path(__file__).parent
creds=json.loads(sys.stdin.readline())
client=httpx.Client(base_url='http://localhost:8080',timeout=120,trust_env=False)
r=client.post('/api/client/auth/login',json=creds)
payload=r.json(); data=payload.get('data') or {}; token=data.get('accessToken') or data.get('token')
if not token:
 print(json.dumps({'login_status':r.status_code,'code':payload.get('code'),'message':payload.get('message')},ensure_ascii=True),flush=True);sys.exit(1)
client.headers['Authorization']='Bearer '+token
results={'role':(data.get('user') or {}).get('role'),'checks':[],'cases':[]}
def save(): OUT.joinpath('live-action-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
def unwrap(r):
 p=r.json(); return p.get('data',p) if isinstance(p,dict) else p
for path in ['/api/client/agent/health','/api/admin/agent/chat/sessions','/api/client/agent/sessions/'+str(uuid.uuid4())+'/history']:
 r=client.get(path); results['checks'].append({'path':path,'status':r.status_code,'body':r.json()});print(json.dumps(results['checks'][-1],ensure_ascii=True),flush=True)
print('LOGIN_OK role='+str(results['role']),flush=True);save()
sessions={}
cases=[('preview','请推荐《无职转生 第三季》（站内ID 84），并调用预览加入想看工具，等待确认，禁止执行写入。'),('cancel','取消，不要加入想看。')]
for name,prompt in cases:
 key='search' if name=='search_followup' else 'preview' if name=='cancel' else name
 if key not in sessions:
  r=client.post('/api/client/agent/sessions',json={}); s=unwrap(r)
  sid=s.get('session_id') or s.get('sessionId') if isinstance(s,dict) else None
  if not sid: print('SESSION_FAILED '+str(r.status_code)+' '+str(s),flush=True);break
  sessions[key]=sid
 sid=sessions[key]; rec={'name':name,'prompt':prompt,'session_id':sid,'tools':[],'events':[]};start=time.monotonic();answer=[];thinking_count=0
 try:
  with client.stream('POST','/api/client/agent/stream',json={'session_id':sid,'content':prompt},headers={'X-Request-ID':'agent-test-'+name}) as response:
   rec['status']=response.status_code;rec['content_type']=response.headers.get('content-type');rec['cache_control']=response.headers.get('cache-control')
   for line in response.iter_lines():
    if not line.startswith('data:'):continue
    raw=line[5:].strip()
    try:e=json.loads(raw)
    except Exception:rec.setdefault('parse_errors',[]).append(raw[:150]);continue
    content=e.get('content') or {};typ=e.get('type')
    if typ=='answer' and content.get('text'):
     if not answer:rec['first_answer_seconds']=round(time.monotonic()-start,2)
     answer.append(content['text'])
    if typ=='thinking':thinking_count+=1
    if typ=='function_call':rec['tools'].append(content)
    if typ not in ['thinking','answer']:rec['events'].append(e)
    if e.get('is_end') or e.get('isEnd'):rec['ended']=True
  rec['answer']=''.join(answer);rec['thinking_chunks']=thinking_count
  history=unwrap(client.get('/api/client/agent/sessions/'+sid+'/history'))
  rec['history']=history
  msgs=history if isinstance(history,list) else history.get('messages',[])
  assistants=[m for m in msgs if m.get('role')=='assistant'];rec['history_matches']=bool(assistants) and assistants[-1].get('content')==rec['answer']
 except Exception as exc:rec['error']=type(exc).__name__+': '+str(exc)
 rec['seconds']=round(time.monotonic()-start,2);results['cases'].append(rec);save()
 print(json.dumps({k:rec.get(k) for k in ['name','status','seconds','ended','history_matches','answer','error']} ,ensure_ascii=True),flush=True)
print('DONE',flush=True)