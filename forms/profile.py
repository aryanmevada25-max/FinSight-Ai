from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

from forms.auth import valid_email


CURRENCY_CHOICES = (
    ("INR", "Indian Rupee (₹)"),
    ("USD", "US Dollar ($)"),
    ("EUR", "Euro (€)"),
    ("GBP", "British Pound (£)"),
)


class ProfileForm(FlaskForm):
    name = StringField(
        "Full name", validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField(
        "Email address",
        validators=[DataRequired(), Length(max=120), valid_email],
    )
    currency = SelectField(
        "Preferred currency",
        choices=CURRENCY_CHOICES,
        validators=[DataRequired()],
    )
    monthly_budget = DecimalField(
        "Monthly budget",
        places=2,
        validators=[DataRequired(), NumberRange(min=0, max=9999999999.99)],
    )
    submit = SubmitField("Save profile")
