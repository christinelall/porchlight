import {$,api,esc,humanStatus,initials,toast,mapsUrl,telUrl,saveCachedState,loadCachedState,registerServiceWorker,installConnectivityBanner} from '/static/shared.js';

let state=null;
let selectedStop=null;
let offlineMode=false;
const routeId=new URLSearchParams(location.search).get('route')||'r3';

registerServiceWorker();
installConnectivityBanner('#connectivity');

function currentRoute(){return state?.routes?.[routeId]}
function assigned(){const r=currentRoute();return r?state.volunteers[r.volunteer_id]:null}
function summary(){return state?.route_summaries?.[routeId]}
function nextStop(){const r=currentRoute();return r?.stop_ids.map(id=>state.stops[id]).find(s=>!s.outcome)}
function writeGuard(){if(offlineMode||!navigator.onLine){toast('You are offline. Reconnect before recording or changing delivery outcomes.',true);return false}return true}
function coordinatorPhone(){return state?.organization?.coordinator_phone||''}
function coordinatorName(){return state?.organization?.coordinator_name||'Coordinator'}

function routeHome(){
 const r=currentRoute(); if(!r){$('#app').innerHTML='<div class="empty">No route is assigned in this view.</div>';return}
 const v=assigned(),s=summary(),n=nextStop();
 $('#app').innerHTML=`
 <section class="greeting"><div class="sub">Today</div><h1>Hi, ${esc(v?.name||'Volunteer')}</h1><p>${r.status==='complete'?'Thanks — every stop on this route is accounted for.':'Here’s your delivery route.'}</p></section>
 ${offlineMode?`<div class="offline-card"><strong>Offline mode</strong><span>You can still view the last synced route and delivery instructions. Reconnect before submitting outcomes.</span></div>`:''}
 <section class="route-hero"><div class="sub">${r.start_time} start · ${s.total} stops</div><h2>${esc(r.name)}</h2><div class="big-progress"><div class="progress-label"><strong>${s.delivered+s.exceptions} of ${s.total} accounted for</strong><span class="sub">${s.percent}%</span></div><div class="progress"><span style="width:${s.percent}%"></span></div></div><div class="mobile-route-strip">${r.stop_ids.map(id=>{const x=state.stops[id];return `<span class="mini-route-node ${x.outcome==='delivered'?'done':x.outcome?'exception':n?.id===x.id?'current':'pending'}">${x.outcome==='delivered'?'✓':x.sequence}</span>`}).join('<i></i>')}</div><div class="meta-row"><span>◷ Est. finish ${r.estimated_finish||'—'}</span><span>● ${esc(humanStatus(s.lifecycle||r.status))}</span></div></section>
 <div class="mobile-action-strip"><a class="mini-action" href="${esc(telUrl(coordinatorPhone()))}">☎ ${esc(coordinatorName())}</a><span class="mini-action muted">Route ${esc(r.name)}</span></div>
 <div class="section-title">Your stops</div><div class="route-stops">${r.stop_ids.map(id=>{const x=state.stops[id];return `<button class="vol-stop ${x.outcome?'done':''} ${n?.id===x.id?'current':''}" data-stop="${x.id}"><div class="stop-num">${x.outcome==='delivered'?'✓':x.sequence}</div><div class="grow"><strong>${esc(x.recipient)}</strong><div class="sub">${esc(x.address)}</div></div><div class="sub">${x.outcome?humanStatus(x.outcome):n?.id===x.id?'Next':'Pending'} ›</div></button>`}).join('')}</div>`;
 $('#bottom').innerHTML=r.status==='complete'?`<div class="bottom-action"><div class="btn btn-sage">Route complete · Thank you</div></div>`:r.started_at?(n?`<div class="bottom-action"><button class="btn btn-primary" id="nextBtn">Continue to ${esc(n.recipient)}</button></div>`:`<div class="bottom-action"><div class="btn btn-secondary">All stops recorded · waiting for any coordinator review</div></div>`):`<div class="bottom-action"><button class="btn btn-primary" id="startBtn" ${offlineMode?'disabled':''}>Start route</button></div>`;
 document.querySelectorAll('[data-stop]').forEach(b=>b.onclick=()=>showStop(b.dataset.stop));
 const start=$('#startBtn');if(start)start.onclick=startRoute;const next=$('#nextBtn');if(next)next.onclick=()=>showStop(n.id);
}

