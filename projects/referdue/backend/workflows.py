"""Core referral workflows. Uses local outbox; deliberately never sends email."""
import base64
import csv
import hashlib
import io
import json
import re
import secrets
import time
import uuid
from datetime import date, datetime


class Workflows:
    def __init__(self, store):
        self.s, self.db = store, store.db
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS referral_details(
          referral TEXT PRIMARY KEY REFERENCES referrals(id), company TEXT NOT NULL, email TEXT NOT NULL,
          phone TEXT NOT NULL, service TEXT NOT NULL, introduced TEXT NOT NULL, source TEXT NOT NULL,
          notes TEXT NOT NULL, estimate INTEGER NOT NULL, identity TEXT NOT NULL, stage TEXT NOT NULL DEFAULT 'Submitted');
        CREATE TABLE IF NOT EXISTS claims(workspace TEXT NOT NULL, identity TEXT NOT NULL,
          referral TEXT UNIQUE NOT NULL REFERENCES referrals(id), PRIMARY KEY(workspace,identity));
        CREATE TABLE IF NOT EXISTS attribution_keys(workspace TEXT NOT NULL, identity TEXT NOT NULL,
          referral TEXT NOT NULL REFERENCES referrals(id), PRIMARY KEY(workspace,identity));
        INSERT OR IGNORE INTO attribution_keys SELECT workspace,identity,referral FROM claims;
        CREATE TABLE IF NOT EXISTS capabilities(digest TEXT PRIMARY KEY, kind TEXT NOT NULL,
          workspace TEXT NOT NULL, target TEXT NOT NULL, expires INTEGER NOT NULL, consumed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS approvals(referral TEXT PRIMARY KEY REFERENCES referrals(id), due_date TEXT NOT NULL, actor TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, referral TEXT NOT NULL REFERENCES referrals(id), name TEXT NOT NULL, content BLOB NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY, workspace TEXT NOT NULL, recipient TEXT NOT NULL,
          event TEXT NOT NULL, referral TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          status TEXT NOT NULL DEFAULT 'pending');
        ''')
        # API and ordinary SQL writes cannot rewrite monetary history or terms.
        for table in ('payments','terms'):
            for action in ('UPDATE','DELETE'):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Append-only record'); END")
        self.db.commit()

    @staticmethod
    def normalize(value): return ''.join(c for c in value.casefold() if c.isalnum())

    @staticmethod
    def text(data, key, required=False):
        value=data.get(key,'')
        if not isinstance(value,str) or len(value)>2000 or (required and not value.strip()): raise ValueError('Invalid '+key)
        return value.strip()

    def notify(self, workspace, referral, event):
        row=self.db.execute('SELECT p.email FROM partners p JOIN referrals r ON p.id=r.partner WHERE r.id=? AND r.workspace=?',(referral,workspace)).fetchone()
        if row: self.db.execute('INSERT INTO outbox(workspace,recipient,event,referral) VALUES(?,?,?,?)',(workspace,row[0],event,referral))

    def submit(self, actor, workspace, data, legacy=None):
        self.s._authorize(actor,workspace)
        if legacy:
            self.s._referral_access(actor,workspace,legacy)
            if self.db.execute('SELECT 1 FROM referral_details WHERE referral=?',(legacy,)).fetchone(): raise ValueError('Details already exist')
        values={key:self.text(data,key,key in ('company','service','introduced')) for key in ('company','email','phone','service','introduced','source','notes')}
        date.fromisoformat(values['introduced'])
        if values['email'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',values['email']): raise ValueError('Invalid email')
        estimate=self.s.cents(data.get('estimate'))
        company=self.normalize(values['company']); email=values['email'].casefold(); phone=''.join(c for c in values['phone'] if c.isdigit())
        identity='email:'+email if email else 'phone:'+phone if len(phone)>=7 else 'company:'+company
        existing=self.db.execute('SELECT r.id,d.company,d.email,d.phone FROM referrals r JOIN referral_details d ON r.id=d.referral WHERE r.workspace=?',(workspace,)).fetchall()
        duplicates=[r[0] for r in existing if r[0]!=legacy and (self.normalize(r[1])==company or (email and r[2].casefold()==email) or (len(phone)>=7 and ''.join(c for c in r[3] if c.isdigit())==phone))]
        if duplicates and data.get('confirm_duplicate') is not True: return {'duplicates':duplicates}
        partner=self.text(data,'partner',not legacy); prospect=self.text(data,'prospect',not legacy)
        key=legacy or str(uuid.uuid4())
        with self.db:
            if not legacy: self.db.execute('INSERT INTO referrals VALUES(?,?,?,?)',(key,workspace,partner,prospect))
            self.db.execute('INSERT INTO referral_details(referral,company,email,phone,service,introduced,source,notes,estimate,identity) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (key,values['company'],email,values['phone'],values['service'],values['introduced'],values['source'],values['notes'],estimate,identity))
            self.s._log(actor,workspace,'referral.details_completed' if legacy else 'referral.submitted',key)
        return {'id':key,'duplicates':duplicates}

    def issue(self, actor, workspace, target, kind):
        self.s._authorize(actor,workspace,owner=True)
        if kind=='accept':
            self.s._referral_access(actor,workspace,target)
            if not self.db.execute('SELECT 1 FROM referral_details WHERE referral=?',(target,)).fetchone(): raise ValueError('Complete referral details required')
            if not self.db.execute('SELECT 1 FROM terms WHERE referral=?',(target,)).fetchone(): raise ValueError('Record terms before acceptance')
        elif kind=='portal':
            if not self.db.execute('SELECT 1 FROM partners WHERE id=? AND workspace=?',(target,workspace)).fetchone(): raise PermissionError('Access denied')
        else: raise ValueError('Invalid capability')
        token=secrets.token_urlsafe(32)
        with self.db:
            self.db.execute('UPDATE capabilities SET consumed=1 WHERE kind=? AND workspace=? AND target=?',(kind,workspace,target))
            self.db.execute('INSERT INTO capabilities(digest,kind,workspace,target,expires) VALUES(?,?,?,?,?)',
                (hashlib.sha256(token.encode()).hexdigest(),kind,workspace,target,int(time.time())+(86400 if kind=='accept' else 604800)))
            self.s._log(actor,workspace,'link.issued.'+kind,target)
        return {'token':token,'expires_in':86400 if kind=='accept' else 604800}

    def capability(self, token, kind):
        if not isinstance(token,str) or len(token)>200: raise PermissionError('Invalid or expired link')
        row=self.db.execute('SELECT workspace,target FROM capabilities WHERE digest=? AND kind=? AND consumed=0 AND expires>?',
            (hashlib.sha256(token.encode()).hexdigest(),kind,int(time.time()))).fetchone()
        if not row: raise PermissionError('Invalid or expired link')
        return row

    def preview(self, token):
        workspace,referral=self.capability(token,'accept')
        row=self.db.execute('SELECT r.prospect,d.company,d.service,t.kind,t.value,t.currency FROM referrals r JOIN referral_details d ON d.referral=r.id JOIN terms t ON t.referral=r.id WHERE r.id=?',(referral,)).fetchone()
        return {'referral':list(row),'notice':'Possession of this link permits acceptance. Confirm only if you are the intended receiving business.'}

    def accept(self, token):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            workspace,referral=self.capability(token,'accept')
            row=self.db.execute('SELECT identity,stage FROM referral_details WHERE referral=?',(referral,)).fetchone()
            if row[1]!='Submitted': raise ValueError('Referral is no longer awaiting acceptance')
            details=self.db.execute('SELECT company,email,phone FROM referral_details WHERE referral=?',(referral,)).fetchone()
            identities={'company:'+self.normalize(details[0]),row[0]}
            if details[1]: identities.add('email:'+details[1].casefold())
            phone=''.join(c for c in details[2] if c.isdigit())
            if len(phone)>=7: identities.add('phone:'+phone)
            for identity in sorted(identities): self.db.execute('INSERT INTO attribution_keys VALUES(?,?,?)',(workspace,identity,referral))
            self.db.execute('INSERT INTO claims VALUES(?,?,?)',(workspace,row[0],referral))
            self.db.execute("UPDATE referral_details SET stage='Accepted' WHERE referral=?",(referral,))
            self.db.execute('UPDATE capabilities SET consumed=1 WHERE digest=?',(hashlib.sha256(token.encode()).hexdigest(),))
            self.s._log('acceptance-link',workspace,'referral.accepted',referral)
            self.notify(workspace,referral,'referral.accepted')
        return {'ok':True}

    def stage(self, actor, workspace, referral, stage):
        self.s._referral_access(actor,workspace,referral)
        transitions={'Submitted':{'Lost'},'Accepted':{'Contacted','Won','Lost'},'Contacted':{'Won','Lost'},'Won':set(),'Lost':set()}
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT stage FROM referral_details WHERE referral=?',(referral,)).fetchone()
            if not row or stage not in transitions.get(row[0],set()): raise ValueError('Invalid stage transition')
            self.db.execute('UPDATE referral_details SET stage=? WHERE referral=?',(stage,referral))
            self.s._log(actor,workspace,'stage.'+stage,referral); self.notify(workspace,referral,'stage.'+stage)
        return {'ok':True}

    def approve(self, actor, workspace, referral, due):
        self.s._referral_access(actor,workspace,referral); self.s._authorize(actor,workspace,owner=True)
        if not isinstance(due,str): raise ValueError('Due date required')
        date.fromisoformat(due)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            current=self.s.ledger(actor,workspace,referral)
            if current['earned']<=0: raise ValueError('No earned commission')
            self.db.execute('INSERT INTO approvals VALUES(?,?,?)',(referral,due,actor))
            self.s._log(actor,workspace,'commission.approved',referral); self.notify(workspace,referral,'commission.approved')
        return {'ok':True}

    def summary(self, actor, workspace, referral, today=None):
        result=self.s.ledger(actor,workspace,referral)
        detail=self.db.execute('SELECT stage FROM referral_details WHERE referral=?',(referral,)).fetchone()
        approval=self.db.execute('SELECT due_date FROM approvals WHERE referral=?',(referral,)).fetchone()
        today=today or date.today().isoformat()
        result['stage']=detail[0] if detail else 'Legacy introduction'
        result['due_date']=approval[0] if approval else None
        result['commission_status']='Pending'
        if result['earned']>0:
            if result['due']==0: result['commission_status']='Paid'
            elif not approval: result['commission_status']='Pending approval'
            elif approval[0]<today: result['commission_status']='Overdue'
            elif approval[0]==today: result['commission_status']='Due'
            else: result['commission_status']='Approved'
        if result['revenue']>0: result['stage']='Customer Paid'
        if approval and result['due']>0 and approval[0]<=today: result['stage']='Commission Due'
        if result['earned']>0 and result['due']==0: result['stage']='Commission Paid'
        return result

    def payment(self, actor, workspace, referral, data):
        self.s._referral_access(actor,workspace,referral)
        detail=self.db.execute('SELECT stage FROM referral_details WHERE referral=?',(referral,)).fetchone()
        if not detail or detail[0]!='Won': raise ValueError('Accept the referral and mark it Won before recording revenue')
        if data.get('kind')=='commission' and not self.db.execute('SELECT 1 FROM approvals WHERE referral=?',(referral,)).fetchone(): raise ValueError('Owner approval required')
        # Outbox and ledger commit together; a retry returns the original event.
        return self.s.record_payment(actor,workspace,referral,data.get('kind'),data.get('amount'),data.get('request_id'),
            on_record=lambda: self.notify(workspace,referral,'payment.'+data['request_id']))

    def portal(self, token):
        workspace,partner=self.capability(token,'portal')
        # Select only this partner's records. Never grant membership from email matching.
        owner=self.db.execute("SELECT actor FROM members WHERE workspace=? AND role='owner' LIMIT 1",(workspace,)).fetchone()[0]
        rows=self.db.execute('SELECT id,prospect FROM referrals WHERE workspace=? AND partner=?',(workspace,partner)).fetchall()
        return {'items':[{'id':key,'prospect':name,'ledger':self.summary(owner,workspace,key)} for key,name in rows]}

    def statement(self, actor, workspace, partner, month):
        self.s._authorize(actor,workspace)
        if not isinstance(month,str) or not re.fullmatch(r'\d{4}-\d{2}',month): raise ValueError('Use YYYY-MM')
        date.fromisoformat(month+'-01')
        if not self.db.execute('SELECT 1 FROM partners WHERE workspace=? AND id=?',(workspace,partner)).fetchone(): raise PermissionError('Access denied')
        output=io.StringIO(); writer=csv.writer(output)
        writer.writerow(['Referral','Prospect','Currency','Opening due','Revenue in month','Commission earned in month','Paid in month','Closing due'])
        for referral,prospect in self.db.execute('SELECT id,prospect FROM referrals WHERE workspace=? AND partner=?',(workspace,partner)):
            terms=self.db.execute('SELECT kind,value,currency FROM terms WHERE referral=?',(referral,)).fetchone()
            if not terms: continue
            events=self.db.execute('SELECT kind,cents,substr(created_at,1,7) FROM payments WHERE referral=?',(referral,)).fetchall()
            rev_before=sum(n for k,n,m in events if k=='revenue' and m<month); rev=sum(n for k,n,m in events if k=='revenue' and m==month)
            paid_before=sum(n for k,n,m in events if k=='commission' and m<month); paid=sum(n for k,n,m in events if k=='commission' and m==month)
            def earned(n): return (n*terms[1]+5000)//10000 if terms[0]=='percent' else (terms[1] if n else 0)
            opening=earned(rev_before)-paid_before; accrued=earned(rev_before+rev)-earned(rev_before)
            safe="'"+prospect if prospect.lstrip().startswith(('=','+','-','@','\t','\r','\n')) else prospect
            writer.writerow([referral,safe,terms[2],f'{opening/100:.2f}',f'{rev/100:.2f}',f'{accrued/100:.2f}',f'{paid/100:.2f}',f'{(opening+accrued-paid)/100:.2f}'])
        return {'csv':output.getvalue(),'month':month,'timezone':'UTC'}

    def add_evidence(self, actor, workspace, referral, data):
        self.s._referral_access(actor,workspace,referral)
        name=self.text(data,'name',True)
        if '/' in name or '\\' in name or len(name)>100: raise ValueError('Invalid filename')
        encoded=data.get('content','')
        if not isinstance(encoded,str) or len(encoded)>1400000: raise ValueError('Maximum file size is 1 MB')
        raw=base64.b64decode(encoded,validate=True)
        if not raw or len(raw)>1048576: raise ValueError('Maximum file size is 1 MB')
        lower=name.lower()
        valid=(lower.endswith('.pdf') and raw.startswith(b'%PDF-')) or (lower.endswith('.png') and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (lower.endswith(('.jpg','.jpeg')) and raw.startswith(b'\xff\xd8\xff'))
        if lower.endswith('.txt'):
            raw.decode('utf-8'); valid=b'\x00' not in raw
        if not valid: raise ValueError('Use PDF, PNG, JPEG or UTF-8 text')
        key=str(uuid.uuid4())
        with self.db:
            self.db.execute('INSERT INTO evidence VALUES(?,?,?,?)',(key,referral,name,raw))
            self.s._log(actor,workspace,'evidence.added',key)
        return {'id':key}

    def evidence(self, actor, workspace, referral, key=None):
        self.s._referral_access(actor,workspace,referral)
        if key is None: return {'items':self.db.execute('SELECT id,name,length(content) FROM evidence WHERE referral=?',(referral,)).fetchall()}
        row=self.db.execute('SELECT name,content FROM evidence WHERE referral=? AND id=?',(referral,key)).fetchone()
        if not row: raise PermissionError('Access denied')
        return {'name':row[0],'content':base64.b64encode(row[1]).decode()}
