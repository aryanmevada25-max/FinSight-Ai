import unittest
from datetime import date
from decimal import Decimal

from app import create_app
from models import db
from models.income import Income
from models.user import User
from tests.test_auth import TestConfig


class IncomeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(name="Income User", email="income@example.com")
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
                "email": "income@example.com",
                "password": "secure-pass-123",
            },
        )

    def add_income(self, **overrides):
        data = {
            "amount": "50000.00",
            "source": "Salary",
            "description": "Monthly salary",
            "income_date": "2026-07-01",
        }
        data.update(overrides)
        return self.client.post(
            "/income/new", data=data, follow_redirects=True
        )

    def test_income_pages_require_authentication(self):
        self.assertEqual(self.client.get("/income/").status_code, 302)
        self.assertEqual(self.client.get("/income/new").status_code, 302)

    def test_create_and_validate_income(self):
        self.login()
        response = self.add_income()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Income added successfully.", response.data)
        self.assertIn(b"Monthly salary", response.data)

        with self.app.app_context():
            record = db.session.scalar(db.select(Income))
            self.assertEqual(record.amount, Decimal("50000.00"))
            self.assertEqual(record.user_id, self.user_id)

        invalid_response = self.add_income(amount="0")
        self.assertEqual(invalid_response.status_code, 422)
        with self.app.app_context():
            self.assertEqual(
                db.session.scalar(db.select(db.func.count(Income.id))), 1
            )

    def test_history_is_newest_first(self):
        self.login()
        self.add_income(description="Older income", income_date="2026-06-01")
        self.add_income(description="Newer income", income_date="2026-07-01")

        response = self.client.get("/income/")

        self.assertLess(
            response.data.index(b"Newer income"),
            response.data.index(b"Older income"),
        )

    def test_edit_delete_and_user_ownership(self):
        with self.app.app_context():
            own_income = Income(
                amount=Decimal("1000.00"),
                source="Freelance",
                description="Design project",
                income_date=date(2026, 7, 1),
                user_id=self.user_id,
            )
            other_income = Income(
                amount=Decimal("800.00"),
                source="Gift",
                description="Private income",
                income_date=date(2026, 7, 1),
                user_id=self.other_user_id,
            )
            db.session.add_all([own_income, other_income])
            db.session.commit()
            own_income_id = own_income.id
            other_income_id = other_income.id

        self.login()
        edit_response = self.client.post(
            f"/income/{own_income_id}/edit",
            data={
                "amount": "1250.50",
                "source": "Business",
                "description": "Updated project",
                "income_date": "2026-07-02",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Income updated successfully.", edit_response.data)
        self.assertIn(b"Updated project", edit_response.data)

        self.assertEqual(
            self.client.get(f"/income/{other_income_id}/edit").status_code,
            404,
        )
        self.assertEqual(
            self.client.post(f"/income/{other_income_id}/delete").status_code,
            404,
        )

        delete_response = self.client.post(
            f"/income/{own_income_id}/delete", follow_redirects=True
        )
        self.assertIn(b"Income deleted successfully.", delete_response.data)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Income, own_income_id))
            self.assertIsNotNone(db.session.get(Income, other_income_id))


if __name__ == "__main__":
    unittest.main()
