import {$,api,esc,timeAgo,humanStatus,statusBadge,toast,clock,mapsUrl} from '/static/shared.js';
let state=null; let filter=''; let initialRoute=new URLSearchParams(location.search).get('route');

function lifecycleStatus(route){return state?.route_summaries?.[route.id]?.lifecycle||route.status}
function attentionStatus(route){return state?.route_summaries?.[route.id]?.attention||null}
function overlayBadge(route){const att=attentionStatus(route);return att?statusBadge(att):''}
function greeting(){const h=new Date().getHours();return h<12?'Good morning':h<18?'Good afternoon':'Good evening'}
function severityRank(s){return ({high:3,medium:2,low:1})[s]||0}
function nextPending(routeId){const r=state.routes[routeId];return r?.stop_ids.map(id=>state.stops[id]).find(x=>!x.outcome)||null}

function routeRow(route){
  const s=state.route_summaries[route.id]; const v=state.volunteers[route.volunteer_id];
  return `<button class="route-row" data-route="${route.id}" style="width:100%;text-align:left">
    <div><div class="route-name">${esc(route.name)}</div><div class="sub">${esc(v?.name||'Unassigned')} · ${route.start_time} · ${s.total} stops</div><div class="progress"><span style="width:${s.percent}%"></span></div></div>
    <div class="route-meta hide-sm"><span class="sub">Progress</span><strong>${s.delivered+s.exceptions}/${s.total}</strong></div>
    <div class="route-meta hide-md"><span class="sub">Est. finish</span><strong>${route.estimated_finish||'—'}</strong></div>
    <div class="hide-sm status-stack">${statusBadge(lifecycleStatus(route))}${overlayBadge(route)}</div><div class="chev">›</div></button>`;
}

function recommendedRouteAction(r){
  if(r.status==='uncovered')return 'Find approved replacement';
  if(r.status==='at_risk' && r.last_contact_at)return 'Confirm availability or replace';
  if(r.status==='at_risk')return 'Send route-start reminder';
  return 'Review route';
}

function routeAttention(r){
 const v=state.volunteers[r.volunteer_id];
 const overdue=r.overdue_minutes?`${r.overdue_minutes} minutes overdue`:'Start requires attention';
 const last=r.last_contact_at?`${esc(r.last_contact_status||'Contacted')} · ${timeAgo(r.last_contact_at)}`:esc(r.last_contact_status||'No reminder sent yet');
 return `<div class="attention-item"><div class="attention-top"><div><div class="attention-title">${esc(r.name)}</div><div class="sub">${esc(v?.name||'Unassigned')} · scheduled ${r.start_time}</div></div>${statusBadge(attentionStatus(r)||r.status)}</div>
 <p>${esc(r.risk_note||'This route needs coordinator attention.')}</p>
 <div class="attention-facts"><div><span>Timing</span><strong>${esc(overdue)}</strong></div><div><span>Last contact</span><strong>${last}</strong></div><div><span>Recommended</span><strong>${esc(recommendedRouteAction(r))}</strong></div></div>
 <div class="action-row">${r.status==='uncovered'?`<button class="btn btn-primary btn-sm" data-route-attn="${r.id}">Find replacement</button>`:`<button class="btn btn-primary btn-sm" data-remind="${r.id}">Send reminder</button><button class="btn btn-secondary btn-sm" data-route-attn="${r.id}">Open route</button>`}</div></div>`;
}

function issueActionLabel(issue){
 if(issue.type.includes('welfare'))return 'Review welfare concern';
 if(issue.type.includes('meal'))return 'Review meal issue';
 if(issue.type.includes('no_answer'))return 'Review no-answer';
 if(issue.type==='coverage_gap')return 'Resolve coverage';
 return 'Review & acknowledge';
}

