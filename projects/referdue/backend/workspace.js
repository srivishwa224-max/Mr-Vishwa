const $ = id => document.getElementById(id);
async function api(path, data) {
  const response = await fetch('/api/' + path, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error);
  return result;
}
function list(id, items) {
  $(id).replaceChildren(...items.map(item => { const li=document.createElement('li'); li.textContent=item; return li; }));
}
async function details() {
  const id=$('selection').value;
  $('details').hidden=!id;
  if (!id) return;
  const prefix='workspaces/'+encodeURIComponent(id)+'/';
  const [partners,referrals,history]=await Promise.all(['partners','referrals','history'].map(name=>api(prefix+name)));
  list('partners',partners.items.map(row=>row[1]+' — '+row[2]+(row[3]?' · Payment reference: '+row[3]:'')));
  $('partner-selection').replaceChildren(...partners.items.map(row=>new Option(row[1],row[0])));
  $('statement-partner').replaceChildren(...partners.items.map(row=>new Option(row[1],row[0])));
  list('referrals',referrals.items.map(row=>row[2]));
  const selected=$('ledger-referral').value;
  $('ledger-referral').replaceChildren(...referrals.items.map(row=>new Option(row[2],row[0])));
  if(referrals.items.some(row=>row[0]===selected)) $('ledger-referral').value=selected;
  await ledger();
  list('history',history.items.map(row=>row[3]+' · '+row[1]));
}
async function refresh() {
  const prior=$('selection').value;
  const result=await api('workspaces');
  $('auth').hidden=true; $('workspace').hidden=false;
  $('selection').replaceChildren(...result.items.map(row=>new Option(row[1]+' ('+row[2]+')',row[0])));
  if(result.items.some(row=>row[0]===prior)) $('selection').value=prior;
  await details();
}
function bind(id, action) {
  $(id).addEventListener('submit',async event=>{
    event.preventDefault();
    const buttons=[...event.target.querySelectorAll('button')]; buttons.forEach(button=>button.disabled=true);
    try { await action(Object.fromEntries(new FormData(event.target)),event); $('message').textContent='Saved.'; event.target.reset(); }
    catch(error) { $('message').textContent=error.message; }
    finally { buttons.forEach(button=>button.disabled=false); }
  });
}
bind('login',async (data,event)=>{ await api(event.submitter.value,data); await refresh(); });
bind('new-workspace',async data=>{await api('workspaces',data); await refresh();});
for(const [id,resource] of [['partner','partners'],['member','members']]) bind(id,async data=>{await api('workspaces/'+encodeURIComponent($('selection').value)+'/'+resource,data); await details();});
$('selection').addEventListener('change',()=>details().catch(error=>$('message').textContent=error.message));
$('logout').addEventListener('click',async ()=>{try {await api('logout',{}); location.reload();}catch(error){$('message').textContent=error.message;}});
refresh().catch(()=>{ $('auth').hidden=false; $('workspace').hidden=true; });

function ledgerPath() { return 'workspaces/'+encodeURIComponent($('selection').value)+'/referrals/'+encodeURIComponent($('ledger-referral').value)+'/'; }
async function ledger() {
  const exists=Boolean($('ledger-referral').value);
  $('terms').hidden=!exists; $('payment').hidden=!exists;
  for(const id of ['accept-link','stage','approval','upload']) $(id).hidden=!exists;
  if(!exists) { $('ledger-summary').textContent='Select a referral first.'; return; }
  const result=await api(ledgerPath()+'ledger');
  await evidence();
  $('terms').hidden=Boolean(result.terms); $('payment').hidden=!result.terms;
  const money=value=>new Intl.NumberFormat('en-IN',{style:'currency',currency:result.terms?.[2]||'INR'}).format(value/100);
  $('ledger-summary').textContent=['Revenue: '+money(result.revenue),'Earned: '+money(result.earned),'Paid: '+money(result.paid),'Due: '+money(result.due),'Events: '+result.events.length,'Stage: '+result.stage,'Commission: '+result.commission_status,'Due date: '+(result.due_date||'Not approved')].join('\n');
}
$('ledger-referral').addEventListener('change',()=>ledger().catch(error=>$('message').textContent=error.message));
bind('terms',async data=>{ await api(ledgerPath()+'terms',data); await details(); });
let paymentAttempt=null;
bind('payment',async data=>{
  const path=ledgerPath()+'payments';
  const signature=JSON.stringify([path,data]);
  if(!paymentAttempt || paymentAttempt.signature!==signature) paymentAttempt={signature,id:crypto.randomUUID()};
  await api(path,{...data,request_id:paymentAttempt.id});
  paymentAttempt=null;
  await details();
});

