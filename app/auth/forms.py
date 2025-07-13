from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from app.models import Farmer

class LoginForm(FlaskForm):
    user_type = HiddenField('User Type', validators=[DataRequired()], default='farmer')
    id = StringField('User ID', validators=[DataRequired()])
    password = PasswordField('Password')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    user_id = StringField('User ID', validators=[
        DataRequired(),
        Length(min=3, max=50),
    ])
    pincode = StringField('Pincode', validators=[
        DataRequired(),
        Length(min=6, max=6, message="Must be exactly 6 digits")
    ])
    location_id = SelectField('Location', validators=[DataRequired()], choices=[])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=10, message="Must be 10 digits")
    ])
    email = StringField('Email', validators=[Optional(), Length(max=100)])
    land_area = FloatField('Land Area (hectares)', validators=[
        Optional(),
        NumberRange(min=0, message="Must be positive")
    ])
    submit = SubmitField('Register')

    def validate_user_id(self, field):
        if Farmer.query.filter_by(id=field.data).first():
            raise ValidationError('This user ID is already registered')
