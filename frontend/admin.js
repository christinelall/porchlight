import {$,api,esc,statusBadge,timeAgo,humanStatus,toast} from '/static/shared.js';
let state=null;

function integrationStatus(x){return `<div class="integration-card"><div><strong>${esc(x.provider)}</strong><span>${esc(humanStatus(x.status))}</span></div><span class="integration-dot ${x.status==='enabled'||x.status==='live'?'on':'demo'}"></span></div>`}
function metric(label,value,detail=''){return `<div class="eval-card"><span>${esc(label)}</span><strong>${esc(value)}</strong>${detail?`<small>${esc(detail)}</small>`:''}</div>`}
function scenarioCard(name,title,copy,steps){return `<button class="scenario-card" data-scenario="${name}"><div><strong>${esc(title)}</strong><p>${esc(copy)}</p></div><small>${esc(steps)}</small><span>Load scenario →</span></button>`}

function render(){
 const s=state,rt=s.strands,m=s.agent_metrics||{};
 $('#diag').innerHTML=`<div class="diag-box"><span>Agent orchestration</span><strong>${rt.enabled?'Strands enabled':'Fallback / disabled'}</strong></div><div class="diag-box"><span>Model provider</span><strong>${esc(rt.provider)}</strong></div><div class="diag-box"><span>Model</span><strong>${esc(rt.model_id)}</strong></div>`;
 $('#evalMetrics').innerHTML=[
   metric('Workflows',String(m.workflows_total||0),`${m.workflows_succeeded||0} succeeded · ${m.workflows_failed||0} failed`),
   metric('Success rate',`${m.success_rate||0}%`,'Completed agent workflows'),
   metric('Tool calls',String(m.tool_calls||0),`${m.avg_tools_per_workflow||0} avg / workflow`),
   metric('Verified outcomes',String(m.verified_postconditions||0),'Postcondition checked in application state'),
   metric('Human handoffs',String(m.human_handoffs||0),'Safety or operational decisions surfaced'),
   metric('Declines handled',String(m.backup_declines_handled||0),'Agent continued after a backup declined'),
 ].join('');
 $('#guardrails').innerHTML=[
   ['Explicit acceptance','A backup cannot be assigned until the contact tool records an explicit acceptance.'],
   ['Human safety boundary','Welfare and no-answer events follow an approved protocol and remain human-owned.'],
   ['No false completion','A route cannot close while any scheduled stop is unaccounted for or an issue is open.'],
   ['Factual evidence only','Safety-sensitive outcomes require a short factual note; diagnosis and inference are excluded.'],
 ].map(([t,d])=>`<div class="guardrail"><span>✓ Enforced</span><strong>${esc(t)}</strong><p>${esc(d)}</p></div>`).join('');
 const runs=s.agent_runs||[];
 $('#agentRuns').innerHTML=runs.length?runs.slice(0,20).map(r=>`<button class="agent-run" data-run="${r.id}"><div><strong>${esc(humanStatus(r.workflow))}</strong><span>${esc(s.routes[r.route_id]?.name||r.route_id)} · ${timeAgo(r.started_at)}</span></div><div><span class="run-status ${r.status}">${esc(humanStatus(r.status))}</span><strong>${r.tool_events?.length||0} tools</strong></div><div><span>Postcondition</span><strong>${r.postcondition?esc(humanStatus(r.postcondition)):r.status==='running'?'Pending':'Not recorded'}</strong></div><div><span>Duration</span><strong>${r.duration_ms==null?'—':`${(r.duration_ms/1000).toFixed(1)}s`}</strong></div></button>`).join(''):`<div class="empty">Run a live Porchlight workflow and its evidence will appear here.</div>`;

 const current=s.demo?.scenario||'baseline';
 $('#scenarioBadge').innerHTML=`<span class="badge b-confirmed">${esc(s.demo?.label||'Sample day')}</span>`;
 $('#scenarioGrid').innerHTML=[
   scenarioCard('baseline','Sample delivery day','A balanced day with one route at risk and normal delivery progress.','Best for general product walkthroughs.'),
   scenarioCard('backup_retry','Backup retry','Andre cannot cover East End. Camila declines; Noah accepts.','Open East End and mark Andre unavailable.'),
   scenarioCard('coverage_gap','Coverage gap','All approved East End backups decline, forcing a human coverage handoff.','Tests safe failure and escalation.'),
   scenarioCard('no_answer','No-answer handoff','George Town is already underway and Mary is the next pending stop.','Open /volunteer?route=r3 and report No Answer.'),
 ].join('');
 document.querySelectorAll('[data-scenario]').forEach(b=>{if(b.dataset.scenario===current)b.classList.add('selected');b.onclick=()=>loadScenario(b.dataset.scenario)});

 const org=s.organization||{};
 $('#orgSettings').innerHTML=`<div class="settings-card"><label>Coordinator name</label><input id="orgName" class="field" value="${esc(org.coordinator_name||'')}"><label>Coordinator phone</label><input id="orgPhone" class="field" value="${esc(org.coordinator_phone||'')}"><label>Emergency guidance</label><textarea id="orgEmergency" class="field">${esc(org.emergency_note||'')}</textarea><button class="btn btn-primary btn-sm" id="saveOrg">Save settings</button></div>`;
 $('#integrationCards').innerHTML=Object.values(s.integrations||{}).map(integrationStatus).join('');
 $('#saveOrg').onclick=async()=>{try{await api('/api/admin/organization',{method:'PUT',body:JSON.stringify({coordinator_name:$('#orgName').value.trim(),coordinator_phone:$('#orgPhone').value.trim(),emergency_note:$('#orgEmergency').value.trim()})});toast('Organization settings saved.');await refresh()}catch(e){toast(e.message,true)}};
 $('#volRows').innerHTML=Object.values(s.volunteers).map(v=>`<tr><td><strong>${esc(v.name)}</strong></td><td>${statusBadge(v.available?'confirmed':'at_risk')}</td><td>${esc(v.eligible_routes.join(', '))}</td><td>${v.reliability||'—'}%</td><td>${esc(v.phone||'—')}</td><td><button class="btn btn-ghost btn-sm" data-edit-vol="${v.id}">Edit</button></td></tr>`).join('');
 $('#protocolCards').innerHTML=Object.values(s.protocols).map(p=>`<div class="route-row protocol-row"><div><div class="route-name">${esc(p.title)}</div><div class="sub">${p.ordered_steps.length} defined steps · ${esc(p.escalation_target)}</div></div><div>${statusBadge(p.requires_acknowledgement?'needs_review':'confirmed')}</div><div class="route-meta"><span class="sub">Severity</span><strong>${esc(p.severity)}</strong></div><div class="route-meta"><span class="sub">Outcome</span><strong>${p.requires_acknowledgement?'Human review':'Record & continue'}</strong></div><button class="btn btn-ghost btn-sm" data-edit-protocol="${esc(p.exception_type)}">Edit</button></div>`).join('');
 $('#auditRows').innerHTML=s.audit.slice(0,60).map(a=>`<div class="audit-row"><div class="sub">${timeAgo(a.timestamp)}</div><div><strong>${esc(a.actor)}</strong></div><div><strong>${esc(humanStatus(a.action))}</strong><div class="sub">${esc(a.detail)}</div></div></div>`).join('');
 document.querySelectorAll('[data-edit-vol]').forEach(b=>b.onclick=()=>editVolunteer(b.dataset.editVol));
 document.querySelectorAll('[data-edit-protocol]').forEach(b=>b.onclick=()=>editProtocol(b.dataset.editProtocol));
 document.querySelectorAll('[data-run]').forEach(b=>b.onclick=()=>openRun(b.dataset.run));
}

