import unittest
from datetime import date
from decimal import Decimal

from app import create_app
from models import db
from models.expense import Expense
from models.income import Income
from models.user import User
from tests.test_auth import TestConfig


class RemainingModulesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                name="Module User",
                email="module@example.com",
                monthly_budget=Decimal("1000.00"),
            )
            self.user.set_password("secure-pass-123")
            self.other_user = User(
                name="Other User",
                email="other-module@example.com",
            )
            self.other_user.set_password("secure-pass-123")
            db.session.add_all([self.user, self.other_user])
            db.session.commit()
            self.user_id = self.user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def login(self):
        return self.client.post(
            "/login",
            data={
                "email": "module@example.com",
                "password": "secure-pass-123",
            },
        )

    def seed_transactions(self):
        with self.app.app_context():
            db.session.add_all(
                [
                    Income(
                        amount=Decimal("5000.00"),
                        source="Salary",
                        description="Monthly salary",
                        income_date=date.today(),
                        user_id=self.user_id,
                    ),
                    Expense(
                        amount=Decimal("750.00"),
                        category="Food",
                        description="Groceries",
                        expense_date=date.today(),
                        user_id=self.user_id,
                    ),
                ]
            )
            db.session.commit()

    def test_ai_advisor_requires_login_and_renders_local_advice(self):
        self.assertEqual(self.client.get("/ai/advisor").status_code, 302)
        self.seed_transactions()
        self.login()

        response = self.client.get("/ai/advisor")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Budget Advisor", response.data)
        self.assertIn(b"Local Advisor", response.data)
        self.assertIn("₹5,000.00".encode(), response.data)

    def test_reports_render_and_export(self):
        self.seed_transactions()
        self.login()

        response = self.client.get("/reports/")
        csv_response = self.client.get("/reports/export.csv")
        pdf_response = self.client.get("/reports/export.pdf")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reports", response.data)
        self.assertIn(b"Monthly salary", response.data)
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn(b"Monthly salary", csv_response.data)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response.mimetype, "application/pdf")

    def test_profile_edit_and_duplicate_email_validation(self):
        self.login()
        response = self.client.post(
            "/profile",
            data={
                "name": "Updated User",
                "email": "updated@example.com",
                "currency": "INR",
                "monthly_budget": "3000.00",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Profile updated successfully.", response.data)
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            self.assertEqual(user.name, "Updated User")
            self.assertEqual(user.email, "updated@example.com")
            self.assertEqual(user.monthly_budget, Decimal("3000.00"))

        duplicate_response = self.client.post(
            "/profile",
            data={
                "name": "Updated User",
                "email": "other-module@example.com",
                "currency": "INR",
                "monthly_budget": "3000.00",
            },
        )
        self.assertEqual(duplicate_response.status_code, 422)
        self.assertIn(b"This email address is already in use.", duplicate_response.data)


if __name__ == "__main__":
    unittest.main()
