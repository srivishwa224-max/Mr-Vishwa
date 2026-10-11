import tempfile
import unittest
from pathlib import Path
from server import App
from notifications import dispatch

class AccountSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'db'; self.app=App(self.path)
        self.token=self.app.login('sample@example.com','synthetic-original-password',True)
    def tearDown(self): self.app.store.close(); self.tmp.cleanup()
    def mail_token(self,purpose):
        body=self.app.db.execute("SELECT body FROM account_mail WHERE purpose=? AND status='pending'",(purpose,)).fetchone()[0]
        return body.split('#'+purpose+'=')[1].split()[0]
    def test_unverified_access_denied_then_verified(self):
        with self.assertRaises(PermissionError): self.app.route('POST','/api/workspaces',{'name':'Private'},self.token)
        token=self.mail_token('verify'); self.app.security.complete(token,'verify')
        self.assertIn('id',self.app.route('POST','/api/workspaces',{'name':'Private'},self.token))
        with self.assertRaises(PermissionError): self.app.security.complete(token,'verify')
    def test_reset_revokes_sessions_and_old_password(self):
        self.app.security.request('sample@example.com','reset'); token=self.mail_token('reset')
        self.app.security.complete(token,'reset','synthetic-new-password')
        with self.assertRaises(PermissionError): self.app.authenticate(self.token)
        with self.assertRaises(PermissionError): self.app.login('sample@example.com','synthetic-original-password')
        self.assertTrue(self.app.login('sample@example.com','synthetic-new-password'))
        with self.assertRaises(PermissionError): self.app.security.complete(token,'reset','another-test-password')
    def test_wrong_purpose_and_expiry(self):
        token=self.mail_token('verify')
        with self.assertRaises(PermissionError): self.app.security.complete(token,'reset','synthetic-new-password')
        with self.app.db: self.app.db.execute('UPDATE account_tokens SET expires=0')
        with self.assertRaises(PermissionError): self.app.security.complete(token,'verify')
    def test_reissue_invalidates_previous(self):
        token=self.mail_token('verify'); self.app.security.request('sample@example.com','verify')
        with self.assertRaises(PermissionError): self.app.security.complete(token,'verify')
        self.assertNotEqual(token,self.mail_token('verify'))
    def test_unknown_and_known_reset_responses_match(self):
        self.assertEqual(self.app.security.request('sample@example.com','reset'),self.app.security.request('unknown@example.com','reset'))
    def test_limit_survives_restart(self):
        for _ in range(10):
            with self.assertRaises(PermissionError): self.app.login('unknown@example.com','synthetic-password')
        self.app.store.close(); self.app=App(self.path)
        with self.assertRaises(ValueError): self.app.login('unknown@example.com','synthetic-password')
    def test_delivery_clears_mail_body_but_token_still_works(self):
        messages=[]; token=self.mail_token('verify')
        self.assertEqual(dispatch(self.app,messages.append)['sent'],1)
        self.assertIn('#verify=',messages[0].get_content())
        self.assertEqual(self.app.db.execute('SELECT body FROM account_mail').fetchone()[0],'')
        self.app.security.complete(token,'verify')
    def test_invalid_reset_password_does_not_consume_token(self):
        self.app.security.request('sample@example.com','reset'); token=self.mail_token('reset')
        with self.assertRaises(ValueError): self.app.security.complete(token,'reset','short')
        self.app.security.complete(token,'reset','synthetic-long-password')

if __name__=='__main__': unittest.main()