async function loadScenario(name){
 if(!confirm('Loading a scenario resets the sample data for this local demo. Continue?'))return;
 try{await api(`/api/admin/scenarios/${name}`,{method:'POST'});toast('Scenario loaded. Use the normal coordinator or volunteer screens to continue.');await refresh()}catch(e){toast(e.message,true)}
}

function drawer(title,body){$('#drawerRoot').innerHTML=`<div class="drawer-backdrop" id="backdrop"><aside class="drawer"><div class="drawer-head"><h2>${esc(title)}</h2><button class="close" id="closeDrawer">×</button></div>${body}</aside></div>`;$('#closeDrawer').onclick=()=>$('#drawerRoot').innerHTML='';$('#backdrop').onclick=e=>{if(e.target.id==='backdrop')$('#drawerRoot').innerHTML=''} }

function openRun(id){
 const r=state.agent_runs.find(x=>x.id===id);if(!r)return;
 const route=state.routes[r.route_id];
 const tools=(r.tool_events||[]).map((t,i)=>`<div class="tool-evidence ${t.ok?'':'blocked'}"><span>${i+1}</span><div><strong>${esc(humanStatus(t.tool))}</strong><p>${esc(t.detail)}</p></div><small>${t.ok?'completed':'blocked'}</small></div>`).join('')||'<div class="empty compact">No tool calls recorded.</div>';
 drawer(humanStatus(r.workflow),`<div class="detail-block"><div class="detail-grid detail-grid-3"><div class="kv"><span>Route</span><strong>${esc(route?.name||r.route_id)}</strong></div><div class="kv"><span>Status</span><strong>${esc(humanStatus(r.status))}</strong></div><div class="kv"><span>Model</span><strong>${esc(r.model_id||'—')}</strong></div></div></div><div class="detail-block"><h3>Tool evidence</h3>${tools}</div><div class="detail-block"><h3>Verified operational result</h3><div class="decision-box"><span>Postcondition</span><strong>${r.postcondition?esc(humanStatus(r.postcondition)):'Not recorded'}</strong><small>${r.postcondition_verified===true?'Verified against Porchlight application state.':r.postcondition_verified===false?'Postcondition check failed.':'No postcondition check was recorded for this run.'}</small></div></div>${r.error?`<div class="detail-block"><h3>Error</h3><p>${esc(r.error)}</p></div>`:''}<div class="detail-block"><h3>Privacy</h3><p class="sub">Porchlight stores workflow status, tool evidence and operational outcomes. Hidden model reasoning is not stored or displayed.</p></div>`);
}

