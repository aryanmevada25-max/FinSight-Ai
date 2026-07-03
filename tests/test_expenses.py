import unittest
from datetime import date
from decimal import Decimal

from app import create_app
from models import db
from models.expense import Expense
from models.user import User
from tests.test_auth import TestConfig


class ExpenseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(name="Expense User", email="expense@example.com")
            self.user.set_password("secure-pass-123")
            self.other_user = User(name="Other User", email="other@example.com")
            self.other_user.set_password("secure-pass-123")
            db.session.add_all([self.user, self.other_user])
            db.session.commit()
            self.user_id = self.user.id
            self.other_user_id = self.other_user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def login(self):
        return self.client.post(
            "/login",
            data={
                "email": "expense@example.com",
                "password": "secure-pass-123",
            },
        )

    def add_expense(self, **overrides):
        data = {
            "amount": "125.50",
            "category": "Food",
            "description": "Team lunch",
            "expense_date": "2026-07-01",
        }
        data.update(overrides)
        return self.client.post(
            "/expenses/new", data=data, follow_redirects=True
        )

    def test_expense_pages_require_authentication(self):
        self.assertEqual(self.client.get("/expenses/").status_code, 302)
        self.assertEqual(self.client.get("/expenses/new").status_code, 302)

    def test_create_and_validate_expense(self):
        self.login()
        response = self.add_expense()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Expense added successfully.", response.data)
        self.assertIn(b"Team lunch", response.data)

        with self.app.app_context():
            record = db.session.scalar(db.select(Expense))
            self.assertEqual(record.amount, Decimal("125.50"))
            self.assertEqual(record.user_id, self.user_id)

        invalid_response = self.add_expense(amount="0")
        self.assertEqual(invalid_response.status_code, 422)
        with self.app.app_context():
            self.assertEqual(
                db.session.scalar(db.select(db.func.count(Expense.id))), 1
            )

    def test_search_and_category_filters(self):
        self.login()
        self.add_expense()
        self.add_expense(
            amount="2400.00",
            category="Bills",
            description="Electricity bill",
            expense_date="2026-06-15",
        )

        search_response = self.client.get("/expenses/?q=lunch")
        self.assertIn(b"Team lunch", search_response.data)
        self.assertNotIn(b"Electricity bill", search_response.data)

        filter_response = self.client.get("/expenses/?category=Bills")
        self.assertIn(b"Electricity bill", filter_response.data)
        self.assertNotIn(b"Team lunch", filter_response.data)

    def test_edit_delete_and_user_ownership(self):
        with self.app.app_context():
            own_expense = Expense(
                amount=Decimal("50.00"),
                category="Transport",
                description="Taxi",
                expense_date=date(2026, 7, 1),
                user_id=self.user_id,
            )
            other_expense = Expense(
                amount=Decimal("80.00"),
                category="Shopping",
                description="Private purchase",
                expense_date=date(2026, 7, 1),
                user_id=self.other_user_id,
            )
            db.session.add_all([own_expense, other_expense])
            db.session.commit()
            own_expense_id = own_expense.id
            other_expense_id = other_expense.id

        self.login()
        edit_response = self.client.post(
            f"/expenses/{own_expense_id}/edit",
            data={
                "amount": "75.25",
                "category": "Transport",
                "description": "Airport taxi",
                "expense_date": "2026-07-02",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Expense updated successfully.", edit_response.data)
        self.assertIn(b"Airport taxi", edit_response.data)

        self.assertEqual(
            self.client.get(f"/expenses/{other_expense_id}/edit").status_code,
            404,
        )
        self.assertEqual(
            self.client.post(f"/expenses/{other_expense_id}/delete").status_code,
            404,
        )

        delete_response = self.client.post(
            f"/expenses/{own_expense_id}/delete", follow_redirects=True
        )
        self.assertIn(b"Expense deleted successfully.", delete_response.data)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Expense, own_expense_id))
            self.assertIsNotNone(db.session.get(Expense, other_expense_id))


if __name__ == "__main__":
    unittest.main()
