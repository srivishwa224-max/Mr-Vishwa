"""Duplicate warnings use normalized local identities, never another tenant's IDs."""
import tempfile
import unittest
from pathlib import Path
from store import Store
from workflows import Workflows


class DuplicateIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Store(Path(self.tmp.name) / 'synthetic.sqlite')
        self.s.init_ledger()
        self.f = Workflows(self.s)
        self.a = self.s.create_workspace('alice', 'Synthetic A')
        self.b = self.s.create_workspace('bob', 'Synthetic B')
        self.pa = self.s.add_partner('alice', self.a, 'Sample A', 'a@example.com')
        self.pb = self.s.add_partner('bob', self.b, 'Sample B', 'b@example.com')
        self.original = self.data(self.pa, company='Example Co.',
                                  email='Lead@Example.com', phone='+1 (555) 123-4567')
        self.r = self.f.submit('alice', self.a, self.original)['id']

    def tearDown(self):
        self.s.close()
        self.tmp.cleanup()

    def data(self, partner, **changes):
        return dict({'partner': partner, 'prospect': 'Synthetic prospect',
                     'company': 'Different Company', 'email': 'different@example.com',
                     'phone': '7778889999', 'service': 'Sample',
                     'introduced': '2026-10-18', 'estimate': '100'}, **changes)

    def snapshot(self):
        return {table: self.s.db.execute('SELECT * FROM ' + table).fetchall()
                for table in ('referrals', 'referral_details', 'activity')}

    def test_each_normalized_key_warns_without_writes(self):
        for fields in ({'company': '  EXAMPLE-co '},
                       {'email': '  LEAD@EXAMPLE.COM '},
                       {'phone': '1-555-123-4567'}):
            with self.subTest(fields=fields):
                before = self.snapshot()
                result = self.f.submit('alice', self.a, self.data(self.pa, **fields))
                self.assertEqual(result, {'duplicates': [self.r]})
                self.assertEqual(self.snapshot(), before)

    def test_identical_other_workspace_is_not_disclosed(self):
        remote = self.f.submit('bob', self.b, {**self.original, 'partner': self.pb})
        self.assertEqual(remote['duplicates'], [])
        self.assertNotEqual(remote['id'], self.r)
        result = self.f.submit('bob', self.b, {**self.original, 'partner': self.pb})
        self.assertEqual(result, {'duplicates': [remote['id']]})
        self.assertNotIn(self.r, str(result))

    def test_unauthorized_actor_denied_before_duplicate_lookup(self):
        before = self.snapshot()
        with self.assertRaises(PermissionError):
            self.f.submit('bob', self.a, self.original)
        self.assertEqual(self.snapshot(), before)

    def test_explicit_confirmation_creates_only_local_duplicate(self):
        before = len(self.s.list_referrals('alice', self.a))
        result = self.f.submit('alice', self.a, {**self.original, 'confirm_duplicate': True})
        self.assertEqual(result['duplicates'], [self.r])
        self.assertNotEqual(result['id'], self.r)
        self.assertEqual(len(self.s.list_referrals('alice', self.a)), before + 1)
        self.assertEqual(self.s.list_referrals('bob', self.b), [])

    def test_empty_and_short_contacts_do_not_match_unrelated_companies(self):
        self.f.submit('alice', self.a, self.data(self.pa, company='First', email='', phone='123'))
        result = self.f.submit('alice', self.a, self.data(self.pa, company='Second', email='', phone='123'))
        self.assertEqual(result['duplicates'], [])


if __name__ == '__main__':
    unittest.main()