function editVolunteer(id){
 const v=state.volunteers[id];const routes=Object.values(state.routes);
 drawer(`Edit ${v.name}`,`<div class="detail-block"><label class="toggle-row"><input type="checkbox" id="volActive" ${v.active?'checked':''}><span><strong>Active volunteer</strong><small>Can be scheduled for approved routes</small></span></label><label class="toggle-row"><input type="checkbox" id="volAvailable" ${v.available?'checked':''}><span><strong>Available today</strong><small>Can be considered for backup coverage</small></span></label></div><div class="detail-block"><h3>Approved routes</h3><div class="check-grid">${routes.map(r=>`<label><input type="checkbox" data-route-check value="${r.id}" ${v.eligible_routes.includes(r.id)?'checked':''}> ${esc(r.name)}</label>`).join('')}</div></div><div class="detail-block"><label class="sub">Backup priority</label><input class="field" id="backupPriority" type="number" min="1" max="999" value="${v.backup_priority||100}"></div><button class="btn btn-primary" id="saveVolunteer" style="width:100%">Save volunteer</button>`);
 $('#saveVolunteer').onclick=async()=>{const eligible_routes=[...document.querySelectorAll('[data-route-check]:checked')].map(x=>x.value);try{await api(`/api/admin/volunteers/${id}`,{method:'PUT',body:JSON.stringify({active:$('#volActive').checked,available:$('#volAvailable').checked,eligible_routes,backup_priority:Number($('#backupPriority').value||100)})});toast('Volunteer profile updated.');$('#drawerRoot').innerHTML='';await refresh()}catch(e){toast(e.message,true)}};
}

