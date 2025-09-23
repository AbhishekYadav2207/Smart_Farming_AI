from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange
from wtforms.validators import ValidationError
from app.models import Location

class RegisterGovtUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    id = StringField('User ID', validators=[DataRequired(), Length(min=3)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10)])
    email = StringField('Email', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=6)])
    
    def validate_pincode(self, field):
        if not field.data.isdigit() or len(field.data) != 6:
            raise ValidationError('Pincode must be a 6-digit number')

class RegisterLocationForm(FlaskForm):
    pincode = IntegerField('Pincode', validators=[DataRequired(), NumberRange(min=100000, max=999999)])
    name = StringField('Location Name', validators=[DataRequired()])
    district = StringField('District', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    latitude = StringField('Latitude', validators=[Optional()])
    longitude = StringField('Longitude', validators=[Optional()])

    def validate_id(self, field):
        if Location.query.filter_by(id=field.data).first():
            raise ValidationError('Location ID already exists')