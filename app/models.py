from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Farmer(db.Model):
    name = db.Column(db.String(100))
    id = db.Column(db.String(50), primary_key=True)
    soil_type = db.Column(db.String(100))
    pH_level = db.Column(db.String(100))
    annual_rainfall = db.Column(db.String(100))
    average_temperature = db.Column(db.String(100))
    location = db.Column(db.String(100))
    nitrogen = db.Column(db.String(100))
    phosphorus = db.Column(db.String(100))
    potassium = db.Column(db.String(100))
    crop_selected = db.Column(db.String(100))
    area_of_land = db.Column(db.String(100))
    previous_crop = db.Column(db.String(100))
    previous_yield = db.Column(db.String(100))
    previous_fertilizer_used = db.Column(db.String(100))
    fertilizer_needed = db.Column(db.String(100))
    water_needed = db.Column(db.String(100))
    disease_detection = db.Column(db.String(100))

class GovtUser(db.Model):
    name = db.Column(db.String(100))
    id = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(100))
    annual_rainfall = db.Column(db.String(100))
    average_temperature = db.Column(db.String(100))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        if not password:
            raise ValueError('Password cannot be empty')
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)