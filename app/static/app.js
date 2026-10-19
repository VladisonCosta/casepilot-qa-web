const state = { token: sessionStorage.getItem('casepilot_token'), role: '', email: '', tickets: [] };
const $ = (id) => document.getElementById(id);
const statusNames = { OPEN:'Aberto', IN_PROGRESS:'Em andamento', RESOLVED:'Resolvido' };
const priorityNames = { LOW:'Baixa', MEDIUM:'Média', HIGH:'Alta' };
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let toastTimer;
function toast(message) { const el=$('toast'); el.textContent=message; el.hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.hidden=true,3200); }
async function api(path, options={}) {
  const headers = {...(options.body?{'Content-Type':'application/json'}:{}), ...(state.token?{Authorization:`Bearer ${state.token}`}:{})};
  const response = await fetch(path,{...options, headers});
  if (response.status === 401 && path !== '/api/login') { signOut(false); throw new Error('Sessão expirada. Entre novamente.'); }
  let body=null; try { body=await response.json(); } catch(e) { /* 204 */ }
  if (!response.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : 'Erro na operação');
  return body;
}
function signOut(request=true) { if(request && state.token) api('/api/logout',{method:'POST'}).catch(()=>{}); state.token=''; sessionStorage.removeItem('casepilot_token'); $('dashboard-view').hidden=true; $('login-view').hidden=false; }
async function showDashboard() { $('login-view').hidden=true; $('dashboard-view').hidden=false; $('account-role').textContent=state.role==='AGENT'?'Agente de suporte':'Visualizador'; $('account-email').textContent=state.email; await loadTickets(); }
async function loadTickets() {
  const search=$('search').value.trim(), status=$('status-filter').value;
  const result=await api(`/api/tickets?search=${encodeURIComponent(search)}&status=${encodeURIComponent(status)}`);
  state.tickets=result.items;
  const tbody=$('ticket-list'); tbody.replaceChildren();
  for(const ticket of result.items){
    const row=document.createElement('tr'); row.setAttribute('data-testid','ticket-row');
    const safeTitle=escapeHtml(ticket.title), safeDescription=escapeHtml(ticket.description);
    const date=new Date(ticket.created_at).toLocaleDateString('pt-BR');
    const choices=Object.entries(statusNames).map(([key,value])=>`<option value="${key}" ${ticket.status===key?'selected':''}>${value}</option>`).join('');
    row.innerHTML=`<td><strong>${safeTitle}</strong><small>#${ticket.id} · ${safeDescription.slice(0,75)}</small></td><td><span class="pill ${ticket.priority}">${priorityNames[ticket.priority]}</span></td><td><span class="pill ${ticket.status}" data-testid="ticket-status">${statusNames[ticket.status]}</span></td><td>${date}</td><td>${state.role==='AGENT'?`<select class="status-select" aria-label="Alterar status de ${safeTitle}" data-testid="status-change" data-id="${ticket.id}">${choices}</select>`:'Somente leitura'}</td>`;
    tbody.append(row);
  }
  $('empty-state').hidden=result.total!==0;
  $('table-footer').textContent=`Exibindo ${result.total} chamado(s)`;
  $('metric-total').textContent=result.total;
  $('metric-open').textContent=result.items.filter(x=>x.status==='OPEN').length;
  $('metric-progress').textContent=result.items.filter(x=>x.status==='IN_PROGRESS').length;
  $('metric-resolved').textContent=result.items.filter(x=>x.status==='RESOLVED').length;
}
$('login-form').addEventListener('submit',async (event)=>{
  event.preventDefault(); $('login-error').hidden=true;
  try { const res=await api('/api/login',{method:'POST',body:JSON.stringify({email:$('email').value,password:$('password').value})});
    state.token=res.token; state.role=res.role; state.email=res.email; sessionStorage.setItem('casepilot_token',res.token); await showDashboard();
  } catch(err){$('login-error').textContent=err.message; $('login-error').hidden=false;}
});
$('logout').addEventListener('click',()=>signOut());
const openModal=()=>{ $('modal-backdrop').hidden=false; $('ticket-title').focus(); };
const closeModal=()=>{ $('modal-backdrop').hidden=true; $('ticket-form').reset(); };
$('new-ticket').addEventListener('click',openModal);
$('close-modal').addEventListener('click',closeModal);
$('cancel-modal').addEventListener('click',closeModal);
$('ticket-form').addEventListener('submit',async (event)=>{
 event.preventDefault();
 try { await api('/api/tickets',{method:'POST',body:JSON.stringify({title:$('ticket-title').value,description:$('ticket-description').value,priority:$('ticket-priority').value})}); closeModal(); await loadTickets(); toast('Chamado criado com sucesso!'); }
 catch(err){toast(err.message);}
});
$('ticket-list').addEventListener('change',async(event)=>{
 const select=event.target.closest('[data-testid="status-change"]'); if(!select)return;
 try{await api(`/api/tickets/${select.dataset.id}/status`,{method:'PATCH',body:JSON.stringify({status:select.value})}); await loadTickets(); toast('Status atualizado com sucesso!');}catch(err){toast(err.message); await loadTickets();}
});
let searchTimeout;
$('search').addEventListener('input',()=>{clearTimeout(searchTimeout); searchTimeout=setTimeout(()=>loadTickets().catch(err=>toast(err.message)),180);});
$('status-filter').addEventListener('change',()=>loadTickets().catch(err=>toast(err.message)));
if(state.token){ // Token de sessão recuperado: novo login para determinar papel sem persistir credenciais.
 state.token=''; sessionStorage.removeItem('casepilot_token');
}
