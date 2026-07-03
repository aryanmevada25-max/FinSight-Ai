from flask import Flask

from config import Config
from models import bcrypt, csrf, db, login_manager, migrate
from routes.ai import ai
from routes.api import api
from routes.auth import auth
from routes.budget import budget
from routes.dashboard import dashboard
from routes.expense import expense
from routes.income import income
from routes.main import main, register_error_handlers
from routes.profile import profile
from routes.reports import reports
from routes.ui import ui


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set in the environment.")

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(expense)
    app.register_blueprint(income)
    app.register_blueprint(budget)
    app.register_blueprint(reports)
    app.register_blueprint(ai)
    app.register_blueprint(api)
    app.register_blueprint(profile)
    app.register_blueprint(ui)
    register_error_handlers(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