function editProtocol(type){
 const p=state.protocols[type];
 drawer(`Edit ${p.title}`,`<div class="detail-block"><label class="sub">Protocol title</label><input id="protocolTitle" class="field" value="${esc(p.title)}"><label class="sub editor-label">Severity</label><select id="protocolSeverity" class="field"><option value="low" ${p.severity==='low'?'selected':''}>Low</option><option value="medium" ${p.severity==='medium'?'selected':''}>Medium</option><option value="high" ${p.severity==='high'?'selected':''}>High</option></select><label class="sub editor-label">Escalation target</label><input id="protocolTarget" class="field" value="${esc(p.escalation_target)}"><label class="sub editor-label">Volunteer note prompt</label><input id="protocolNotePrompt" class="field" value="${esc(p.note_prompt||'Describe only what you observed.')}"><label class="toggle-row editor-label"><input type="checkbox" id="protocolAck" ${p.requires_acknowledgement?'checked':''}><span><strong>Human acknowledgement required</strong><small>Keep the issue open until a coordinator reviews it</small></span></label></div><div class="detail-block"><div class="section-inline"><h3>Approved steps</h3><button class="btn btn-ghost btn-sm" id="addStep">+ Add step</button></div><div id="stepEditor">${p.ordered_steps.map((x,i)=>stepEditorRow(x,i)).join('')}</div></div><div class="detail-block protocol-preview"><h3>Volunteer preview</h3><div id="protocolPreview"></div></div><button class="btn btn-primary" id="saveProtocol" style="width:100%">Save protocol</button>`);
 wireProtocolEditor();
 $('#saveProtocol').onclick=async()=>{const ordered_steps=[...document.querySelectorAll('[data-step-input]')].map(x=>x.value.trim()).filter(Boolean);if(!ordered_steps.length){toast('Add at least one protocol step.',true);return}try{await api(`/api/admin/protocols/${type}`,{method:'PUT',body:JSON.stringify({title:$('#protocolTitle').value.trim(),ordered_steps,severity:$('#protocolSeverity').value,escalation_target:$('#protocolTarget').value.trim(),requires_acknowledgement:$('#protocolAck').checked,note_prompt:$('#protocolNotePrompt').value.trim()})});toast('Protocol updated.');$('#drawerRoot').innerHTML='';await refresh()}catch(e){toast(e.message,true)}};
}

function stepEditorRow(value='',i=0){return `<div class="step-edit" data-step-row><span>${i+1}</span><input class="field" data-step-input value="${esc(value)}" placeholder="Protocol step"><div class="step-actions"><button type="button" class="step-move" data-up title="Move up">↑</button><button type="button" class="step-move" data-down title="Move down">↓</button><button type="button" class="step-delete" data-delete title="Delete">×</button></div></div>`}
function renumberSteps(){document.querySelectorAll('[data-step-row]').forEach((row,i)=>row.querySelector(':scope > span').textContent=i+1);renderProtocolPreview()}
function renderProtocolPreview(){const box=$('#protocolPreview');if(!box)return;const steps=[...document.querySelectorAll('[data-step-input]')].map(x=>x.value.trim()).filter(Boolean);const severity=$('#protocolSeverity')?.value||'medium';box.innerHTML=`<div class="protocol"><div class="protocol-head"><strong>${esc($('#protocolTitle')?.value||'Protocol')}</strong><span class="severity severity-${esc(severity)}">${esc(severity)} priority</span></div><div class="protocol-steps">${steps.map((x,i)=>`<div class="protocol-step"><span></span><span class="step-number">${i+1}</span><span>${esc(x)}</span></div>`).join('')}</div><div class="what-next"><strong>What happens next</strong><span>${$('#protocolAck')?.checked?`This stays open until ${esc($('#protocolTarget')?.value||'a coordinator')} reviews it.`:'This is recorded and the route can continue without a human review.'}</span></div></div>`}
function wireProtocolEditor(){
 const editor=$('#stepEditor');
 const wireRows=()=>{editor.querySelectorAll('[data-up]').forEach(b=>b.onclick=()=>{const row=b.closest('[data-step-row]');if(row.previousElementSibling)editor.insertBefore(row,row.previousElementSibling);renumberSteps()});editor.querySelectorAll('[data-down]').forEach(b=>b.onclick=()=>{const row=b.closest('[data-step-row]');if(row.nextElementSibling)editor.insertBefore(row.nextElementSibling,row);renumberSteps()});editor.querySelectorAll('[data-delete]').forEach(b=>b.onclick=()=>{if(editor.children.length<=1){toast('A protocol needs at least one step.',true);return}b.closest('[data-step-row]').remove();renumberSteps()});editor.querySelectorAll('[data-step-input]').forEach(x=>x.oninput=renderProtocolPreview)};
 $('#addStep').onclick=()=>{editor.insertAdjacentHTML('beforeend',stepEditorRow('',editor.children.length));wireRows();renumberSteps()};
 ['protocolTitle','protocolSeverity','protocolTarget','protocolAck'].forEach(id=>{const el=$(`#${id}`);if(el)el.oninput=renderProtocolPreview});
 wireRows();renderProtocolPreview();
}

async function refresh(){try{state=await api('/api/state');render()}catch(e){toast(e.message,true)}}
refresh();
