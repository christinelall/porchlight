import {$,api,esc,statusBadge} from '/static/shared.js';
let state=null,filter='';
function render(){
 const assignments={};Object.values(state.routes).forEach(r=>{if(r.volunteer_id)assignments[r.volunteer_id]=r});
 const vols=Object.values(state.volunteers).filter(v=>v.name.toLowerCase().includes(filter.toLowerCase()));
 $('#volunteerCards').innerHTML=vols.map(v=>{const r=assignments[v.id];return `<article class="volunteer-card"><div class="volunteer-card-top"><div class="avatar">${esc(v.name[0])}</div><div class="grow"><strong>${esc(v.name)}</strong><div class="sub">${esc(v.phone)}</div></div><span class="availability ${v.available?'available':'unavailable'}">${v.available?'Available':'Unavailable'}</span></div><div class="volunteer-stats"><div><span>Today</span><strong>${r?esc(r.name):'No route'}</strong></div><div><span>Reliability</span><strong>${v.reliability??'—'}%</strong></div></div>${r?`<div class="volunteer-route"><span class="sub">${r.start_time} · ${r.stop_ids.length} stops</span><a class="btn btn-ghost btn-sm" href="/coordinator?route=${r.id}">Open route</a></div>`:`<div class="volunteer-route"><span class="sub">Eligible: ${v.eligible_routes.length} route${v.eligible_routes.length===1?'':'s'}</span></div>`}</article>`}).join('')||`<div class="empty">No volunteers match your search.</div>`;
}
async function refresh(){state=await api('/api/state');render()}
$('#search').oninput=e=>{filter=e.target.value;render()};refresh();
