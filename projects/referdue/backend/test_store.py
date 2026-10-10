import tempfile
import unittest
import sqlite3
from pathlib import Path
from store import Store

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'test.sqlite'
        self.store = Store(self.path)
        self.a = self.store.create_workspace('owner-a','Workspace A')
        self.b = self.store.create_workspace('owner-b','Workspace B')
        self.partner = self.store.add_partner('owner-a',self.a,'Sample Partner','partner@example.com')

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_persists_after_reopen(self):
        key = self.store.add_referral('owner-a',self.a,self.partner,'Sample prospect')
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual(self.store.list_referrals('owner-a',self.a)[0][0],key)

    def test_cross_workspace_read_and_write_denied(self):
        with self.assertRaises(PermissionError): self.store.list_referrals('owner-b',self.a)
        with self.assertRaises(PermissionError): self.store.add_partner('owner-b',self.a,'X','x@example.com')
        with self.assertRaises(PermissionError): self.store.history('owner-b',self.a)

    def test_only_owner_can_add_members(self):
        self.store.add_member('owner-a',self.a,'teammate')
        with self.assertRaises(PermissionError): self.store.add_member('teammate',self.a,'outsider')
        self.store.add_referral('teammate',self.a,self.partner,'Synthetic opportunity')
        self.assertEqual(len(self.store.list_referrals('teammate',self.a)),1)

    def test_cross_workspace_partner_rejected_and_rolled_back(self):
        before = self.store.history('owner-b',self.b)
        with self.assertRaises(sqlite3.IntegrityError): self.store.add_referral('owner-b',self.b,self.partner,'X')
        self.assertEqual(self.store.list_referrals('owner-b',self.b),[])
        self.assertEqual(self.store.history('owner-b',self.b),before)

    def test_audit_cannot_be_updated_or_deleted(self):
        for statement in ['UPDATE activity SET action="changed"','DELETE FROM activity']:
            with self.assertRaises(sqlite3.IntegrityError): self.store.db.execute(statement)
            self.store.db.rollback()

    def test_sql_injection_is_literal_text(self):
        self.store.add_referral('owner-a',self.a,self.partner,"'); DROP TABLE referrals; --")
        self.assertEqual(len(self.store.list_referrals('owner-a',self.a)),1)

if __name__ == '__main__': unittest.main()
