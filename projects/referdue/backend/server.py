"""Loopback-only development server. Not a production HTTP server."""
import argparse
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from store import Store
from workflows import Workflows
from account_security import AccountSecurity


class App:
    def __init__(self, path, origin="http://127.0.0.1:4174"):
        self.store = Store(path)
        self.db = self.store.db
        self.store.init_ledger()
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, salt BLOB NOT NULL, digest BLOB NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY, actor TEXT NOT NULL REFERENCES users(id), expires INTEGER NOT NULL);
        ''')
        self.workflows = Workflows(self.store)
        self.security = AccountSecurity(self,origin)

    @staticmethod
    def password_hash(password, salt):
        return hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)

    def authenticate(self, token):
        row = self.db.execute('SELECT actor FROM sessions WHERE digest=? AND expires>?',
                              (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        if not row: raise PermissionError('Sign in required')
        return row[0]

    def login(self, email, password, register=False):
        now = time.time()
        email=self.security.email(email)
        self.security.throttle('login',email)
        if not isinstance(password,str) or not 12 <= len(password) <= 128: raise ValueError('Use a password of 12–128 characters')
        email = email.strip().lower()
        if register:
            actor = secrets.token_hex(16)
            salt = secrets.token_bytes(16)
            with self.db:
                self.db.execute('INSERT INTO users VALUES(?,?,?,?)', (actor,email,salt,self.password_hash(password,salt)))
        if register: self.security.request(email,'verify')
        row = self.db.execute('SELECT id,salt,digest FROM users WHERE email=?',(email,)).fetchone()
        salt = row[1] if row else bytes(16)
        digest = self.password_hash(password,salt)
        if not row or not hmac.compare_digest(row[2],digest): raise PermissionError('Invalid email or password')
        token = secrets.token_urlsafe(32)
        with self.db:
            self.db.execute('DELETE FROM sessions WHERE expires<=?',(int(now),))
            self.db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row[0],int(now)+3600))
        return token

    def route(self, method, path, data, token):
        if method=='POST' and path in ['/api/request-verification','/api/request-reset']:
            return self.security.request(data.get('email'),'verify' if path.endswith('verification') else 'reset')
        if method=='POST' and path in ['/api/verify-account','/api/reset-password']:
            return self.security.complete(data.get('token'),'verify' if path.endswith('account') else 'reset',data.get('password'))
        if method=='POST' and path in ['/api/accept-preview','/api/accept','/api/portal']:
            capability=data.get('token')
            return self.workflows.preview(capability) if path=='/api/accept-preview' else self.workflows.accept(capability) if path=='/api/accept' else self.workflows.portal(capability)
        actor = self.authenticate(token)
        if path == '/api/logout' and method == 'POST':
            with self.db: self.db.execute('DELETE FROM sessions WHERE digest=?',(hashlib.sha256(token.encode()).hexdigest(),))
            return {'ok':True}
        if path=='/api/me' and method=='GET': return {'verified':self.security.verified(actor)}
        if not self.security.verified(actor): raise PermissionError('Verify your email before accessing workspaces')
        if path == '/api/workspaces':
            if method == 'POST': return {'id':self.store.create_workspace(actor,data.get('name'))}
            return {'items':self.db.execute('SELECT w.id,w.name,m.role FROM workspaces w JOIN members m ON w.id=m.workspace WHERE m.actor=?',(actor,)).fetchall()}
        parts = path.strip('/').split('/')
        if len(parts)==6 and parts[:2]==['api','workspaces'] and parts[3]=='referrals':
            workspace, referral, action = parts[2],parts[4],parts[5]
            if action=='ledger' and method=='GET': return self.workflows.summary(actor,workspace,referral)
            if action=='terms' and method=='POST':
                self.store.set_terms(actor,workspace,referral,data.get('kind'),data.get('value'),data.get('currency'))
                return self.store.ledger(actor,workspace,referral)
            if action=='payments' and method=='POST':
                return self.workflows.payment(actor,workspace,referral,data)
            if action=='details' and method=='POST': return self.workflows.submit(actor,workspace,data,legacy=referral)
            if action=='accept-link' and method=='POST': return self.workflows.issue(actor,workspace,referral,'accept')
            if action=='stage' and method=='POST': return self.workflows.stage(actor,workspace,referral,data.get('stage'))
            if action=='approve' and method=='POST': return self.workflows.approve(actor,workspace,referral,data.get('due_date'))
            if action=='evidence':
                return self.workflows.add_evidence(actor,workspace,referral,data) if method=='POST' else self.workflows.evidence(actor,workspace,referral)
            if action=='evidence-download' and method=='POST': return self.workflows.evidence(actor,workspace,referral,data.get('id'))
            raise LookupError('Not found')
        if len(parts)!=4 or parts[:2]!=['api','workspaces']: raise LookupError('Not found')
        workspace, resource = parts[2:]
        self.store._authorize(actor,workspace)
        if resource == 'partners':
            if method=='POST': return {'id':self.store.add_partner(actor,workspace,data.get('name'),data.get('email'),data.get('payment_reference',''))}
            return {'items':self.db.execute("SELECT p.id,p.name,p.email,coalesce(x.payment_reference,'') FROM partners p LEFT JOIN partner_profiles x ON x.partner=p.id WHERE p.workspace=?",(workspace,)).fetchall()}
        if resource == 'referrals':
            if method=='POST': return self.workflows.submit(actor,workspace,data)
            return {'items':self.store.list_referrals(actor,workspace)}
        if resource=='portal-link' and method=='POST': return self.workflows.issue(actor,workspace,data.get('partner'),'portal')
        if resource=='statement' and method=='POST': return self.workflows.statement(actor,workspace,data.get('partner'),data.get('month'))
        if resource=='outbox' and method=='GET':
            self.store._authorize(actor,workspace,owner=True)
            return {'items':self.db.execute('SELECT event,recipient,status,created_at FROM outbox WHERE workspace=? ORDER BY id',(workspace,)).fetchall()}
        if resource == 'history'  and method=='GET': return {'items':self.store.history(actor,workspace)}
        if resource == 'members' and method=='POST':
            self.store._authorize(actor,workspace,owner=True)
            email = data.get('email','')
            if not isinstance(email,str): raise ValueError('Invalid email')
            row = self.db.execute('SELECT id FROM users WHERE email=?',(email.strip().lower(),)).fetchone()
            if not row or not self.security.verified(row[0]): raise ValueError('Account must register and verify its email first')
            self.store.add_member(actor,workspace,row[0])
            return {'ok':True}
        raise LookupError('Not found')


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def reply(self, status, body, content_type='application/json', cookie=None):
            raw = body if isinstance(body,bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if cookie: self.send_header('Set-Cookie',cookie)
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self): self.handle_request('GET')
        def do_POST(self): self.handle_request('POST')
        def handle_request(self, method):
            port = self.server.server_address[1]
            allowed = {f'localhost:{port}',f'127.0.0.1:{port}'}
            host = self.headers.get('Host','')
            if host not in allowed: return self.reply(403,{'error':'Invalid host'})
            if method=='POST' and self.headers.get('Origin') != 'http://'+host:
                return self.reply(403,{'error':'Same-origin request required'})
            if method=='GET' and self.path in ['/', '/workspace.js']:
                name = 'workspace.html' if self.path=='/' else 'workspace.js'
                return self.reply(200,(Path(__file__).parent/name).read_bytes(), 'text/html; charset=utf-8' if name.endswith('.html') else 'text/javascript')
            if not self.path.startswith('/api/'): return self.reply(404,{'error':'Not found'})
            try:
                if method=='POST': app.security.throttle('http',self.client_address[0],maximum=120)
                data = {}
                if method=='POST':
                    length = int(self.headers.get('Content-Length','0'))
                    if length<1 or length>1500000 or self.headers.get('Content-Type')!='application/json': raise ValueError('Expected JSON, maximum 1.5 MB')
                    data=json.loads(self.rfile.read(length))
                    if not isinstance(data,dict): raise ValueError('Expected JSON object')
                jar = SimpleCookie(); jar.load(self.headers.get('Cookie',''))
                token = jar['rd_session'].value if 'rd_session' in jar else ''
                if method=='POST' and self.path in ['/api/login','/api/register']:
                    token=app.login(data.get('email'),data.get('password'),self.path=='/api/register')
                    return self.reply(200,{'ok':True},cookie='rd_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600')
                result=app.route(method,self.path,data,token)
                return self.reply(200,result,cookie='rd_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0' if self.path=='/api/logout' else None)
            except PermissionError as error: self.reply(403,{'error':str(error)})
            except LookupError: self.reply(404,{'error':'Not found'})
            except (ValueError,TypeError,sqlite3.IntegrityError): self.reply(400,{'error':'Invalid or conflicting request'})
    return Handler

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--database',required=True,help='Private database path outside the source/static folder')
    parser.add_argument('--port',type=int,default=4174)
    args=parser.parse_args()
    path=Path(args.database).expanduser().resolve()
    if Path(__file__).resolve().parents[1] in path.parents: parser.error('Database must be outside the project folder')
    app=App(path,origin=f"http://127.0.0.1:{args.port}")
    server=HTTPServer(('127.0.0.1',args.port),make_handler(app))
    server.timeout=10
    print(f'Local development only: http://127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    finally: server.server_close(); app.store.close()
