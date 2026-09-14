export const $ = (sel, root=document) => root.querySelector(sel);
export const $$ = (sel, root=document) => [...root.querySelectorAll(sel)];
export async function api(path, options={}){
  const init={headers:{'Content-Type':'application/json'},...options};
  const res=await fetch(path,init);
  let data={}; try{data=await res.json()}catch{}
  if(!res.ok) throw new Error(data.detail||`Request failed (${res.status})`);
  return data;
}
export function esc(value=''){return String(value).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
export function timeAgo(iso){
  if(!iso)return '';
  const mins=Math.max(0,Math.round((Date.now()-new Date(iso).getTime())/60000));
  if(mins<1)return 'just now'; if(mins<60)return `${mins} min ago`; const h=Math.floor(mins/60); if(h<24)return `${h}h ago`; return new Date(iso).toLocaleDateString();
}
export function clock(iso){return iso?new Date(iso).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}):'';}
export function initials(name=''){return name.split(/\s+/).map(s=>s[0]).join('').slice(0,2).toUpperCase();}
export function humanStatus(s=''){return s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());}
export function toast(message,error=false){const old=$('.toast');if(old)old.remove();const el=document.createElement('div');el.className='toast'+(error?' error':'');el.textContent=message;document.body.appendChild(el);setTimeout(()=>el.remove(),4500);}
export function statusBadge(status){return `<span class="badge b-${esc(status)}">${esc(humanStatus(status))}</span>`;}
