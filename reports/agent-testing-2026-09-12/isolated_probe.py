import asyncio,json,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'backend'/'agent'))
from app.chat.streaming import StreamConfig,stream_agent_events
from app.chat.event_sink import emit_answer_delta
from app.chat.pending_events import emit_pending_action_clear
from app.agent.runtime import _extract_reasoning_content_from_chunk
from app.agent.client.gateway import _is_explicit_confirmation
class Workflow:
 def __init__(self,mode):self.mode=mode
 async def astream(self,state,stream_mode):
  if self.mode=='normal':emit_answer_delta('visible answer')
  if self.mode=='pending':emit_answer_delta('preview ready');emit_pending_action_clear()
  yield 'values',{'result':'fallback answer'}
async def main():
 results=[]
 for mode in ['normal','fallback','answer_save_failure','pending']:
  saved=[];failures=[]
  async def save(text,tools):
   if mode=='answer_save_failure':failures.append('save_failed');raise RuntimeError('simulated store outage')
   saved.append(text)
  async def pending(event):failures.append('pending_save_failed');raise RuntimeError('simulated pending store outage')
  events=[e async for e in stream_agent_events(StreamConfig(workflow=Workflow('normal' if mode=='answer_save_failure' else mode),build_initial_state=lambda:{},extract_final_content=lambda s:s['result'],on_answer_completed=save,on_pending_action=pending))]
  results.append({'case':mode,'displayed':''.join(e.text or '' for e in events if e.type.value=='answer'),'saved':saved,'events':[e.type.value for e in events],'injected_failures':failures})
 chunks=['I ','will ','search'];results.append({'case':'reasoning_spaces','input':chunks,'actual':''.join(_extract_reasoning_content_from_chunk(SimpleNamespace(reasoning_content=t,additional_kwargs={})) for t in chunks)})
 results.append({'case':'confirmation_parser','actual':{x:_is_explicit_confirmation(x) for x in ['确认','取消','不要','没问题','确认？','确认!']}})
 Path(__file__).with_name('isolated-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(results,ensure_ascii=True,indent=2))
asyncio.run(main())