from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from models.income import INCOME_SOURCES


class IncomeForm(FlaskForm):
    amount = DecimalField(
        "Amount",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, max=9999999999.99),
        ],
    )
    source = SelectField(
        "Source",
        choices=[(source, source) for source in INCOME_SOURCES],
        validators=[DataRequired()],
    )
    description = StringField(
        "Description", validators=[Optional(), Length(max=255)]
    )
    income_date = DateField(
        "Date", default=date.today, validators=[DataRequired()]
    )
    submit = SubmitField("Save income")
