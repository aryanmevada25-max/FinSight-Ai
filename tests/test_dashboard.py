import unittest
from datetime import date
from decimal import Decimal

from app import create_app
from models import db
from models.expense import Expense
from models.income import Income
from models.user import User
from tests.test_auth import TestConfig


class DashboardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            user = User(name="Dashboard User", email="dashboard@example.com")
            user.set_password("secure-pass-123")
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_dashboard_renders_empty_financial_state(self):
        self.client.post(
            "/login",
            data={
                "email": "dashboard@example.com",
                "password": "secure-pass-123",
            },
        )

        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back, Dashboard User", response.data)
        self.assertGreaterEqual(response.data.count("₹0.00".encode()), 5)
        self.assertIn(b"No transactions found.", response.data)
        self.assertIn(b"incomeExpenseChart", response.data)
        self.assertIn(b"expenseCategoriesChart", response.data)
        self.assertIn(b"monthlySpendingChart", response.data)
        self.assertIn(b"weeklySpendingChart", response.data)
        self.assertIn(
            b"Get personalized budget guidance", response.data
        )

    def test_dashboard_includes_expense_totals_and_recent_activity(self):
        with self.app.app_context():
            db.session.add(
                Expense(
                    amount=Decimal("450.25"),
                    category="Food",
                    description="Groceries",
                    expense_date=date.today(),
                    user_id=self.user_id,
                )
            )
            db.session.commit()

        self.client.post(
            "/login",
            data={
                "email": "dashboard@example.com",
                "password": "secure-pass-123",
            },
        )
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data.count("₹450.25".encode()), 2)
        self.assertIn("-₹450.25".encode(), response.data)
        self.assertIn(b"Expense", response.data)
        self.assertIn(b"Food", response.data)

    def test_dashboard_calculates_income_balance_and_savings(self):
        with self.app.app_context():
            db.session.add_all(
                [
                    Income(
                        amount=Decimal("1000.00"),
                        source="Salary",
                        description="Pay",
                        income_date=date.today(),
                        user_id=self.user_id,
                    ),
                    Expense(
                        amount=Decimal("250.25"),
                        category="Bills",
                        description="Internet",
                        expense_date=date.today(),
                        user_id=self.user_id,
                    ),
                ]
            )
            db.session.commit()

        self.client.post(
            "/login",
            data={
                "email": "dashboard@example.com",
                "password": "secure-pass-123",
            },
        )
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("₹1,000.00".encode(), response.data)
        self.assertGreaterEqual(response.data.count("₹749.75".encode()), 2)
        self.assertIn("+₹1,000.00".encode(), response.data)
        self.assertIn(b"Salary", response.data)
        self.assertIn(b"Bills", response.data)


if __name__ == "__main__":
    unittest.main()