function handledStory(a){
  const r=state.routes[a.route_id];
  const routeName=r?.name||'Route';
  let title=humanStatus(a.event_type), detail=a.message, icon='✓', tag='Handled';
  if(a.event_type==='coverage_restored'){
    const comms=state.communications.filter(c=>c.route_id===a.route_id && ['accept','decline'].includes(c.status));
    const declined=comms.filter(c=>c.status==='decline').map(c=>c.volunteer_name);
    const accepted=comms.find(c=>c.status==='accept');
    title=`${routeName} coverage restored`;
    detail=declined.length?`${declined.join(', ')} declined; ${accepted?.volunteer_name||'an approved backup'} accepted. No coordinator action was needed.`:a.message;
    icon='↻';
  } else if(a.event_type==='route_reconciled' || a.event_type==='route_complete'){
    const s=state.route_summaries[a.route_id];
    title=`${routeName} closed cleanly`;
    detail=s?`${s.total} scheduled stops accounted for with ${s.exceptions} exception${s.exceptions===1?'':'s'} and no open review.`:a.message;
    icon='✓';
  } else if(a.event_type==='volunteer_reminder_sent'){
    title=`${routeName} reminder sent`;
    detail=a.message; icon='→'; tag='In progress';
  } else if(a.event_type==='routine_confirmation' || a.event_type==='route_confirmed'){
    title=`${routeName} coverage confirmed`;
    detail=a.message; icon='●';
  } else if(a.event_type==='coordinator_reassignment'){
    title=`${routeName} manually reassigned`; detail=a.message; icon='↔'; tag='Human action';
  }
  return `<div class="handled-card"><div class="handled-icon">${icon}</div><div class="grow"><div class="handled-top"><strong>${esc(title)}</strong><span>${esc(tag)}</span></div><p>${esc(detail)}</p><small>${timeAgo(a.timestamp)}</small></div></div>`;
}

function render(){
 const st=state.stats;
 const h1=document.querySelector('.page-head h1');if(h1)h1.textContent=`${greeting()}, ${state.users?.coordinator?.name||'Coordinator'}`;
 $('#stats').innerHTML=[['Deliveries scheduled',st.meals_scheduled,'◉'],['Active routes',st.routes_active,'⌁'],['Completed',st.routes_complete,'✓'],['Needs attention',st.attention_items ?? (st.open_issues+st.routes_at_risk),'!']].map(x=>`<div class="stat"><div class="stat-top"><span class="stat-label">${x[0]}</span><span class="mini-icon">${x[2]}</span></div><strong>${x[1]}</strong></div>`).join('');
 const routes=Object.values(state.routes).filter(r=>`${r.name} ${state.volunteers[r.volunteer_id]?.name||''}`.toLowerCase().includes(filter.toLowerCase()));
 $('#routeList').innerHTML=routes.map(routeRow).join('')||`<div class="empty">No routes match your search.</div>`;
 const open=state.issues.filter(i=>i.status==='open').sort((a,b)=>severityRank(b.severity)-severityRank(a.severity)||new Date(a.created_at)-new Date(b.created_at));
 const riskRoutes=Object.values(state.routes).filter(r=>['at_risk','uncovered'].includes(r.status) && !open.some(i=>i.route_id===r.id));
 const attentionTotal=open.length+riskRoutes.length; $('#attentionCount').innerHTML=attentionTotal?`<span class="badge b-needs_review">${attentionTotal}</span>`:'';
 const issueHtml=open.map(i=>{const r=state.routes[i.route_id], stop=i.stop_id?state.stops[i.stop_id]:null, protocol=stop?.outcome?state.protocols[stop.outcome]:null;return `<div class="attention-item ${i.severity==='high'?'high':''}"><div class="attention-top"><div><div class="attention-title">${esc(stop?.recipient||r.name)}</div><div class="sub">${esc(r.name)}${stop?` · Stop ${stop.sequence}`:''} · ${timeAgo(i.created_at)}</div></div><span class="severity severity-${esc(i.severity)}">${esc(i.severity)}</span></div><p>${esc(i.reason)}</p><div class="attention-facts"><div><span>Next action</span><strong>${esc(issueActionLabel(i))}</strong></div><div><span>Escalates to</span><strong>${esc(protocol?.escalation_target||'Coordinator')}</strong></div><div><span>Route impact</span><strong>${state.route_summaries[i.route_id]?.pending||0} stop(s) still pending</strong></div></div><button class="btn btn-primary btn-sm" data-review-issue="${i.id}">${esc(issueActionLabel(i))}</button></div>`}).join('');
 const riskHtml=riskRoutes.map(routeAttention).join('');
 $('#attentionList').innerHTML=attentionTotal?(issueHtml+riskHtml):`<div class="empty">Everything that needs a person is clear right now.</div>`;
 const visible=state.activity.filter(a=>a.actor!=='human_event' && ['coverage_restored','route_reconciled','route_complete','volunteer_reminder_sent','routine_confirmation','route_confirmed','coordinator_reassignment'].includes(a.event_type)).slice(0,6);
 $('#handled').innerHTML=visible.length?visible.map(handledStory).join(''):`<div class="empty">Porchlight’s resolved work will appear here.</div>`;
 document.querySelectorAll('[data-route]').forEach(b=>b.onclick=()=>openRoute(b.dataset.route));
 document.querySelectorAll('[data-review-issue]').forEach(b=>b.onclick=()=>openIssueReview(b.dataset.reviewIssue));
 document.querySelectorAll('[data-route-attn]').forEach(b=>b.onclick=()=>openRoute(b.dataset.routeAttn));
 document.querySelectorAll('[data-remind]').forEach(b=>b.onclick=async()=>{b.disabled=true;b.textContent='Sending…';try{await api(`/api/routes/${b.dataset.remind}/contact-assigned`,{method:'POST'});toast('Reminder recorded.');await refresh();}catch(e){toast(e.message,true);b.disabled=false;b.textContent='Send reminder'}});
}

