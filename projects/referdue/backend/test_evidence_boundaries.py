"""Synthetic attachment boundaries and referral/workspace access checks."""
import base64
import tempfile
import unittest
from pathlib import Path
from store import Store
from workflows import Workflows


class EvidenceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Store(Path(self.tmp.name) / 'synthetic.sqlite')
        self.s.init_ledger()
        self.f = Workflows(self.s)
        self.a = self.s.create_workspace('alice', 'Synthetic A')
        self.b = self.s.create_workspace('bob', 'Synthetic B')
        pa = self.s.add_partner('alice', self.a, 'A', 'a@example.com')
        pb = self.s.add_partner('bob', self.b, 'B', 'b@example.com')
        self.ra = self.s.add_referral('alice', self.a, pa, 'A')
        self.ra2 = self.s.add_referral('alice', self.a, pa, 'A2')
        self.rb = self.s.add_referral('bob', self.b, pb, 'B')

    def tearDown(self):
        self.s.close()
        self.tmp.cleanup()

    def payload(self, raw, name='sample.txt'):
        return {'name': name, 'content': base64.b64encode(raw).decode('ascii')}

    def snapshot(self):
        return {table: self.s.db.execute('SELECT * FROM ' + table).fetchall()
                for table in ('evidence', 'activity')}

    def test_exact_one_mib_round_trip(self):
        raw = b'x' * 1048576
        before = len(self.s.history('alice', self.a))
        key = self.f.add_evidence('alice', self.a, self.ra, self.payload(raw))['id']
        result = self.f.evidence('alice', self.a, self.ra, key)
        self.assertEqual(base64.b64decode(result['content']), raw)
        self.assertEqual(result['name'], 'sample.txt')
        self.assertEqual(self.f.evidence('alice', self.a, self.ra)['items'],
                         [(key, 'sample.txt', 1048576)])
        self.assertEqual(len(self.s.history('alice', self.a)), before + 1)

    def test_invalid_and_oversized_payloads_leave_no_writes(self):
        cases = [self.payload(b'x' * 1048577), self.payload(b''),
                 {'name': 'sample.txt', 'content': '!' * 1400001},
                 {'name': 'sample.txt', 'content': 'not base64!'},
                 self.payload(b'not a pdf', 'sample.pdf'),
                 self.payload(b'bad', '../sample.txt')]
        for data in cases:
            with self.subTest(name=data['name'], length=len(data['content'])):
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.f.add_evidence('alice', self.a, self.ra, data)
                self.assertEqual(self.snapshot(), before)

    def test_unauthorized_upload_list_and_download_are_denied(self):
        key = self.f.add_evidence('alice', self.a, self.ra, self.payload(b'synthetic'))['id']
        before = self.snapshot()
        with self.assertRaises(PermissionError):
            self.f.add_evidence('bob', self.a, self.ra, self.payload(b'blocked'))
        for evidence_id in (None, key):
            with self.assertRaises(PermissionError):
                self.f.evidence('bob', self.a, self.ra, evidence_id)
        self.assertEqual(self.snapshot(), before)

    def test_attachment_id_cannot_cross_referral_or_workspace(self):
        key = self.f.add_evidence('alice', self.a, self.ra, self.payload(b'synthetic'))['id']
        for actor, workspace, referral in [('alice', self.a, self.ra2),
                                            ('bob', self.b, self.rb)]:
            with self.subTest(actor=actor):
                self.assertEqual(self.f.evidence(actor, workspace, referral)['items'], [])
                with self.assertRaises(PermissionError):
                    self.f.evidence(actor, workspace, referral, key)
        with self.assertRaises(PermissionError):
            self.f.add_evidence('alice', self.a, self.rb, self.payload(b'blocked'))


if __name__ == '__main__':
    unittest.main()
