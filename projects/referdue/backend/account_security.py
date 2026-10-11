"""Email proof and account recovery. Delivery is queued, never sent by requests."""
import hashlib
import json
import re
import secrets
import time


class AccountSecurity:
    def __init__(self, app, origin):
        self.app, self.db, self.origin = app, app.db, origin.rstrip('/')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS verified_accounts(actor TEXT PRIMARY KEY REFERENCES users(id), verified_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS account_tokens(digest TEXT PRIMARY KEY, actor TEXT NOT NULL REFERENCES users(id), purpose TEXT NOT NULL,
          expires INTEGER NOT NULL, consumed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS account_mail(id TEXT PRIMARY KEY, recipient TEXT NOT NULL, purpose TEXT NOT NULL,
          body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending');
        CREATE TABLE IF NOT EXISTS request_limits(bucket TEXT PRIMARY KEY, window INTEGER NOT NULL, count INTEGER NOT NULL);
        ''')

    @staticmethod
    def email(value):
        if not isinstance(value,str) or len(value)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value.strip()): raise ValueError('Enter a valid email')
        return value.strip().lower()

    def throttle(self, action, identity, maximum=10, seconds=60):
        now=int(time.time()); key=hashlib.sha256((action+':'+identity).encode()).hexdigest()
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT window,count FROM request_limits WHERE bucket=?',(key,)).fetchone()
            if row and now-row[0]<seconds:
                if row[1]>=maximum: raise ValueError('Too many attempts; try later')
                self.db.execute('UPDATE request_limits SET count=count+1 WHERE bucket=?',(key,))
            else: self.db.execute('INSERT OR REPLACE INTO request_limits VALUES(?,?,1)',(key,now))
            self.db.execute('DELETE FROM request_limits WHERE window<?',(now-86400,))

    def verified(self, actor):
        return bool(self.db.execute('SELECT 1 FROM verified_accounts WHERE actor=?',(actor,)).fetchone())

    def request(self, email, purpose):
        email=self.email(email)
        if purpose not in ('verify','reset'): raise ValueError('Invalid purpose')
        self.throttle('account-'+purpose,email,maximum=3,seconds=900)
        row=self.db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()
        # The HTTP response does not reveal account existence or any token.
        response={'ok':True,'message':'If this account is eligible, a link is queued for its email address.'}
        if not row or (purpose=='verify' and self.verified(row[0])): return response
        actor=row[0]; token=secrets.token_urlsafe(32); digest=hashlib.sha256(token.encode()).hexdigest()
        with self.db:
            self.db.execute('UPDATE account_tokens SET consumed=1 WHERE actor=? AND purpose=?',(actor,purpose))
            self.db.execute("UPDATE account_mail SET status='superseded',body='' WHERE recipient=? AND purpose=? AND status='pending'",(email,purpose))
            self.db.execute('INSERT INTO account_tokens(digest,actor,purpose,expires) VALUES(?,?,?,?)',(digest,actor,purpose,int(time.time())+1800))
            link=self.origin+'/#'+purpose+'='+token
            body=f'ReferDue {purpose} request\nOpen this private link within 30 minutes:\n{link}\nIf you did not request this, ignore this message.\n'
            self.db.execute('INSERT INTO account_mail(id,recipient,purpose,body) VALUES(?,?,?,?)',(secrets.token_hex(16),email,purpose,body))
        return response

    def complete(self, token, purpose, password=None):
        if not isinstance(token,str) or not 20<=len(token)<=200 or purpose not in ('verify','reset'): raise PermissionError('Invalid or expired link')
        if purpose=='reset' and (not isinstance(password,str) or not 12<=len(password)<=128): raise ValueError('Use 12–128 password characters')
        digest=hashlib.sha256(token.encode()).hexdigest()
        salt=secrets.token_bytes(16) if purpose=='reset' else None
        password_digest=self.app.password_hash(password,salt) if purpose=='reset' else None
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT actor FROM account_tokens WHERE digest=? AND purpose=? AND consumed=0 AND expires>?',(digest,purpose,int(time.time()))).fetchone()
            if not row: raise PermissionError('Invalid or expired link')
            actor=row[0]
            self.db.execute('UPDATE account_tokens SET consumed=1 WHERE digest=?',(digest,))
            self.db.execute('INSERT OR REPLACE INTO verified_accounts VALUES(?,?)',(actor,int(time.time())))
            if purpose=='reset':
                self.db.execute('UPDATE users SET salt=?,digest=? WHERE id=?',(salt,password_digest,actor))
                self.db.execute('DELETE FROM sessions WHERE actor=?',(actor,))
                self.db.execute('UPDATE account_tokens SET consumed=1 WHERE actor=?',(actor,))
            email=self.db.execute('SELECT email FROM users WHERE id=?',(actor,)).fetchone()[0]
            self.db.execute("UPDATE account_mail SET body='',status='consumed' WHERE recipient=? AND purpose=? AND status='pending'",(email,purpose))
        return {'ok':True,'message':'Email verified.' if purpose=='verify' else 'Password changed. Sign in again.'}
