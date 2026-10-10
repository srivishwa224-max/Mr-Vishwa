import json
import tempfile
import unittest
from pathlib import Path
from server import App

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=App(Path(self.tmp.name)/'test.db')
        self.a=self.app.login('a@example.com','synthetic-passphrase-a',True)
        self.b=self.app.login('b@example.com','synthetic-passphrase-b',True)
    def tearDown(self):
        self.app.store.close(); self.tmp.cleanup()
    def test_account_workspace_partner_referral_flow(self):
        wid=self.app.route('POST','/api/workspaces',{'name':'Sample'},self.a)['id']
        prefix='/api/workspaces/'+wid+'/'
        partner=self.app.route('POST',prefix+'partners',{'name':'Example','email':'p@example.com'},self.a)['id']
        referral=self.app.route('POST',prefix+'referrals',{'partner':partner,'prospect':'Synthetic prospect'},self.a)['id']
        ledger_path=prefix+'referrals/'+referral+'/'
        self.app.route('POST',ledger_path+'terms',{'kind':'percent','value':'10','currency':'INR'},self.a)
        result=self.app.route('POST',ledger_path+'payments',{'kind':'revenue','amount':'500','request_id':'api-sample'},self.a)
        self.assertEqual(result['due'],5000)
        with self.assertRaises(PermissionError): self.app.route('GET',ledger_path+'ledger',{},self.b)
        self.assertEqual(len(self.app.route('GET',prefix+'referrals',{},self.a)['items']),1)
        with self.assertRaises(PermissionError): self.app.route('GET',prefix+'referrals',{},self.b)
        self.app.route('POST',prefix+'members',{'email':'b@example.com'},self.a)
        self.assertEqual(len(self.app.route('GET',prefix+'referrals',{},self.b)['items']),1)
        with self.assertRaises(PermissionError): self.app.route('POST',prefix+'members',{'email':'a@example.com'},self.b)
    def test_logout_and_expiry(self):
        self.app.route('POST','/api/logout',{},self.a)
        with self.assertRaises(PermissionError): self.app.authenticate(self.a)
        with self.app.db: self.app.db.execute('UPDATE sessions SET expires=0')
        with self.assertRaises(PermissionError): self.app.authenticate(self.b)
    def test_password_and_token_not_stored_plaintext(self):
        row=self.app.db.execute('SELECT digest FROM users LIMIT 1').fetchone()[0]
        self.assertNotEqual(row,b'synthetic-passphrase-a')
        self.assertFalse(self.app.db.execute('SELECT 1 FROM sessions WHERE digest=?',(self.a,)).fetchone())
        with self.assertRaises(PermissionError): self.app.login('a@example.com','incorrect-passphrase')
        token=self.app.login('a@example.com','synthetic-passphrase-a')
        self.assertEqual(self.app.authenticate(token),self.app.authenticate(self.a))
    def test_untrusted_actor_field_cannot_impersonate(self):
        actor=self.app.authenticate(self.a)
        wid=self.app.route('POST','/api/workspaces',{'name':'Private'},self.a)['id']
        with self.assertRaises(PermissionError):
            self.app.route('POST','/api/workspaces/'+wid+'/partners',{'actor':actor,'name':'X','email':'x@example.com'},self.b)
    def test_login_throttle(self):
        for _ in range(8):
            with self.assertRaises(PermissionError): self.app.login('unknown@example.com','synthetic-password')
        with self.assertRaises(ValueError): self.app.login('a@example.com','synthetic-passphrase-a')

if __name__=='__main__': unittest.main()
