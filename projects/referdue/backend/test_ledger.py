import tempfile
import unittest
from pathlib import Path
from store import Store

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.s=Store(Path(self.tmp.name)/'db'); self.s.init_ledger()
        self.w=self.s.create_workspace('owner','Sample'); p=self.s.add_partner('owner',self.w,'Sample','sample@example.com')
        self.r=self.s.add_referral('owner',self.w,p,'Prospect')
    def tearDown(self): self.s.close(); self.tmp.cleanup()
    def pay(self,kind,amount,key): return self.s.record_payment('owner',self.w,self.r,kind,amount,key)
    def test_percentage_partial_payment_and_retry(self):
        self.s.set_terms('owner',self.w,self.r,'percent','10','INR')
        self.assertEqual(self.pay('revenue','500','r1')['due'],5000)
        self.assertEqual(self.pay('commission','20','p1')['due'],3000)
        self.assertEqual(self.pay('commission','20','p1')['due'],3000)
        with self.assertRaises(ValueError): self.pay('commission','40','p2')
        self.assertEqual(self.pay('commission','30','p3')['due'],0)
        self.assertEqual(len(self.s.ledger('owner',self.w,self.r)['events']),3)
    def test_fixed_no_payment_before_revenue(self):
        self.s.set_terms('owner',self.w,self.r,'fixed','100','INR')
        with self.assertRaises(ValueError): self.pay('commission','1','p1')
        self.pay('revenue','10','r1')
        self.assertEqual(self.pay('revenue','20','r2')['earned'],10000)
    def test_validation_and_access(self):
        for amount in ['0.001','NaN','Infinity','-1','0']:
            with self.assertRaises(ValueError): self.pay('revenue',amount,'bad')
        with self.assertRaises(PermissionError): self.s.ledger('outsider',self.w,self.r)
        with self.assertRaises(ValueError): self.pay('revenue','10','before-terms')
    def test_cent_rounding_and_id_conflict(self):
        self.s.set_terms('owner',self.w,self.r,'percent','7.5','USD')
        self.assertEqual(self.pay('revenue','199.99','one')['earned'],1500)
        with self.assertRaises(ValueError): self.pay('revenue','200','one')
        self.assertEqual(self.s.ledger('owner',self.w,self.r)['revenue'],19999)

if __name__=='__main__': unittest.main()
