"""Synthetic two-connection acceptance races; no network or real records."""
import concurrent.futures
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from store import Store
from workflows import Workflows


class AcceptanceConcurrencyTests(unittest.TestCase):
    def run_race(self, same_token):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.sqlite'
            setup = Store(path)
            setup.init_ledger()
            workflow = Workflows(setup)
            workspace = setup.create_workspace('owner', 'Synthetic workspace')
            partner = setup.add_partner('owner', workspace, 'Sample', 'sample@example.com')
            referrals, tokens = [], []
            for index in range(1 if same_token else 2):
                # Different companies insert a non-conflicting key BEFORE the
                # shared email collides, exercising partial-write rollback.
                referral = workflow.submit('owner', workspace, {
                    'partner': partner, 'prospect': 'Synthetic prospect',
                    'company': 'Company ' + str(index), 'email': 'shared@example.com',
                    'phone': '555000' + str(index), 'service': 'Sample',
                    'introduced': '2026-10-17', 'estimate': '100',
                    'confirm_duplicate': True,
                })['id']
                setup.set_terms('owner', workspace, referral, 'fixed', '10', 'INR')
                referrals.append(referral)
                tokens.append(workflow.issue('owner', workspace, referral, 'accept')['token'])
            baseline_activity = setup.db.execute('SELECT count(*) FROM activity').fetchone()[0]
            setup.close()
            gate = threading.Barrier(2)

            def accept(index):
                connection = Store(path)
                try:
                    worker = Workflows(connection)
                    gate.wait(timeout=10)
                    try:
                        worker.accept(tokens[0 if same_token else index])
                        return index, 'accepted'
                    except (PermissionError, sqlite3.IntegrityError) as error:
                        return index, type(error).__name__
                finally:
                    connection.close()

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(accept, range(2)))
            expected_error = 'PermissionError' if same_token else 'IntegrityError'
            self.assertEqual(sorted(result for _, result in results),
                             sorted(['accepted', expected_error]))
            winner_index = next(index for index, result in results if result == 'accepted')
            winner = referrals[0 if same_token else winner_index]
            check = Store(path)
            try:
                db = check.db
                self.assertEqual(db.execute('SELECT referral FROM claims').fetchall(), [(winner,)])
                keys = db.execute('SELECT identity,referral FROM attribution_keys').fetchall()
                self.assertEqual(len(keys), 3)
                self.assertEqual({referral for _, referral in keys}, {winner})
                self.assertEqual(db.execute('SELECT referral FROM outbox').fetchall(), [(winner,)])
                self.assertEqual(db.execute('SELECT entity FROM activity WHERE action=?',
                                            ('referral.accepted',)).fetchall(), [(winner,)])
                self.assertEqual(db.execute('SELECT count(*) FROM activity').fetchone()[0],
                                 baseline_activity + 1)
                for referral in referrals:
                    won = referral == winner
                    self.assertEqual(db.execute('SELECT stage FROM referral_details WHERE referral=?',
                                                (referral,)).fetchone()[0],
                                     'Accepted' if won else 'Submitted')
                    self.assertEqual(db.execute('SELECT consumed FROM capabilities WHERE target=?',
                                                (referral,)).fetchone()[0], int(won))
                again = Workflows(check)
                with self.assertRaises(PermissionError):
                    again.accept(tokens[0 if same_token else winner_index])
            finally:
                check.close()

    def test_competing_introductions_are_atomic(self):
        self.run_race(False)

    def test_same_token_is_consumed_once(self):
        self.run_race(True)


if __name__ == '__main__':
    unittest.main()
