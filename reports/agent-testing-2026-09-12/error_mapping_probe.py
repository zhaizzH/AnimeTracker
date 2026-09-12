import json,sys
from pathlib import Path
import httpx
root=Path('reports/agent-testing-2026-09-12');c=httpx.Client(timeout=20,trust_env=False);d=c.post('http://localhost:8080/api/client/auth/login',json=json.loads(sys.stdin.readline())).json()['data'];c.headers['Authorization']='Bearer '+(d.get('token') or d.get('accessToken'));u=json.loads((root/'live-user-results.json').read_text(encoding='utf8'));sid=u['cases'][0]['session_id'];a=json.loads((root/'live-admin-results.json').read_text(encoding='utf8'));foreign=a['cases'][0]['session_id'];rows=[]
for name,body in [('empty',{'session_id':sid,'content':''}),('oversize',{'session_id':sid,'content':'x'*4097}),('foreign',{'session_id':foreign,'content':'hello'}),('nonexistent',{'session_id':'agent-test-nonexistent','content':'hello'})]:
 for port in [8090,8080]:
  r=c.post(f'http://localhost:{port}/api/client/agent/stream',json=body);item={'name':name,'port':port,'status':r.status_code,'body':r.json()};rows.append(item);print(json.dumps({'name':name,'port':port,'status':r.status_code}))
(root/'error-mapping-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
