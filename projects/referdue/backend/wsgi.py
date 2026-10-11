"""WSGI entry point for an HTTPS reverse proxy plus production WSGI server.
No server is launched and no live service is connected by importing this module.
"""
import json
import os
import sqlite3
import threading
from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit
from server import App


class Application:
    def __init__(self, database, origin):
        parsed=urlsplit(origin)
        if parsed.scheme!='https' or not parsed.netloc or parsed.path not in ('','/') or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError('Production origin must be a single HTTPS origin')
        self.origin='https://'+parsed.netloc
        self.host=parsed.netloc
        self.database=Path(database).expanduser().resolve()
        if Path(__file__).resolve().parents[1] in self.database.parents: raise ValueError('Database must be outside the source tree')
        self.local=threading.local()

    def app(self):
        if not hasattr(self.local,'app'): self.local.app=App(self.database,self.origin)
        return self.local.app

    def __call__(self, environ, start_response):
        status=200; headers=[]; result=None; content_type='application/json'; cookie=None
        method=environ.get('REQUEST_METHOD','GET'); path=environ.get('PATH_INFO','/')
        def reject(code,message): return code,{'error':message}
        if environ.get('wsgi.url_scheme')!='https' or environ.get('HTTP_HOST')!=self.host:
            status,result=reject(403,'HTTPS and configured host required')
        elif method not in ('GET','POST'): status,result=reject(405,'Method not allowed')
        elif method=='POST' and environ.get('HTTP_ORIGIN')!=self.origin: status,result=reject(403,'Same-origin request required')
        elif method=='GET' and path in ('/','/workspace.js'):
            name='workspace.html' if path=='/' else 'workspace.js'
            result=(Path(__file__).parent/name).read_bytes()
            content_type='text/html; charset=utf-8' if path=='/' else 'text/javascript'
        elif not path.startswith('/api/'): status,result=reject(404,'Not found')
        else:
            try:
                app=self.app(); data={}
                if method=='POST':
                    app.security.throttle('http',environ.get('REMOTE_ADDR','unknown'),maximum=120)
                    length=int(environ.get('CONTENT_LENGTH','0'))
                    if not 1<=length<=1500000 or environ.get('CONTENT_TYPE')!='application/json': raise ValueError('Expected bounded JSON body')
                    data=json.loads(environ['wsgi.input'].read(length))
                    if not isinstance(data,dict): raise ValueError('Expected object')
                jar=SimpleCookie(); jar.load(environ.get('HTTP_COOKIE',''))
                token=jar['rd_session'].value if 'rd_session' in jar else ''
                if method=='POST' and path in ('/api/login','/api/register'):
                    token=app.login(data.get('email'),data.get('password'),path=='/api/register')
                    cookie=f'rd_session={token}; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600'
                    result={'ok':True}
                else:
                    result=app.route(method,path,data,token)
                    if path=='/api/logout': cookie='rd_session=; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'
            except PermissionError as error: status,result=reject(403,str(error))
            except LookupError: status,result=reject(404,'Not found')
            except (ValueError,TypeError,CookieError,sqlite3.IntegrityError): status,result=reject(400,'Invalid or conflicting request')
            except sqlite3.OperationalError: status,result=reject(503,'Database temporarily unavailable; retry safely')
        raw=result if isinstance(result,bytes) else json.dumps(result).encode()
        headers.extend([('Content-Type',content_type),('Content-Length',str(len(raw))),('Cache-Control','no-store'),
            ('Referrer-Policy','no-referrer'),('X-Content-Type-Options','nosniff'),('Strict-Transport-Security','max-age=31536000'),
            ('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")])
        if cookie: headers.append(('Set-Cookie',cookie))
        reason={200:'OK',400:'Bad Request',403:'Forbidden',404:'Not Found',405:'Method Not Allowed',503:'Service Unavailable'}[status]
        start_response(f'{status} {reason}',headers)
        return [raw]


_instance=None
def application(environ,start_response):
    global _instance
    if _instance is None:
        # Only non-secret deployment configuration; operator must explicitly configure these.
        _instance=Application(os.environ['REFERDUE_DATABASE'],os.environ['REFERDUE_ORIGIN'])
    return _instance(environ,start_response)
