import json,sys
from pathlib import Path
import httpx
root=Path(__file__).parent; c=httpx.Client(base_url='http://localhost:8080',timeout=20,trust_env=False)
r=c.post('/api/client/auth/login',json=json.loads(sys.stdin.readline())).json()['data'];c.headers['Authorization']='Bearer '+(r.get('accessToken') or r.get('token'));rows=[]
def check(name,method,path,body=None):
 r=c.request(method,path,json=body);p=r.json();rows.append({'name':name,'status':r.status_code,'body':p});print(json.dumps({'name':name,'status':r.status_code,'code':p.get('code')},ensure_ascii=True));return p.get('data',p)
a=json.loads(root.joinpath('live-admin-results.json').read_text(encoding='utf8'));u=json.loads(root.joinpath('live-user-results.json').read_text(encoding='utf8'));foreign=a['cases'][0]['session_id'];own=u['cases'][0]['session_id']
check('cross_user_history','GET','/api/client/agent/sessions/'+foreign+'/history')
check('cross_user_stream','POST','/api/client/agent/stream',{'session_id':foreign,'content':'hello'})
check('empty_message','POST','/api/client/agent/stream',{'session_id':own,'content':''})
check('oversize_message','POST','/api/client/agent/stream',{'session_id':own,'content':'x'*4097})
check('invalid_session','POST','/api/client/agent/stream',{'session_id':'agent-test-nonexistent','content':'hello'})
check('collection_after_cancel','GET','/api/client/collections/84')
check('subject_84_authority','GET','/api/client/subjects/84')
check('subject_84_episodes','GET','/api/client/subjects/84/episodes')
check('lexical_release','POST','/api/client/subjects/lexical-search',{'q':'无职转生','limit':5})
check('saturday_schedule','GET','/api/client/subjects/schedule?weekday=6&year=2026&quarter=summer&page=1&size=50')
root.joinpath('boundary-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')