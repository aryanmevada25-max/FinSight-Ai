import unittest

from app import create_app
from models import db
from models.user import User


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False


class AuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def register(self, email="person@example.com"):
        return self.client.post(
            "/register",
            data={
                "name": "Test Person",
                "email": email,
                "password": "secure-pass-123",
                "confirm_password": "secure-pass-123",
            },
            follow_redirects=True,
        )

    def login(self, password="secure-pass-123"):
        return self.client.post(
            "/login",
            data={"email": "person@example.com", "password": password},
            follow_redirects=True,
        )

    def test_registration_hashes_password(self):
        response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account created successfully", response.data)

        with self.app.app_context():
            user = db.session.scalar(db.select(User))
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password, "secure-pass-123")
            self.assertTrue(user.check_password("secure-pass-123"))

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.register()
        response = self.register("PERSON@example.com")
        self.assertIn(b"email already exists", response.data)

        with self.app.app_context():
            self.assertEqual(db.session.scalar(db.select(db.func.count(User.id))), 1)

    def test_login_logout_and_protected_route(self):
        protected_response = self.client.get("/dashboard")
        self.assertEqual(protected_response.status_code, 302)
        self.assertIn("/login", protected_response.location)

        self.register()
        wrong_password_response = self.login("incorrect-password")
        self.assertIn(b"Invalid email address or password", wrong_password_response.data)

        login_response = self.login()
        self.assertIn(b"Welcome back", login_response.data)
        self.assertIn(b"Your numbers at a glance", login_response.data)

        logout_response = self.client.post("/logout", follow_redirects=True)
        self.assertIn(b"You have been logged out", logout_response.data)
        self.assertEqual(self.client.get("/dashboard").status_code, 302)


if __name__ == "__main__":
    unittest.main()
