import base64
import csv
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from server import App

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.app=App(Path(self.tmp.name)/'db'); self.s=self.app.store; self.f=self.app.workflows
        self.a=self.s.create_workspace('owner','Sample'); self.b=self.s.create_workspace('other','Other')
        self.p=self.s.add_partner('owner',self.a,'Referrer','referrer@example.com')
        self.q=self.s.add_partner('owner',self.a,'Second','second@example.com')
        self.data={'partner':self.p,'prospect':'Sample prospect','company':'Example Co','email':'prospect@example.com','phone':'123456789','service':'Design','introduced':'2026-10-10','estimate':'1000','source':'Sample','notes':'Synthetic'}
        self.r=self.f.submit('owner',self.a,self.data)['id']; self.s.set_terms('owner',self.a,self.r,'percent','10','INR')
    def tearDown(self): self.s.close(); self.tmp.cleanup()
    def accept(self, referral=None):
        token=self.f.issue('owner',self.a,referral or self.r,'accept')['token']; self.f.accept(token); return token
    def won(self): self.accept(); self.f.stage('owner',self.a,self.r,'Won')
    def test_acceptance_preview_replay_and_first_claim(self):
        token=self.f.issue('owner',self.a,self.r,'accept')['token']
        self.assertEqual(self.f.preview(token)['referral'][1],'Example Co')
        self.f.accept(token)
        with self.assertRaises(PermissionError): self.f.accept(token)
        duplicate=self.f.submit('owner',self.a,{**self.data,'partner':self.q,'confirm_duplicate':True})['id']
        self.s.set_terms('owner',self.a,duplicate,'fixed','50','INR')
        second=self.f.issue('owner',self.a,duplicate,'accept')['token']
        with self.assertRaises(sqlite3.IntegrityError): self.f.accept(second)
        self.assertEqual(self.f.summary('owner',self.a,duplicate)['stage'],'Submitted')
    def test_expired_and_reissued_capabilities(self):
        first=self.f.issue('owner',self.a,self.r,'accept')['token']
        second=self.f.issue('owner',self.a,self.r,'accept')['token']
        with self.assertRaises(PermissionError): self.f.preview(first)
        with self.s.db: self.s.db.execute('UPDATE capabilities SET expires=0')
        with self.assertRaises(PermissionError): self.f.preview(second)
    def test_private_portal_only_selected_partner(self):
        other=self.s.add_referral('owner',self.a,self.q,'Hidden prospect')
        token=self.f.issue('owner',self.a,self.p,'portal')['token']
        items=self.f.portal(token)['items']
        self.assertEqual([x['id'] for x in items],[self.r]); self.assertNotIn(other,str(items))
        with self.assertRaises(PermissionError): self.f.issue('other',self.a,self.p,'portal')
    def test_duplicate_warning_does_not_insert(self):
        result=self.f.submit('owner',self.a,self.data)
        self.assertEqual(result['duplicates'],[self.r]); self.assertNotIn('id',result)
        self.assertEqual(len(self.s.list_referrals('owner',self.a)),1)
    def test_approval_due_and_overdue(self):
        self.won(); self.f.payment('owner',self.a,self.r,{'kind':'revenue','amount':'500','request_id':'r'})
        with self.assertRaises(ValueError): self.f.payment('owner',self.a,self.r,{'kind':'commission','amount':'10','request_id':'p'})
        self.f.approve('owner',self.a,self.r,'2026-10-15')
        for day,status in [('2026-10-14','Approved'),('2026-10-15','Due'),('2026-10-16','Overdue')]:
            self.assertEqual(self.f.summary('owner',self.a,self.r,day)['commission_status'],status)
        self.f.payment('owner',self.a,self.r,{'kind':'commission','amount':'50','request_id':'p'})
        self.assertEqual(self.f.summary('owner',self.a,self.r)['commission_status'],'Paid')
    def test_outbox_retry_and_no_network_delivery(self):
        self.won()
        data={'kind':'revenue','amount':'100','request_id':'unique'}
        self.f.payment('owner',self.a,self.r,data); self.f.payment('owner',self.a,self.r,data)
        self.assertEqual(self.s.db.execute("SELECT count(*) FROM outbox WHERE event='payment.unique'").fetchone()[0],1)
        self.assertEqual(self.s.db.execute("SELECT count(*) FROM outbox WHERE status!='pending'").fetchone()[0],0)
    def test_evidence_validation_and_access(self):
        evidence=self.f.add_evidence('owner',self.a,self.r,{'name':'sample.txt','content':base64.b64encode(b'Synthetic evidence').decode()})
        self.assertEqual(self.f.evidence('owner',self.a,self.r,evidence['id'])['name'],'sample.txt')
        with self.assertRaises(PermissionError): self.f.evidence('other',self.a,self.r,evidence['id'])
        for name,content in [('x.html',b'<script>'),('../x.txt',b'bad'),('fake.pdf',b'not pdf')]:
            with self.assertRaises(ValueError): self.f.add_evidence('owner',self.a,self.r,{'name':name,'content':base64.b64encode(content).decode()})
    def test_monthly_statement_opening_and_csv_safety(self):
        with self.s.db:
            self.s.db.execute("UPDATE referrals SET prospect='=HYPERLINK(1)' WHERE id=?",(self.r,))
            self.s.db.execute("INSERT INTO payments VALUES('a',?,'revenue',10000,'2026-09-30 00:00:00')",(self.r,))
            self.s.db.execute("INSERT INTO payments VALUES('b',?,'revenue',20000,'2026-10-01 00:00:00')",(self.r,))
            self.s.db.execute("INSERT INTO payments VALUES('c',?,'commission',500,'2026-10-02 00:00:00')",(self.r,))
        result=self.f.statement('owner',self.a,self.p,'2026-10')
        row=list(csv.reader(io.StringIO(result['csv'])))[1]
        self.assertTrue(row[1].startswith("'=")); self.assertEqual(row[3:],['10.00','200.00','20.00','5.00','25.00'])
        with self.assertRaises(PermissionError): self.f.statement('other',self.a,self.p,'2026-10')
    def test_payment_and_notification_rollback_together(self):
        self.won()
        original=self.f.notify
        def fail(*args): raise RuntimeError('Synthetic outbox failure')
        self.f.notify=fail
        with self.assertRaises(RuntimeError): self.f.payment('owner',self.a,self.r,{'kind':'revenue','amount':'100','request_id':'atomic'})
        self.f.notify=original
        self.assertEqual(self.s.ledger('owner',self.a,self.r)['revenue'],0)

    def test_legacy_completion_preserves_identity_and_ledger(self):
        legacy=self.s.add_referral('owner',self.a,self.q,'Original prospect')
        self.s.set_terms('owner',self.a,legacy,'fixed','50','INR')
        self.s.record_payment('owner',self.a,legacy,'revenue','500','legacy-revenue')
        self.f.submit('owner',self.a,{**self.data,'company':'Other Co','email':'other@example.com','phone':'','confirm_duplicate':True},legacy=legacy)
        row=self.s.db.execute('SELECT partner,prospect FROM referrals WHERE id=?',(legacy,)).fetchone()
        self.assertEqual(row,(self.q,'Original prospect'))
        self.assertEqual(self.s.ledger('owner',self.a,legacy)['revenue'],50000)
        with self.assertRaises(ValueError): self.f.submit('owner',self.a,self.data,legacy=legacy)

    def test_stage_and_term_guards(self):
        with self.assertRaises(ValueError): self.f.stage('owner',self.a,self.r,'Won')
        with self.assertRaises(ValueError): self.f.payment('owner',self.a,self.r,{'kind':'revenue','amount':'1','request_id':'a'})
        with self.assertRaises(sqlite3.IntegrityError): self.s.set_terms('owner',self.a,self.r,'fixed','5','INR')
        self.s.db.rollback()
        with self.assertRaises(sqlite3.IntegrityError): self.s.db.execute('DELETE FROM terms')
        self.s.db.rollback()

if __name__=='__main__': unittest.main()
