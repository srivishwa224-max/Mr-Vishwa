import tempfile
import unittest
from pathlib import Path
from server import App
from notifications import dispatch

class NotificationTests(unittest.TestCase):
    def test_dry_run_failure_and_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=App(Path(tmp)/'db')
            try:
                with app.db: app.db.execute("INSERT INTO outbox(workspace,recipient,event,referral) VALUES('sample','sample@example.com','referral.accepted','sample-referral')")
                self.assertEqual(dispatch(app),{'pending_seen':1,'sent':0,'dry_run':True})
                def fail(message): raise RuntimeError('Synthetic transport failure')
                with self.assertRaises(RuntimeError): dispatch(app,fail)
                delivered=[]
                self.assertEqual(dispatch(app,delivered.append)['sent'],1)
                self.assertEqual(delivered[0]['To'],'sample@example.com')
                self.assertEqual(dispatch(app,delivered.append)['pending_seen'],0)
                self.assertEqual(len(delivered),1)
            finally: app.store.close()

if __name__=='__main__': unittest.main()
