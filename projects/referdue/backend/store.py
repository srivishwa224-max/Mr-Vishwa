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
