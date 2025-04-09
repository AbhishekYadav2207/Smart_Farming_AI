from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    user_type = HiddenField('User Type', validators=[DataRequired()])
    id = StringField('User ID', validators=[DataRequired()])
    password = PasswordField('Password')