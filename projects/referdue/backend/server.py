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


class App:
    def __init__(self, path):
        self.store = Store(path)
        self.db = self.store.db
        self.store.init_ledger()
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, salt BLOB NOT NULL, digest BLOB NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY, actor TEXT NOT NULL REFERENCES users(id), expires INTEGER NOT NULL);
        ''')
        self.attempts = []

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
        self.attempts = [t for t in self.attempts if now-t < 60]
        if len(self.attempts) >= 10: raise ValueError('Too many attempts; wait one minute')
        self.attempts.append(now)
        if not isinstance(email,str) or len(email)>254 or '@' not in email: raise ValueError('Enter a valid email')
        if not isinstance(password,str) or not 12 <= len(password) <= 128: raise ValueError('Use a password of 12–128 characters')
        email = email.strip().lower()
        if register:
            actor = secrets.token_hex(16)
            salt = secrets.token_bytes(16)
            with self.db:
                self.db.execute('INSERT INTO users VALUES(?,?,?,?)', (actor,email,salt,self.password_hash(password,salt)))
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
        actor = self.authenticate(token)
        if path == '/api/logout' and method == 'POST':
            with self.db: self.db.execute('DELETE FROM sessions WHERE digest=?',(hashlib.sha256(token.encode()).hexdigest(),))
            return {'ok':True}
        if path == '/api/workspaces':
            if method == 'POST': return {'id':self.store.create_workspace(actor,data.get('name'))}
            return {'items':self.db.execute('SELECT w.id,w.name,m.role FROM workspaces w JOIN members m ON w.id=m.workspace WHERE m.actor=?',(actor,)).fetchall()}
        parts = path.strip('/').split('/')
        if len(parts)==6 and parts[:2]==['api','workspaces'] and parts[3]=='referrals':
            workspace, referral, action = parts[2],parts[4],parts[5]
            if action=='ledger' and method=='GET': return self.store.ledger(actor,workspace,referral)
            if action=='terms' and method=='POST':
                self.store.set_terms(actor,workspace,referral,data.get('kind'),data.get('value'),data.get('currency'))
                return self.store.ledger(actor,workspace,referral)
            if action=='payments' and method=='POST':
                return self.store.record_payment(actor,workspace,referral,data.get('kind'),data.get('amount'),data.get('request_id'))
            raise LookupError('Not found')
        if len(parts)!=4 or parts[:2]!=['api','workspaces']: raise LookupError('Not found')
        workspace, resource = parts[2:]
        self.store._authorize(actor,workspace)
        if resource == 'partners':
            if method=='POST': return {'id':self.store.add_partner(actor,workspace,data.get('name'),data.get('email'))}
            return {'items':self.db.execute('SELECT id,name,email FROM partners WHERE workspace=?',(workspace,)).fetchall()}
        if resource == 'referrals':
            if method=='POST': return {'id':self.store.add_referral(actor,workspace,data.get('partner'),data.get('prospect'))}
            return {'items':self.store.list_referrals(actor,workspace)}
        if resource == 'history' and method=='GET': return {'items':self.store.history(actor,workspace)}
        if resource == 'members' and method=='POST':
            self.store._authorize(actor,workspace,owner=True)
            email = data.get('email','')
            if not isinstance(email,str): raise ValueError('Invalid email')
            row = self.db.execute('SELECT id FROM users WHERE email=?',(email.strip().lower(),)).fetchone()
            if not row: raise ValueError('Account must register first')
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
                data = {}
                if method=='POST':
                    length = int(self.headers.get('Content-Length','0'))
                    if length<1 or length>16384 or self.headers.get('Content-Type')!='application/json': raise ValueError('Expected JSON, maximum 16 KB')
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
    app=App(path)
    server=HTTPServer(('127.0.0.1',args.port),make_handler(app))
    server.timeout=10
    print(f'Local development only: http://127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    finally: server.server_close(); app.store.close()
