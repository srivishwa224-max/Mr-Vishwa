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
  list('partners',partners.items.map(row=>row[1]+' — '+row[2]));
  $('partner-selection').replaceChildren(...partners.items.map(row=>new Option(row[1],row[0])));
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
    try { await action(Object.fromEntries(new FormData(event.target)),event); $('message').textContent='Saved.'; event.target.reset(); }
    catch(error) { $('message').textContent=error.message; }
  });
}
bind('login',async (data,event)=>{ await api(event.submitter.value,data); await refresh(); });
bind('new-workspace',async data=>{await api('workspaces',data); await refresh();});
for(const [id,resource] of [['partner','partners'],['referral','referrals'],['member','members']]) bind(id,async data=>{await api('workspaces/'+encodeURIComponent($('selection').value)+'/'+resource,data); await details();});
$('selection').addEventListener('change',()=>details().catch(error=>$('message').textContent=error.message));
$('logout').addEventListener('click',async ()=>{try {await api('logout',{}); location.reload();}catch(error){$('message').textContent=error.message;}});
refresh().catch(()=>{ $('auth').hidden=false; $('workspace').hidden=true; });

function ledgerPath() { return 'workspaces/'+encodeURIComponent($('selection').value)+'/referrals/'+encodeURIComponent($('ledger-referral').value)+'/'; }
async function ledger() {
  const exists=Boolean($('ledger-referral').value);
  $('terms').hidden=!exists; $('payment').hidden=!exists;
  if(!exists) { $('ledger-summary').textContent='Select a referral first.'; return; }
  const result=await api(ledgerPath()+'ledger');
  $('terms').hidden=Boolean(result.terms); $('payment').hidden=!result.terms;
  const money=value=>new Intl.NumberFormat('en-IN',{style:'currency',currency:result.terms?.[2]||'INR'}).format(value/100);
  $('ledger-summary').textContent=['Revenue: '+money(result.revenue),'Earned: '+money(result.earned),'Paid: '+money(result.paid),'Due: '+money(result.due),'Events: '+result.events.length].join('\n');
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
