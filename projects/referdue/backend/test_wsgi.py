import io
import json
import tempfile
import unittest
from pathlib import Path
from wsgi import Application

class WsgiTests(unittest.TestCase):
    def test_https_origin_cookie_and_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            application=Application(Path(tmp)/'db','https://referdue.example')
            def request(path,body=None,**overrides):
                raw=json.dumps(body).encode() if body is not None else b''
                env={'REQUEST_METHOD':'POST' if body is not None else 'GET','PATH_INFO':path,'wsgi.url_scheme':'https','HTTP_HOST':'referdue.example',
                    'HTTP_ORIGIN':'https://referdue.example','CONTENT_LENGTH':str(len(raw)),'CONTENT_TYPE':'application/json','wsgi.input':io.BytesIO(raw),'REMOTE_ADDR':'127.0.0.1',**overrides}
                response={}
                def start(status,headers): response.update(status=status,headers=dict(headers))
                response['body']=b''.join(application(env,start)); return response
            try:
                self.assertTrue(request('/',**{'wsgi.url_scheme':'http'})['status'].startswith('403'))
                self.assertTrue(request('/api/register',{},HTTP_ORIGIN='https://other.example')['status'].startswith('403'))
                registered=request('/api/register',{'email':'sample@example.com','password':'synthetic-long-password'})
                self.assertTrue(registered['status'].startswith('200'))
                cookie=registered['headers']['Set-Cookie']; self.assertIn('Secure;',cookie); self.assertIn('HttpOnly;',cookie)
                self.assertIn('Strict-Transport-Security',registered['headers'])
                self.assertTrue(request('/api/workspaces',HTTP_COOKIE=cookie)['status'].startswith('403'))
                body=application.app().db.execute("SELECT body FROM account_mail WHERE status='pending'").fetchone()[0]
                token=body.split('#verify=')[1].split()[0]
                self.assertIn('https://referdue.example/#verify=',body)
                self.assertTrue(request('/api/verify-account',{'token':token})['status'].startswith('200'))
                self.assertTrue(request('/api/workspaces',{'name':'Sample'},HTTP_COOKIE=cookie)['status'].startswith('200'))
                self.assertTrue(request('/server.py')['status'].startswith('404'))
            finally:
                if hasattr(application.local,'app'): application.local.app.store.close()
    def test_rejects_insecure_production_config(self):
        with self.assertRaises(ValueError): Application('/tmp/sample.db','http://example.com')

if __name__=='__main__': unittest.main()
