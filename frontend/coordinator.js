import {$,api,esc,timeAgo,humanStatus,statusBadge,toast} from '/static/shared.js';
let state=null; let filter='';
function routeRow(route){
  const s=state.route_summaries[route.id]; const v=state.volunteers[route.volunteer_id];
  return `<button class="route-row" data-route="${route.id}" style="width:100%;text-align:left">
    <div><div class="route-name">${esc(route.name)}</div><div class="sub">${esc(v?.name||'Unassigned')} · ${route.start_time} · ${s.total} stops</div><div class="progress"><span style="width:${s.percent}%"></span></div></div>
    <div class="route-meta hide-sm"><span class="sub">Progress</span><strong>${s.delivered+s.exceptions}/${s.total}</strong></div>
    <div class="route-meta hide-md"><span class="sub">Est. finish</span><strong>${route.estimated_finish||'—'}</strong></div>
    <div class="hide-sm">${statusBadge(route.status)}</div><div class="chev">›</div></button>`;
}
function render(){
 const st=state.stats;
 $('#stats').innerHTML=[['Meals scheduled',st.meals_scheduled,'◉'],['Active routes',st.routes_active,'⌁'],['Completed',st.routes_complete,'✓'],['Needs attention',st.open_issues+st.routes_at_risk,'!']].map(x=>`<div class="stat"><div class="stat-top"><span class="stat-label">${x[0]}</span><span class="mini-icon">${x[2]}</span></div><strong>${x[1]}</strong></div>`).join('');
 const routes=Object.values(state.routes).filter(r=>`${r.name} ${state.volunteers[r.volunteer_id]?.name||''}`.toLowerCase().includes(filter.toLowerCase()));
 $('#routeList').innerHTML=routes.map(routeRow).join('')||`<div class="empty">No routes match your search.</div>`;
 const open=state.issues.filter(i=>i.status==='open');
 const riskRoutes=Object.values(state.routes).filter(r=>['at_risk','uncovered'].includes(r.status) && !open.some(i=>i.route_id===r.id));
 const attentionTotal=open.length+riskRoutes.length; $('#attentionCount').innerHTML=attentionTotal?`<span class="badge b-needs_review">${attentionTotal}</span>`:'';
 const issueHtml=open.map(i=>{const r=state.routes[i.route_id], stop=i.stop_id?state.stops[i.stop_id]:null;return `<div class="attention-item ${i.severity==='high'?'high':''}"><div class="attention-top"><div><div class="attention-title">${esc(stop?.recipient||r.name)}</div><div class="sub">${esc(r.name)} · ${timeAgo(i.created_at)}</div></div><span class="badge b-needs_review">${esc(i.severity)}</span></div><p>${esc(i.reason)}</p><button class="btn btn-primary btn-sm" data-ack="${i.id}">Review & acknowledge</button></div>`}).join('');
 const riskHtml=riskRoutes.map(r=>`<div class="attention-item"><div class="attention-top"><div><div class="attention-title">${esc(r.name)}</div><div class="sub">Route coverage / start</div></div>${statusBadge(r.status)}</div><p>${esc(r.risk_note||'This route needs coordinator attention.')}</p><button class="btn btn-secondary btn-sm" data-route-attn="${r.id}">Review route</button></div>`).join('');
 $('#attentionList').innerHTML=attentionTotal?(issueHtml+riskHtml):`<div class="empty">Everything that needs a person is clear right now.</div>`;
 const visible=state.activity.filter(a=>['coverage_restored','backup_contacted','route_reconciled','route_complete','route_started','issue_acknowledged'].includes(a.event_type)).slice(0,6);
 $('#handled').innerHTML=visible.length?visible.map(a=>`<div class="timeline-item ${a.human_action_required?'attention':''}"><div class="timeline-dot"></div><div><strong>${esc(a.message)}</strong><small>${timeAgo(a.timestamp)}</small></div></div>`).join(''):`<div class="empty">Porchlight’s resolved work will appear here.</div>`;
 document.querySelectorAll('[data-route]').forEach(b=>b.onclick=()=>openRoute(b.dataset.route));
 document.querySelectorAll('[data-ack]').forEach(b=>b.onclick=async()=>{try{await api(`/api/issues/${b.dataset.ack}/acknowledge`,{method:'POST'});toast('Item acknowledged.');await refresh();}catch(e){toast(e.message,true)}});
 document.querySelectorAll('[data-route-attn]').forEach(b=>b.onclick=()=>openRoute(b.dataset.routeAttn));
}
async function openRoute(id){
 const data=await api(`/api/routes/${id}`);const r=data.route,v=data.volunteer,s=data.summary;
 const comms=data.communications.length?data.communications.map(c=>`<div class="comm"><div class="comm-top"><strong>${esc(c.volunteer_name)}</strong><span>${statusBadge(c.status==='accept'?'confirmed':c.status==='decline'?'scheduled':c.status)}</span></div><p>${esc(c.message)}</p><span class="sub">${esc(c.channel)} · ${timeAgo(c.sent_at)}</span></div>`).join(''):`<div class="sub">No backup outreach on this route.</div>`;
 const stops=data.stops.map(x=>`<div class="stop-mini"><div class="stop-num">${x.sequence}</div><div class="grow"><strong>${esc(x.recipient)}</strong><div class="sub">${esc(x.address)}</div></div><span class="sub">${esc(x.outcome?humanStatus(x.outcome):'Pending')}</span></div>`).join('');
 $('#drawerRoot').innerHTML=`<div class="drawer-backdrop" id="backdrop"><aside class="drawer"><div class="drawer-head"><div><div class="sub">Today · ${r.start_time}</div><h2>${esc(r.name)}</h2><div style="margin-top:8px">${statusBadge(r.status)}</div></div><button class="close" id="closeDrawer">×</button></div>
 <div class="detail-block"><h3>Route overview</h3><div class="detail-grid"><div class="kv"><span>Volunteer</span><strong>${esc(v?.name||'Unassigned')}</strong></div><div class="kv"><span>Progress</span><strong>${s.delivered+s.exceptions} of ${s.total}</strong></div><div class="kv"><span>Estimated finish</span><strong>${r.estimated_finish||'—'}</strong></div><div class="kv"><span>Open issues</span><strong>${s.open_issues}</strong></div></div>${r.risk_note?`<div class="attention-item" style="margin-top:14px"><strong>${esc(r.risk_note)}</strong></div>`:''}</div>
 <div class="detail-block"><h3>Stops</h3>${stops}</div>
 <div class="detail-block"><h3>Volunteer communications</h3>${comms}</div>
 ${r.id==='r3'&&r.status!=='complete'?`<div class="detail-block"><h3>Coverage</h3><p class="sub">If the assigned volunteer reports they cannot make the route, Porchlight can coordinate approved backups automatically.</p><button class="btn btn-secondary" id="unavailableBtn">Volunteer unavailable</button></div>`:''}
 <div class="detail-block"><h3>Coordinator reassignment</h3><p class="sub">Use only when you have separately confirmed the volunteer can take this route.</p><select class="field" id="assignSelect"><option value="">Choose approved volunteer…</option>${Object.values(state.volunteers).filter(x=>x.active&&x.eligible_routes.includes(r.id)&&x.id!==r.volunteer_id).map(x=>`<option value="${x.id}">${esc(x.name)}${x.available?'':' · unavailable'}</option>`).join('')}</select><button class="btn btn-secondary" id="assignBtn" style="margin-top:10px">Assign volunteer</button></div>
 </aside></div>`;
 $('#closeDrawer').onclick=()=>$('#drawerRoot').innerHTML='';$('#backdrop').onclick=e=>{if(e.target.id==='backdrop')$('#drawerRoot').innerHTML=''};
 const ub=$('#unavailableBtn');if(ub)ub.onclick=async()=>{ub.disabled=true;ub.textContent='Porchlight is coordinating…';try{await api('/api/routes/r3/volunteer-unavailable',{method:'POST',body:JSON.stringify({reason:'Coordinator received an availability change.'})});toast('Porchlight restored or escalated route coverage.');$('#drawerRoot').innerHTML='';await refresh();}catch(e){toast(e.message,true);ub.disabled=false;ub.textContent='Volunteer unavailable'}};
 const ab=$('#assignBtn');if(ab)ab.onclick=async()=>{const volunteer_id=$('#assignSelect').value;if(!volunteer_id){toast('Choose a volunteer first.',true);return}ab.disabled=true;try{await api(`/api/routes/${r.id}/assign`,{method:'POST',body:JSON.stringify({volunteer_id,reason:'Coordinator confirmed availability outside Porchlight.'})});toast('Route reassigned.');$('#drawerRoot').innerHTML='';await refresh();}catch(e){toast(e.message,true);ab.disabled=false}};
}
async function refresh(){state=await api('/api/state');render()}
$('#search').oninput=e=>{filter=e.target.value;render()};refresh();setInterval(refresh,30000);
