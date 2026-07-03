import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def valid_email(_form, field) -> None:
    """Validate a practical email address without a network lookup."""
    if not EMAIL_PATTERN.fullmatch(field.data.strip()):
        raise ValidationError("Enter a valid email address.")


class RegistrationForm(FlaskForm):
    name = StringField(
        "Full name", validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField(
        "Email address",
        validators=[DataRequired(), Length(max=120), valid_email],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=72)]
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField(
        "Email address",
        validators=[DataRequired(), Length(max=120), valid_email],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(max=72)]
    )
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")
