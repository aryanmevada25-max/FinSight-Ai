import unittest
from datetime import date
from decimal import Decimal

from app import create_app
from models import db
from models.expense import Expense
from models.user import User
from tests.test_auth import TestConfig


class BudgetTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            self.app_user = User(name="Budget User", email="budget@example.com")
            self.app_user.set_password("secure-pass-123")
            db.create_all()
            db.session.add(self.app_user)
            db.session.commit()
            self.user_id = self.app_user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def login(self):
        return self.client.post(
            "/login",
            data={
                "email": "budget@example.com",
                "password": "secure-pass-123",
            },
        )

    def test_budget_page_requires_authentication(self):
        response = self.client.get("/budget/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_update_and_validate_monthly_budget(self):
        self.login()
        response = self.client.post(
            "/budget/",
            data={"monthly_budget": "25000.00"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Monthly budget updated successfully.", response.data)
        self.assertIn("₹25,000.00".encode(), response.data)

        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            self.assertEqual(user.monthly_budget, Decimal("25000.00"))

        invalid_response = self.client.post(
            "/budget/",
            data={"monthly_budget": "-1"},
        )
        self.assertEqual(invalid_response.status_code, 422)

    def test_budget_progress_uses_current_month_expenses(self):
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.monthly_budget = Decimal("1000.00")
            db.session.add_all(
                [
                    Expense(
                        amount=Decimal("250.00"),
                        category="Food",
                        description="Current month",
                        expense_date=date.today(),
                        user_id=self.user_id,
                    ),
                    Expense(
                        amount=Decimal("400.00"),
                        category="Bills",
                        description="Previous month",
                        expense_date=date(2026, 6, 1),
                        user_id=self.user_id,
                    ),
                ]
            )
            db.session.commit()

        self.login()
        response = self.client.get("/budget/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("₹1,000.00".encode(), response.data)
        self.assertIn("₹250.00".encode(), response.data)
        self.assertIn("₹750.00".encode(), response.data)
        self.assertIn(b"25% used", response.data)

    def test_dashboard_displays_saved_budget_progress(self):
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.monthly_budget = Decimal("2000.00")
            db.session.add(
                Expense(
                    amount=Decimal("500.00"),
                    category="Bills",
                    description="Internet",
                    expense_date=date.today(),
                    user_id=self.user_id,
                )
            )
            db.session.commit()

        self.login()
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("₹500.00".encode(), response.data)
        self.assertIn("of ₹2,000.00 monthly budget".encode(), response.data)
        self.assertIn(b"25% used", response.data)

    def test_over_budget_state_is_visible(self):
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.monthly_budget = Decimal("100.00")
            db.session.add(
                Expense(
                    amount=Decimal("150.00"),
                    category="Shopping",
                    description="Over budget",
                    expense_date=date.today(),
                    user_id=self.user_id,
                )
            )
            db.session.commit()

        self.login()
        response = self.client.get("/budget/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("-₹50.00".encode(), response.data)
        self.assertIn(b"150% used", response.data)
        self.assertIn(b"You are over your monthly budget.", response.data)


if __name__ == "__main__":
    unittest.main()
