from flask import Blueprint, current_app, redirect, render_template, url_for
from flask_login import current_user


main = Blueprint("main", __name__)


@main.route("/")
def home():
    if current_app.config.get("TESTING"):
        return render_template("index.html")
    path = "dashboard" if current_user.is_authenticated else "login"
    return redirect(url_for("ui.app", path=path))


def register_error_handlers(app) -> None:
    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("404.html"), 404
