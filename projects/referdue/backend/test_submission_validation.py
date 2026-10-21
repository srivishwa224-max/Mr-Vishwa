import tempfile
import unittest
from pathlib import Path

from server import App


class SubmissionValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = App(Path(self.tmp.name) / "db")
        self.store = self.app.store
        self.workflows = self.app.workflows
        self.workspace = self.store.create_workspace("owner", "Sample")
        self.other_workspace = self.store.create_workspace("other", "Other")
        self.partner = self.store.add_partner(
            "owner", self.workspace, "Referrer", "referrer@example.com"
        )
        self.other_partner = self.store.add_partner(
            "other", self.other_workspace, "Other", "other@example.com"
        )
        self.data = {
            "partner": self.partner,
            "prospect": "  Sample prospect  ",
            "company": "  Example Co  ",
            "email": "  Prospect@Example.COM  ",
            "phone": "  +91 98765 43210  ",
            "service": "  Design  ",
            "introduced": "  2026-10-21  ",
            "estimate": "1000.25",
            "source": "  Conference  ",
            "notes": "  Synthetic only  ",
        }

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def counts(self):
        return {
            table: self.store.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("referrals", "referral_details", "activity")
        }

    def test_all_submission_fields_are_normalized_and_persisted(self):
        referral = self.workflows.submit("owner", self.workspace, self.data)["id"]
        referral_row = self.store.db.execute(
            "SELECT workspace,partner,prospect FROM referrals WHERE id=?", (referral,)
        ).fetchone()
        details = self.store.db.execute(
            "SELECT company,email,phone,service,introduced,source,notes,estimate,identity,stage "
            "FROM referral_details WHERE referral=?",
            (referral,),
        ).fetchone()
        self.assertEqual(
            referral_row, (self.workspace, self.partner, "Sample prospect")
        )
        self.assertEqual(
            details,
            (
                "Example Co",
                "prospect@example.com",
                "+91 98765 43210",
                "Design",
                "2026-10-21",
                "Conference",
                "Synthetic only",
                100025,
                "email:prospect@example.com",
                "Submitted",
            ),
        )
        self.assertEqual(
            self.store.db.execute(
                "SELECT action,entity FROM activity WHERE workspace=? AND action='referral.submitted'",
                (self.workspace,),
            ).fetchall(),
            [("referral.submitted", referral)],
        )

    def test_required_and_formatted_values_fail_without_writes(self):
        baseline = self.counts()
        cases = [
            ("company", " "),
            ("service", ""),
            ("introduced", "2026-02-30"),
            ("email", "not-an-email"),
            ("estimate", "0"),
            ("notes", "x" * 2001),
            ("source", 7),
            ("partner", ""),
            ("prospect", " "),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.workflows.submit(
                        "owner", self.workspace, {**self.data, field: value}
                    )
                self.assertEqual(self.counts(), baseline)

    def test_unauthorized_actor_and_foreign_partner_cannot_create_referral(self):
        baseline = self.counts()
        with self.assertRaises(PermissionError):
            self.workflows.submit("other", self.workspace, self.data)
        self.assertEqual(self.counts(), baseline)

        with self.assertRaises(PermissionError):
            self.workflows.submit(
                "owner", self.workspace, {**self.data, "partner": self.other_partner}
            )
        self.assertEqual(self.counts(), baseline)


if __name__ == "__main__":
    unittest.main()