async function startRoute(){if(!writeGuard())return;try{await api(`/api/routes/${routeId}/start`,{method:'POST',body:JSON.stringify({volunteer_id:assigned().id})});toast('Route started. Drive safely.');await refresh();showStop(nextStop().id)}catch(e){toast(e.message,true)}}

function showStop(id){
 selectedStop=id;const x=state.stops[id],r=currentRoute();
 $('#app').innerHTML=`
 <div class="stop-nav"><button class="btn btn-ghost" id="backBtn">← Route</button><div class="sub">Stop ${x.sequence} of ${r.stop_ids.length}</div><span></span></div>
 <section class="care-top"><div class="care-avatar">${initials(x.recipient)}</div><h1>${esc(x.recipient)}</h1>${x.accessibility?`<span class="access-tag">ⓘ ${esc(x.accessibility)}</span>`:''}<p class="sub">${esc(x.address)}</p><a class="btn btn-secondary btn-sm navigate-btn" target="_blank" rel="noopener" href="${esc(mapsUrl(x.address))}">↗ Navigate</a></section>
 ${x.conversation_starter?`<div class="warm-note"><label>Conversation starter</label><p>“${esc(x.conversation_starter)}”</p></div>`:''}
 <div class="info-box"><label>Delivery instructions</label><p>${esc(x.delivery_notes||'No special access instructions.')}</p></div>
 <div class="meal-grid"><div class="info-box"><label>Meal</label><p>${esc(x.meal_items||'1 meal')}</p></div><div class="info-box"><label>Diet</label><p>${esc(x.diet||'Regular')}</p></div></div>
 ${x.outcome?`<div class="info-box outcome-record"><label>Recorded outcome</label><p>${esc(humanStatus(x.outcome))}</p>${x.outcome_note?`<div class="sub" style="margin-top:5px">${esc(x.outcome_note)}</div>`:''}</div>`:''}`;
 $('#bottom').innerHTML=x.outcome?`<div class="bottom-action"><button class="btn btn-secondary" id="backBottom">Back to route</button></div>`:`<div class="bottom-action"><button class="btn btn-sage" id="deliveredBtn" ${offlineMode?'disabled':''}>✓ Delivered</button><button class="btn btn-ghost problem-link" id="problemBtn" ${offlineMode?'disabled':''}>Problem / no answer</button></div>`;
 $('#backBtn').onclick=routeHome;const bb=$('#backBottom');if(bb)bb.onclick=routeHome;
 const d=$('#deliveredBtn');if(d)d.onclick=()=>submitOutcome('delivered','Meal handed to recipient.');
 const p=$('#problemBtn');if(p)p.onclick=openProblem;
}

function protocolChecklist(protocol){
 if(!protocol)return '';
 return `<div class="protocol"><div class="protocol-head"><strong>${esc(protocol.title)} protocol</strong><span class="severity severity-${esc(protocol.severity)}">${esc(protocol.severity)} priority</span></div><p class="protocol-helper">Follow each organization-approved step. Porchlight will not make a welfare or medical judgment.</p><div class="protocol-steps">${protocol.ordered_steps.map((step,i)=>`<label class="protocol-step"><input type="checkbox" data-protocol-step><span class="step-number">${i+1}</span><span>${esc(step)}</span></label>`).join('')}</div></div>`;
}