function openIssueReview(issueId){
 const issue=state.issues.find(i=>i.id===issueId);if(!issue)return;
 const route=state.routes[issue.route_id];const stop=issue.stop_id?state.stops[issue.stop_id]:null;
 const outcome=stop?.outcome?humanStatus(stop.outcome):'Route issue';
 const note=stop?.outcome_note||'No volunteer note was recorded.';
 const protocolKey=stop?.outcome;const protocol=protocolKey?state.protocols[protocolKey]:null;
 const steps=protocol?`<div class="detail-block"><h3>Approved protocol</h3><ol class="review-steps">${protocol.ordered_steps.map(x=>`<li>${esc(x)}</li>`).join('')}</ol><div class="sub">Volunteer marked this protocol complete before the issue was raised.</div></div>`:'';
 $('#drawerRoot').innerHTML=`<div class="drawer-backdrop" id="backdrop"><aside class="drawer"><div class="drawer-head"><div><div class="sub">${esc(route.name)}${stop?` · Stop ${stop.sequence}`:''} · ${timeAgo(issue.created_at)}</div><h2>${esc(stop?.recipient||route.name)}</h2><div style="margin-top:8px"><span class="severity severity-${esc(issue.severity)}">${esc(issue.severity)} priority</span></div></div><button class="close" id="closeDrawer" aria-label="Close">×</button></div><div class="detail-block"><h3>${esc(outcome)}</h3><p>${esc(issue.reason)}</p><div class="decision-box"><span>Human decision</span><strong>${esc(issueActionLabel(issue))}</strong><small>${esc(protocol?.escalation_target||'Coordinator')} owns the decision; Porchlight only carries the protocol and evidence forward.</small></div></div>${stop?`<div class="detail-block"><h3>Volunteer’s factual note</h3><p>${esc(note)}</p><div class="sub">No diagnosis or welfare inference is made by Porchlight.</div></div>`:''}${steps}<div class="review-actions"><button class="btn btn-primary" id="ackIssue">Acknowledge & close review</button><button class="btn btn-secondary" id="openIssueRoute">Open route</button></div></aside></div>`;
 $('#closeDrawer').onclick=()=>$('#drawerRoot').innerHTML='';$('#backdrop').onclick=e=>{if(e.target.id==='backdrop')$('#drawerRoot').innerHTML=''};
 $('#openIssueRoute').onclick=()=>openRoute(issue.route_id);
 $('#ackIssue').onclick=async()=>{const b=$('#ackIssue');b.disabled=true;b.textContent='Acknowledging…';try{await api(`/api/issues/${issueId}/acknowledge`,{method:'POST'});toast('Review acknowledged.');$('#drawerRoot').innerHTML='';await refresh()}catch(e){toast(e.message,true);b.disabled=false;b.textContent='Acknowledge & close review'}};
}

