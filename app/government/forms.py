from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, Length

class AreaSettingsForm(FlaskForm):
    annual_rainfall = StringField('Annual Rainfall (mm)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Rainfall must be positive')
    ])
    average_temperature = StringField('Average Temperature (°C)', validators=[
        DataRequired(),
        NumberRange(min=-50, max=60, message='Enter a valid temperature')
    ])
    submit = SubmitField('Save Settings')

class RegisterFarmerForm(FlaskForm):
    name = StringField('Farmer Name', validators=[DataRequired(), Length(max=100)])
    id = StringField('Farmer ID', validators=[DataRequired(), Length(min=3, max=50)])
    area_of_land = StringField('Land Area (hectares)', validators=[NumberRange(min=0)])
    submit = SubmitField('Register Farmer')