function openProblem(){
 if(!writeGuard())return;
 const phone=coordinatorPhone();
 $('#sheetRoot').innerHTML=`<div class="sheet-backdrop" id="sheetBg"><div class="sheet"><div class="sheet-handle"></div><h2>What happened?</h2><p>Choose the closest factual outcome. Porchlight follows your organization’s approved process and brings a person in when required.</p><div class="choice-list">${[['no_answer','No answer'],['recipient_declined','Recipient declined'],['could_not_access','Could not access property'],['meal_issue','Problem with meal'],['welfare_concern','Welfare concern'],['other','Something else']].map(([v,l])=>`<button class="choice" data-choice="${v}">${l}</button>`).join('')}</div><div id="urgentArea"></div><div id="protocolArea"></div><label class="sub note-label" for="outcomeNote">Factual note</label><textarea id="outcomeNote" class="field" placeholder="Describe only what you observed."></textarea><div id="nextStepHint"></div><button class="btn btn-primary" id="submitProblem" style="width:100%;margin-top:12px" disabled>Submit outcome</button>${phone?`<a class="btn btn-secondary" href="${esc(telUrl(phone))}" style="width:100%;margin-top:8px">☎ Call ${esc(coordinatorName())}</a>`:''}<button class="btn btn-ghost" id="cancelSheet" style="width:100%;margin-top:6px">Cancel</button></div></div>`;
 let choice=null;
 document.querySelectorAll('[data-choice]').forEach(b=>b.onclick=()=>{
   choice=b.dataset.choice;document.querySelectorAll('[data-choice]').forEach(x=>x.classList.toggle('selected',x===b));
   const pr=state.protocols[choice];$('#protocolArea').innerHTML=protocolChecklist(pr);
   $('#urgentArea').innerHTML=choice==='welfare_concern'?`<div class="urgent-card"><strong>Human review required</strong><span>${esc(state.organization?.emergency_note||'Contact the site coordinator immediately.')}</span></div>`:'';
   $('#outcomeNote').placeholder=pr?.note_prompt||'Describe only what you observed.';
   $('#nextStepHint').innerHTML=pr?`<div class="what-next"><strong>What happens next</strong><span>${pr.requires_acknowledgement?`This stays open until ${esc(pr.escalation_target)} reviews it.`:`This is recorded and the route can continue without a human review.`}</span></div>`:'';
   $('#submitProblem').disabled=false;
 });
 $('#cancelSheet').onclick=()=>$('#sheetRoot').innerHTML='';$('#sheetBg').onclick=e=>{if(e.target.id==='sheetBg')$('#sheetRoot').innerHTML=''};
 $('#submitProblem').onclick=async()=>{
   if(!choice)return;
   const pr=state.protocols[choice];
   if(pr){const checks=[...document.querySelectorAll('[data-protocol-step]')];if(checks.some(c=>!c.checked)){toast('Complete each protocol step before submitting.',true);return}}
   const note=$('#outcomeNote').value.trim();if(note.length<3){toast('Add a short factual note about what you observed.',true);return}
   await submitOutcome(choice,note,!!pr);
 };
}

async function submitOutcome(outcome,note='',protocol_completed=false){if(!writeGuard())return;try{await api(`/api/routes/${routeId}/stops/${selectedStop}/outcome`,{method:'POST',body:JSON.stringify({outcome,note,protocol_completed})});$('#sheetRoot').innerHTML='';toast(outcome==='delivered'?'Delivery recorded.':'Outcome recorded. Anything requiring a person has been surfaced to the coordinator.');await refresh();routeHome()}catch(e){toast(e.message,true)}}

async function refresh(){
 try{state=await api('/api/state');offlineMode=false;saveCachedState(state)}catch(e){const cached=loadCachedState();if(!cached?.state){$('#app').innerHTML='<div class="empty">Porchlight cannot load this route right now. Check your connection and try again.</div>';return}state=cached.state;offlineMode=true}
 routeHome();
}

window.addEventListener('online',()=>refresh());window.addEventListener('offline',()=>{offlineMode=true;routeHome()});
refresh();
