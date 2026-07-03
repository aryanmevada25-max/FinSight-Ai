from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from models.expense import EXPENSE_CATEGORIES


class ExpenseForm(FlaskForm):
    amount = DecimalField(
        "Amount",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, max=9999999999.99),
        ],
    )
    category = SelectField(
        "Category",
        choices=[(category, category) for category in EXPENSE_CATEGORIES],
        validators=[DataRequired()],
    )
    description = StringField(
        "Description", validators=[Optional(), Length(max=255)]
    )
    expense_date = DateField(
        "Date", default=date.today, validators=[DataRequired()]
    )
    submit = SubmitField("Save expense")
