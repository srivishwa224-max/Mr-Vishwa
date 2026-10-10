"""Local-testable persistence boundary. Actor IDs must come from trusted auth, never request data."""
import sqlite3
import uuid


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS workspaces(id TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS members(workspace TEXT REFERENCES workspaces(id), actor TEXT,
          role TEXT NOT NULL CHECK(role IN ('owner','team')), PRIMARY KEY(workspace,actor));
        CREATE TABLE IF NOT EXISTS partners(id TEXT PRIMARY KEY, workspace TEXT NOT NULL REFERENCES workspaces(id),
          name TEXT NOT NULL, email TEXT NOT NULL, UNIQUE(workspace,id));
        CREATE TABLE IF NOT EXISTS referrals(id TEXT PRIMARY KEY, workspace TEXT NOT NULL, partner TEXT NOT NULL,
          prospect TEXT NOT NULL, FOREIGN KEY(workspace,partner) REFERENCES partners(workspace,id));
        CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY, workspace TEXT NOT NULL,
          actor TEXT NOT NULL, action TEXT NOT NULL, entity TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TRIGGER IF NOT EXISTS activity_no_update BEFORE UPDATE ON activity
          BEGIN SELECT RAISE(ABORT,'Activity is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS activity_no_delete BEFORE DELETE ON activity
          BEGIN SELECT RAISE(ABORT,'Activity is append-only'); END;
        ''')

    def close(self):
        self.db.close()

    def _authorize(self, actor, workspace, owner=False):
        row = self.db.execute('SELECT role FROM members WHERE workspace=? AND actor=?', (workspace,actor)).fetchone()
        if row is None or (owner and row[0] != 'owner'):
            raise PermissionError('Access denied')

    def _log(self, actor, workspace, action, entity):
        self.db.execute('INSERT INTO activity(workspace,actor,action,entity) VALUES(?,?,?,?)',
                        (workspace,actor,action,entity))

    @staticmethod
    def _text(value):
        if not isinstance(value,str) or not value.strip() or len(value)>500:
            raise ValueError('Required text must contain 1–500 characters')
        return value.strip()

    def create_workspace(self, actor, name):
        actor, name = self._text(actor), self._text(name)
        key = str(uuid.uuid4())
        with self.db:
            self.db.execute('INSERT INTO workspaces VALUES(?,?)', (key,name))
            self.db.execute('INSERT INTO members VALUES(?,?,?)', (key,actor,'owner'))
            self._log(actor,key,'workspace.created',key)
        return key

    def add_member(self, actor, workspace, member):
        self._authorize(actor,workspace,owner=True)
        member = self._text(member)
        with self.db:
            self.db.execute('INSERT INTO members VALUES(?,?,?)', (workspace,member,'team'))
            self._log(actor,workspace,'member.added',member)

    def add_partner(self, actor, workspace, name, email):
        self._authorize(actor,workspace)
        name, email = self._text(name), self._text(email)
        key = str(uuid.uuid4())
        with self.db:
            self.db.execute('INSERT INTO partners VALUES(?,?,?,?)', (key,workspace,name,email))
            self._log(actor,workspace,'partner.created',key)
        return key

    def add_referral(self, actor, workspace, partner, prospect):
        self._authorize(actor,workspace)
        prospect = self._text(prospect)
        key = str(uuid.uuid4())
        with self.db:
            self.db.execute('INSERT INTO referrals VALUES(?,?,?,?)', (key,workspace,partner,prospect))
            self._log(actor,workspace,'referral.created',key)
        return key

    def list_referrals(self, actor, workspace):
        self._authorize(actor,workspace)
        return self.db.execute('SELECT id,partner,prospect FROM referrals WHERE workspace=? ORDER BY id', (workspace,)).fetchall()

    def history(self, actor, workspace):
        self._authorize(actor,workspace)
        return self.db.execute('SELECT actor,action,entity,created_at FROM activity WHERE workspace=? ORDER BY id', (workspace,)).fetchall()

    def init_ledger(self):
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS terms(referral TEXT PRIMARY KEY REFERENCES referrals(id), kind TEXT NOT NULL CHECK(kind IN ('fixed','percent')), value INTEGER NOT NULL CHECK(value>0), currency TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS payments(id TEXT PRIMARY KEY, referral TEXT NOT NULL REFERENCES referrals(id), kind TEXT NOT NULL CHECK(kind IN ('revenue','commission')), cents INTEGER NOT NULL CHECK(cents>0), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        ''')

    @staticmethod
    def cents(value):
        from decimal import Decimal, InvalidOperation
        try:
            amount=Decimal(str(value))
            if not amount.is_finite() or amount<=0 or amount>Decimal('1000000000') or amount*100 != (amount*100).to_integral_value(): raise ValueError('Invalid amount')
            return int(amount*100)
        except (InvalidOperation, TypeError): raise ValueError('Invalid amount')

    def _referral_access(self, actor, workspace, referral):
        self._authorize(actor,workspace)
        if not self.db.execute('SELECT 1 FROM referrals WHERE id=? AND workspace=?',(referral,workspace)).fetchone():
            raise PermissionError('Access denied')

    def set_terms(self, actor, workspace, referral, kind, value, currency):
        self._referral_access(actor,workspace,referral)
        number=self.cents(value)
        if kind not in ('fixed','percent') or currency not in ('INR','USD','GBP','EUR') or (kind=='percent' and number>10000): raise ValueError('Invalid terms')
        with self.db:
            self.db.execute('INSERT INTO terms VALUES(?,?,?,?)',(referral,kind,number,currency))
            self._log(actor,workspace,'terms.recorded',referral)

    def ledger(self, actor, workspace, referral):
        self._referral_access(actor,workspace,referral)
        terms=self.db.execute('SELECT kind,value,currency FROM terms WHERE referral=?',(referral,)).fetchone()
        if not terms: return {'terms':None,'revenue':0,'earned':0,'paid':0,'due':0,'events':[]}
        events=self.db.execute('SELECT id,kind,cents,created_at FROM payments WHERE referral=? ORDER BY created_at,id',(referral,)).fetchall()
        revenue=sum(e[2] for e in events if e[1]=='revenue')
        paid=sum(e[2] for e in events if e[1]=='commission')
        earned=(revenue*terms[1]+5000)//10000 if terms[0]=='percent' else (terms[1] if revenue else 0)
        return {'terms':terms,'revenue':revenue,'earned':earned,'paid':paid,'due':earned-paid,'events':events}

    def record_payment(self, actor, workspace, referral, kind, amount, request_id):
        self._referral_access(actor,workspace,referral)
        if kind not in ('revenue','commission'): raise ValueError('Invalid payment type')
        cents=self.cents(amount)
        request_id=self._text(request_id)
        # Serialize the read/check/write sequence to prevent concurrent overpayment.
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            old=self.db.execute('SELECT referral,kind,cents FROM payments WHERE id=?',(request_id,)).fetchone()
            if old:
                if old!=(referral,kind,cents): raise ValueError('Request identifier conflict')
                return self.ledger(actor,workspace,referral)
            current=self.ledger(actor,workspace,referral)
            if not current['terms']: raise ValueError('Record terms first')
            if kind=='commission' and cents>current['due']: raise ValueError('Payment exceeds commission due')
            if kind=='revenue' and current['revenue']+cents>100000000000: raise ValueError('Revenue total too large')
            self.db.execute('INSERT INTO payments(id,referral,kind,cents) VALUES(?,?,?,?)',(request_id,referral,kind,cents))
            self._log(actor,workspace,'payment.'+kind,request_id)
        return self.ledger(actor,workspace,referral)
