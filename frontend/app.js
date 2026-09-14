const $ = (id) => document.getElementById(id);
let state = null;

function showMessage(text, error=false){
  const el = $('message'); el.textContent = text; el.className = 'banner' + (error ? ' error' : '');
  setTimeout(()=>el.classList.add('hidden'), 4500);
}
async function api(path, options={}){
  const res = await fetch(path,{headers:{'Content-Type':'application/json'},...options});
  const data = await res.json(); if(!res.ok) throw new Error(data.detail || 'Request failed'); return data;
}
function volunteerName(id){return state?.volunteers?.[id]?.name || 'Unassigned';}
function render(){
  if(!state) return;
  const route = state.routes.r3;
  const mode = state.strands?.enabled ? 'Strands live' : 'Demo fallback';
  const modeEl = $('agentMode');
  modeEl.textContent = mode;
  modeEl.style.background = state.strands?.enabled ? '#edf4ee' : '#fff5d8';
  modeEl.title = state.strands?.enabled ? `Model: ${state.strands.model_id}` : 'Set PORCHLIGHT_USE_STRANDS=1 after installing Strands';
  $('routeStatus').textContent = route.status;
  $('assignedVolunteer').textContent = volunteerName(route.volunteer_id);
  const open = state.issues.filter(i=>i.status==='open');
  $('openCount').textContent = open.length;
  $('stopList').innerHTML = route.stop_ids.map(sid=>{
    const s=state.stops[sid]; const status=s.outcome || 'pending';
    const cls = status==='no_answer' || status==='emergency' ? 'pill attn':'pill';
    return `<div class="route"><div class="person"><div class="avatar">${s.sequence}</div><div><strong>${s.recipient}</strong><div class="sub">${s.address}</div></div></div><span class="${cls}">${status.replaceAll('_',' ')}</span></div>`
  }).join('');
  $('issues').innerHTML = open.length ? open.map(i=>`<div class="issue"><strong>Human action required</strong><p>${i.reason}</p><small>${i.severity} severity · ${i.id}</small><div><button class="btn btn-primary" style="margin-top:10px" onclick="ackIssue('${i.id}')">Acknowledge</button></div></div>`).join('') : '<div class="sub" style="margin-top:14px">No open issues.</div>';
  $('activity').innerHTML = state.activity.map(a=>`<div class="event ${a.human_action_required?'attention':''}"><div class="meta"><span>${a.event_type.replaceAll('_',' ')}</span><span>${new Date(a.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span></div><p>${a.message}</p><div class="sub" style="margin-top:5px">${a.actor === 'strands_tool' ? 'Strands tool' : a.actor === 'strands' ? 'Strands agent' : a.actor === 'human_event' ? 'Human event' : 'System'}</div>${a.human_action_required?'<div class="needs">Needs human attention</div>':''}</div>`).join('');
}
async function refresh(){state=await api('/api/state');render();}
async function action(path, options={method:'POST'}){try{const d=await api(path,options);await refresh();return d}catch(e){showMessage(e.message,true);throw e}}
window.ackIssue = async(id)=>{await action(`/api/issues/${id}/acknowledge`);showMessage('Issue acknowledged.');};

$('coordinatorTab').onclick=()=>{ $('coordinatorView').classList.remove('hidden');$('volunteerView').classList.add('hidden');$('coordinatorTab').classList.add('active');$('volunteerTab').classList.remove('active'); };
$('volunteerTab').onclick=()=>{ $('coordinatorView').classList.add('hidden');$('volunteerView').classList.remove('hidden');$('coordinatorTab').classList.remove('active');$('volunteerTab').classList.add('active'); };
$('resetBtn').onclick=async()=>{await action('/api/demo/reset');showMessage('Demo reset.');};
$('cancelBtn').onclick=async()=>{
  const btn=$('cancelBtn');
  const oldText=btn.textContent;
  btn.disabled=true;
  btn.textContent='Strands is working…';
  showMessage('Porchlight is asking Strands to restore route coverage…');
  try{
    const d=await action('/api/demo/cancellation');
    showMessage(d.mode==='strands'?`Strands restored coverage${d.attempts>1?' after a retry':''}.`:'Demo fallback resolved the coverage event.');
  } finally {
    btn.disabled=false;
    btn.textContent=oldText;
  }
};
$('reconcileBtn').onclick=async()=>{const d=await action('/api/demo/reconcile');showMessage(`${d.mode==='strands'?'Strands':'Demo fallback'} completed route reconciliation.`);};
$('noAnswerBtn').onclick=()=>{$('protocol').classList.remove('hidden');};
$('protocolDoneBtn').onclick=async()=>{const note=$('note').value || 'Volunteer completed the approved no-answer checklist.';await action('/api/demo/no-answer',{method:'POST',body:JSON.stringify({note})});showMessage('No-answer outcome recorded and coordinator notified.');$('protocol').classList.add('hidden');};
$('deliveredBtn').onclick=async()=>{showMessage('For this demo story, use “Problem / No Answer” to exercise the agent workflow.');};
$('completeRestBtn').onclick=async()=>{await action('/api/demo/complete-rest');showMessage('Remaining normal deliveries recorded.');};
refresh();
