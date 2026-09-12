import json,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path('backend/agent').resolve()))
from app.agent.client.actions.wishlist import _check_collection_state,build_wishlist_tools
from app.chat.user import UserInfo
from app.chat.pending_events import set_pending_action_collector,reset_pending_action_collector,get_pending_action_event
class Business:
 def request(self,*args,**kwargs):return {'code':200,'message':'success'}
b=Business();user=UserInfo(user_id=999,username='isolated',role='USER');token=set_pending_action_collector()
try:
 state=_check_collection_state(84,user,b);tools=build_wishlist_tools(b);preview=tools[0].func(subjects=[{'subjectId':84,'subjectName':'fixture'}],user=user)
 r={'business_response':b.request(),'collection_state':state,'preview':preview,'pending_created':get_pending_action_event() is not None};Path('reports/agent-testing-2026-09-12/empty-collection-results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r))
finally:reset_pending_action_collector(token)
