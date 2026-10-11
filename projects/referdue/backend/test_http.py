import http.client
import json
import sqlite3
import queue
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import HTTPServer
from server import App, make_handler

class HttpTests(unittest.TestCase):
    def test_real_http_auth_origin_and_static_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready=queue.Queue()
            def serve():
                app=App(Path(tmp)/'private.db')
                server=HTTPServer(('127.0.0.1',0),make_handler(app))
                ready.put(server)
                try: server.serve_forever(poll_interval=0.01)
                finally: server.server_close(); app.store.close()
            thread=threading.Thread(target=serve)
            thread.start(); server=ready.get(timeout=5)
            port=server.server_address[1]
            def request(method,path,data=None,cookie=None,origin=True,host=None):
                connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
                headers={'Host':host or '127.0.0.1:'+str(port)}
                if origin: headers['Origin']='http://127.0.0.1:'+str(port)
                if cookie: headers['Cookie']=cookie
                body=None
                if data is not None: body=json.dumps(data); headers['Content-Type']='application/json'
                connection.request(method,path,body,headers)
                response=connection.getresponse()
                result=(response.status,dict(response.getheaders()),response.read())
                connection.close(); return result
            try:
                self.assertEqual(request('GET','/')[0],200)
                self.assertEqual(request('GET','/private.db')[0],404)
                self.assertEqual(request('GET','/backend/server.py')[0],404)
                self.assertEqual(request('GET','/api/workspaces')[0],403)
                self.assertEqual(request('GET','/',host='attacker.example')[0],403)
                data={'email':'synthetic@example.com','password':'synthetic-long-password'}
                self.assertEqual(request('POST','/api/register',data,origin=False)[0],403)
                status,headers,_=request('POST','/api/register',data)
                self.assertEqual(status,200)
                self.assertIn('HttpOnly',headers['Set-Cookie']); self.assertIn('SameSite=Strict',headers['Set-Cookie'])
                cookie=headers['Set-Cookie'].split(';')[0]
                self.assertEqual(request('POST','/api/workspaces',{'name':'Sample'},cookie)[0],403)
                with sqlite3.connect(Path(tmp)/'private.db') as db:
                    body=db.execute("SELECT body FROM account_mail WHERE status='pending'").fetchone()[0]
                token=body.split('#verify=')[1].split()[0]
                self.assertEqual(request('POST','/api/verify-account',{'token':token})[0],200)
                self.assertEqual(request('POST','/api/workspaces',{'name':'Sample'},cookie)[0],200)
                response=request('GET','/api/workspaces',cookie=cookie)
                self.assertEqual(len(json.loads(response[2])['items']),1)
                self.assertEqual(request('POST','/api/logout',{},cookie)[0],200)
                self.assertEqual(request('GET','/api/workspaces',cookie=cookie)[0],403)
            finally:
                server.shutdown(); thread.join(timeout=5)

if __name__=='__main__': unittest.main()