function stopOutcome(x){return x.outcome?`<span class="stop-outcome ${x.outcome==='delivered'?'good':'exception'}">${esc(humanStatus(x.outcome))}</span>`:`<span class="stop-outcome pending">Pending</span>`}
function routeSchematic(stops){return `<div class="route-schematic">${stops.map((x,i)=>`<div class="route-node ${x.outcome==='delivered'?'done':x.outcome?'exception':'pending'}"><div class="node-dot">${x.outcome==='delivered'?'✓':x.sequence}</div><div class="node-copy"><strong>${esc(x.recipient)}</strong><span>${esc(x.address)}</span></div>${i<stops.length-1?'<div class="node-line"></div>':''}</div>`).join('')}</div>`}

async function openRoute(id){
 const data=await api(`/api/routes/${id}`);const r=data.route,v=data.volunteer,s=data.summary;
 const comms=data.communications.length?data.communications.map(c=>`<div class="comm"><div class="comm-top"><strong>${esc(c.volunteer_name)}</strong><span class="comm-status ${esc(c.status)}">${esc(humanStatus(c.status))}</span></div><p>${esc(c.message)}</p><span class="sub">${esc(c.channel)} · ${timeAgo(c.sent_at)}</span></div>`).join(''):`<div class="empty compact">No communications recorded for this route.</div>`;
 const stops=data.stops.map(x=>`<div class="stop-mini"><div class="stop-num">${x.sequence}</div><div class="grow"><strong>${esc(x.recipient)}</strong><div class="sub">${esc(x.address)}</div></div>${stopOutcome(x)}</div>`).join('');
 const isRisk=['at_risk','uncovered'].includes(r.status);
 const timing=`<div class="route-timing"><div><span>Scheduled</span><strong>${r.start_time}</strong></div><div><span>Actual start</span><strong>${r.started_at?clock(r.started_at):'Not started'}</strong></div><div><span>Est. finish</span><strong>${r.estimated_finish||'—'}</strong></div>${r.overdue_minutes?`<div class="overdue"><span>Delay</span><strong>${r.overdue_minutes} min</strong></div>`:''}</div>`;
 const attention=isRisk?`<div class="route-alert"><div><strong>${esc(r.risk_note||'Route needs attention')}</strong><span>${r.overdue_minutes?`${r.overdue_minutes} minutes past scheduled start · `:''}${esc(r.last_contact_status||'No reminder sent yet')}</span></div><div class="action-row"><button class="btn btn-primary btn-sm" id="remindRoute">Send reminder</button><button class="btn btn-secondary btn-sm" id="unavailableBtn">Mark unavailable & find replacement</button></div></div>`:'';
 const next=nextPending(r.id); const nav=next?`<a class="btn btn-secondary btn-sm" target="_blank" rel="noopener" href="${esc(mapsUrl(next.address))}">↗ Open next stop in Maps</a>`:'';
 $('#drawerRoot').innerHTML=`<div class="drawer-backdrop" id="backdrop"><aside class="drawer route-workspace"><div class="drawer-head"><div><div class="sub">Today · ${r.start_time}</div><h2>${esc(r.name)}</h2><div class="status-stack" style="margin-top:8px">${statusBadge(s.lifecycle)}${s.attention?statusBadge(s.attention):''}</div></div><button class="close" id="closeDrawer" aria-label="Close">×</button></div>
 ${attention}
 <div class="detail-block"><div class="section-inline"><h3>Route overview</h3>${nav}</div>${timing}<div class="detail-grid detail-grid-3"><div class="kv"><span>Volunteer</span><strong>${esc(v?.name||'Unassigned')}</strong></div><div class="kv"><span>Progress</span><strong>${s.delivered+s.exceptions} of ${s.total}</strong></div><div class="kv"><span>Human issues</span><strong>${s.open_issues}</strong></div></div></div>
 <div class="detail-block"><div class="section-inline"><h3>Route sequence</h3><span class="sub">${s.pending} pending · ${s.exceptions} exception${s.exceptions===1?'':'s'}</span></div>${routeSchematic(data.stops)}</div>
 <div class="detail-block"><div class="section-inline"><h3>Stops</h3><span class="sub">Operational list</span></div>${stops}</div>
 <div class="detail-block"><div class="section-inline"><h3>Volunteer communications</h3><button class="btn btn-ghost btn-sm" id="sendComm">Send reminder</button></div>${comms}</div>
 <details class="detail-block secondary-actions"><summary>Coordinator actions</summary><div class="secondary-body"><p class="sub">Manual reassignment is an override. Confirm availability with the volunteer before assigning.</p><select class="field" id="assignSelect"><option value="">Choose approved volunteer…</option>${Object.values(state.volunteers).filter(x=>x.active&&x.eligible_routes.includes(r.id)&&x.id!==r.volunteer_id).map(x=>`<option value="${x.id}">${esc(x.name)}${x.available?'':' · unavailable'}</option>`).join('')}</select><button class="btn btn-secondary" id="assignBtn" style="margin-top:10px">Reassign route</button></div></details>
 </aside></div>`;
 $('#closeDrawer').onclick=()=>$('#drawerRoot').innerHTML='';$('#backdrop').onclick=e=>{if(e.target.id==='backdrop')$('#drawerRoot').innerHTML=''};
 async function sendReminder(btn){btn.disabled=true;btn.textContent='Sending…';try{await api(`/api/routes/${r.id}/contact-assigned`,{method:'POST'});toast('Reminder recorded for assigned volunteer.');await refresh();await openRoute(r.id)}catch(e){toast(e.message,true);btn.disabled=false;btn.textContent='Send reminder'}}
 const rb=$('#remindRoute');if(rb)rb.onclick=()=>sendReminder(rb);const sc=$('#sendComm');if(sc)sc.onclick=()=>sendReminder(sc);
 const ub=$('#unavailableBtn');if(ub)ub.onclick=async()=>{if(!confirm(`Mark ${v?.name||'this volunteer'} unavailable and let Porchlight coordinate approved backups?`))return;ub.disabled=true;ub.textContent='Porchlight is coordinating…';try{await api(`/api/routes/${r.id}/volunteer-unavailable`,{method:'POST',body:JSON.stringify({reason:'Coordinator confirmed the volunteer cannot cover this route.'})});toast('Porchlight restored or escalated route coverage.');$('#drawerRoot').innerHTML='';await refresh();}catch(e){toast(e.message,true);ub.disabled=false;ub.textContent='Mark unavailable & find replacement'}};
 const ab=$('#assignBtn');if(ab)ab.onclick=async()=>{const volunteer_id=$('#assignSelect').value;if(!volunteer_id){toast('Choose a volunteer first.',true);return}ab.disabled=true;try{await api(`/api/routes/${r.id}/assign`,{method:'POST',body:JSON.stringify({volunteer_id,reason:'Coordinator confirmed availability outside Porchlight.'})});toast('Route reassigned.');$('#drawerRoot').innerHTML='';await refresh();}catch(e){toast(e.message,true);ab.disabled=false}};
}

async function refresh(){try{state=await api('/api/state');render();if(initialRoute&&state.routes[initialRoute]){const id=initialRoute;initialRoute=null;openRoute(id)}}catch(e){toast(`Porchlight could not refresh operations: ${e.message}`,true)}}
$('#search').oninput=e=>{filter=e.target.value;render()};refresh();setInterval(refresh,30000);
