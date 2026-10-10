import concurrent.futures
import tempfile
import threading
import unittest
from pathlib import Path
from store import Store
from workflows import Workflows

class ConcurrentPayments(unittest.TestCase):
    def test_two_connections_cannot_overpay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'db'; s=Store(path); s.init_ledger()
            workspace=s.create_workspace('owner','Sample'); partner=s.add_partner('owner',workspace,'Sample','sample@example.com')
            referral=s.add_referral('owner',workspace,partner,'Prospect'); s.set_terms('owner',workspace,referral,'fixed','10','INR')
            s.record_payment('owner',workspace,referral,'revenue','100','rev'); s.close()
            gate=threading.Barrier(2)
            def pay(key):
                connection=Store(path)
                try:
                    gate.wait(timeout=5)
                    try: connection.record_payment('owner',workspace,referral,'commission','10',key); return 'paid'
                    except ValueError: return 'rejected'
                finally: connection.close()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                outcomes=list(pool.map(pay,['one','two']))
            self.assertEqual(sorted(outcomes),['paid','rejected'])
            s=Store(path)
            try: self.assertEqual(s.ledger('owner',workspace,referral)['paid'],1000)
            finally: s.close()

if __name__=='__main__': unittest.main()
