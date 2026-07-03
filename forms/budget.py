from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class BudgetForm(FlaskForm):
    monthly_budget = DecimalField(
        "Monthly Budget",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0, max=9999999999.99),
        ],
    )
    submit = SubmitField("Save budget")
