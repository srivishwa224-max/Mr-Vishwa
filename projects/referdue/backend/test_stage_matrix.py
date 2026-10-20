"""Synthetic checks for every documented manual referral-stage transition."""
import tempfile
import unittest
from pathlib import Path
from store import Store
from workflows import Workflows


class StageMatrixTests(unittest.TestCase):
    allowed = {'Submitted': {'Lost'}, 'Accepted': {'Contacted', 'Won', 'Lost'},
               'Contacted': {'Won', 'Lost'}, 'Won': set(), 'Lost': set()}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Store(Path(self.tmp.name) / 'synthetic.sqlite')
        self.s.init_ledger()
        self.f = Workflows(self.s)
        self.w = self.s.create_workspace('owner', 'Synthetic')
        self.p = self.s.add_partner('owner', self.w, 'Sample', 'sample@example.com')

    def tearDown(self):
        self.s.close()
        self.tmp.cleanup()

    def referral_at(self, stage):
        r = self.f.submit('owner', self.w, {
            'partner': self.p, 'prospect': 'Synthetic', 'company': 'Sample',
            'service': 'Sample', 'introduced': '2026-10-20', 'estimate': '100',
            'confirm_duplicate': True})['id']
        # Fixture-only state placement isolates the transition under test.
        with self.s.db:
            self.s.db.execute('UPDATE referral_details SET stage=? WHERE referral=?', (stage, r))
        return r

    def snapshot(self):
        return {table: self.s.db.execute('SELECT * FROM ' + table).fetchall()
                for table in ('referral_details', 'activity', 'outbox')}

    def test_manual_transition_matrix(self):
        targets = list(self.allowed) + ['Customer Paid', 'Commission Due', 'Commission Paid', 'Unknown']
        for source, allowed in self.allowed.items():
            for target in targets:
                with self.subTest(source=source, target=target):
                    r = self.referral_at(source)
                    before = self.snapshot()
                    if target not in allowed:
                        with self.assertRaises(ValueError):
                            self.f.stage('owner', self.w, r, target)
                        self.assertEqual(self.snapshot(), before)
                    else:
                        self.assertEqual(self.f.stage('owner', self.w, r, target), {'ok': True})
                        self.assertEqual(self.s.db.execute('SELECT stage FROM referral_details WHERE referral=?',
                                                          (r,)).fetchone(), (target,))
                        after = self.snapshot()
                        self.assertEqual(after['activity'][:-1], before['activity'])
                        self.assertEqual(after['outbox'][:-1], before['outbox'])
                        self.assertEqual(after['activity'][-1][2:5], ('owner', 'stage.' + target, r))
                        self.assertEqual(after['outbox'][-1][1:5],
                                         (self.w, 'sample@example.com', 'stage.' + target, r))

    def test_unauthorized_transition_has_no_effects(self):
        r = self.referral_at('Accepted')
        before = self.snapshot()
        with self.assertRaises(PermissionError):
            self.f.stage('outsider', self.w, r, 'Won')
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
