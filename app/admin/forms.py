from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

class RegisterGovtUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    id = StringField('User ID', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3)])
    location = StringField('Location', validators=[DataRequired()])