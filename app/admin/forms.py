from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange
from wtforms.validators import ValidationError
from app.models import Location

class RegisterGovtUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    id = StringField('User ID', validators=[DataRequired(), Length(min=3)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10)])
    email = StringField('Email', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    location_id = IntegerField('Location ID', validators=[DataRequired()])

    def validate_location_id(self, field):
        if not Location.query.get(field.data):
            raise ValidationError('Location ID does not exist')

class RegisterLocationForm(FlaskForm):
    id = IntegerField('Location ID', validators=[DataRequired(), NumberRange(min=1)])
    name = StringField('Location Name', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])

    def validate_id(self, field):
        if Location.query.filter_by(id=field.data).first():
            raise ValidationError('Location ID already exists')