function workspacePath() { return 'workspaces/'+encodeURIComponent($('selection').value)+'/'; }
function download(name, content) {
  const url=URL.createObjectURL(new Blob([content],{type:'application/octet-stream'}));
  const link=document.createElement('a'); link.href=url; link.download=name; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function click(id, action) { $(id).addEventListener('click',()=>action().catch(error=>$('message').textContent=error.message)); }
bind('referral',async data=>{
  let result=await api(workspacePath()+'referrals',data);
  if(result.duplicates?.length && !result.id) {
    if(!confirm('Possible duplicate: '+result.duplicates.length+' existing record(s). Save another introduction?')) throw new Error('Not saved. Review the existing records.');
    result=await api(workspacePath()+'referrals',{...data,confirm_duplicate:true});
  }
  await details();
});
bind('stage',async data=>{ await api(ledgerPath()+'stage',data); await details(); });
bind('approval',async data=>{ await api(ledgerPath()+'approve',data); await details(); });
click('accept-link',async ()=>{ const result=await api(ledgerPath()+'accept-link',{}); $('generated-token').textContent='Private acceptance link (24 hours): '+location.origin+'/#accept='+encodeURIComponent(result.token); });
click('portal-link',async ()=>{ const result=await api(workspacePath()+'portal-link',{partner:$('statement-partner').value}); $('generated-token').textContent='Private referrer link (7 days): '+location.origin+'/#portal='+encodeURIComponent(result.token); });
let acceptanceToken='';
bind('capability',async (data,event)=>{
  const action=event.submitter.value;
  const result=await api(action,data);
  $('capability-preview').textContent=JSON.stringify(result,null,2);
  acceptanceToken=action==='accept-preview'?data.token:'';
  $('accept-confirm').hidden=!acceptanceToken;
});
click('accept-confirm',async ()=>{await api('accept',{token:acceptanceToken}); acceptanceToken=''; $('accept-confirm').hidden=true; $('capability-preview').textContent='Introduction accepted.'; if(!$('workspace').hidden) await details();});
bind('statement',async data=>{const result=await api(workspacePath()+'statement',data); download('referdue-'+result.month+'.csv',result.csv);});
click('outbox-load',async ()=>{$('outbox').textContent=JSON.stringify(await api(workspacePath()+'outbox'),null,2);});
async function evidence() {
  const result=await api(ledgerPath()+'evidence');
  $('evidence').replaceChildren(...result.items.map(([id,name,size])=>{
    const li=document.createElement('li'); const button=document.createElement('button'); button.textContent=name+' ('+size+' bytes)';
    const path=ledgerPath();
    button.addEventListener('click',async ()=>{try{const file=await api(path+'evidence-download',{id}); download(file.name,Uint8Array.from(atob(file.content),c=>c.charCodeAt(0)));}catch(error){$('message').textContent=error.message;}});
    li.append(button); return li;
  }));
}
bind('upload',async (_,event)=>{
  const file=event.target.elements.file.files[0]; if(!file || file.size>1048576) throw new Error('Select a file up to 1 MB');
  const bytes=new Uint8Array(await file.arrayBuffer()); let text=''; for(const byte of bytes) text+=String.fromCharCode(byte);
  await api(ledgerPath()+'evidence',{name:file.name,content:btoa(text)}); await evidence();
});

const incoming=new URLSearchParams(location.hash.slice(1));
if(incoming.has('accept') || incoming.has('portal')) {
  $('capability').elements.token.value=incoming.get('accept')||incoming.get('portal');
  $('message').textContent=incoming.has('accept')?'Review the introduction before accepting.':'Choose Open referrer view.';
  history.replaceState(null,'',location.pathname);
}
