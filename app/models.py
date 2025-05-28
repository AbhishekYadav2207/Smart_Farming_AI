# app/models.py
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import event

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), default='India')
    annual_rainfall = db.Column(db.Float)
    average_temperature = db.Column(db.Float)
    soil_types = db.Column(db.String(255))
    
    farmers = db.relationship('Farmer', back_populates='location', cascade='all, delete-orphan')
    govt_users = db.relationship('GovtUser', back_populates='location', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Location {self.name}, {self.state}>'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(20))
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def __repr__(self):
        return f'<User {self.id}: {self.name}>'

class Farmer(User):
    __tablename__ = 'farmers'
    
    id = db.Column(db.String(50), db.ForeignKey('users.id'), primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    land_area = db.Column(db.String(5))
    
    soil_type = db.Column(db.String(100))
    ph_level = db.Column(db.Float)  
    nitrogen = db.Column(db.Float)
    phosphorus = db.Column(db.Float) 
    potassium = db.Column(db.Float) 
    
    current_crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'))
    previous_crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'))
    previous_yield = db.Column(db.Float)
    
    location = db.relationship('Location', back_populates='farmers')
    current_crop = db.relationship('Crop', foreign_keys=[current_crop_id])
    previous_crop = db.relationship('Crop', foreign_keys=[previous_crop_id])
    recommendations = db.relationship('Recommendation', 
                                    back_populates='farmer', 
                                    cascade='all, delete-orphan')
    disease_reports = db.relationship('DiseaseReport', 
                                    backref='farmer', 
                                    lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    
    __mapper_args__ = {'polymorphic_identity': 'farmer'}

    @hybrid_property
    def profile_complete(self):
        return all([
            self.soil_type,
            self.ph_level is not None,
            self.nitrogen is not None,
            self.phosphorus is not None,
            self.potassium is not None
        ])

class GovtUser(User):
    __tablename__ = 'govt_users'
    
    id = db.Column(db.String(50), db.ForeignKey('users.id'), primary_key=True)
    no_farmers_assigned = db.Column(db.Integer, default=0)
    no_farmers_active = db.Column(db.Integer, default=0)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    password_hash = db.Column(db.String(128))
    
    location = db.relationship('Location', back_populates='govt_users')
    
    __mapper_args__ = {'polymorphic_identity': 'govt_user'}
    
    @property
    def password(self):
        raise AttributeError('password is not readable')
    
    @password.setter
    def password(self, password):
        if not password:
            raise ValueError('Password cannot be empty')
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class Crop(db.Model):
    __tablename__ = 'crops'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    being_grown = db.Column(db.Boolean, default=False)
    no_of_farmers = db.Column(db.Integer, default=0)
    scientific_name = db.Column(db.String(100))
    water_requirements = db.Column(db.Float)
    ideal_ph_min = db.Column(db.Float)
    ideal_ph_max = db.Column(db.Float)
    
    recommendations = db.relationship('Recommendation', back_populates='crop')
    farmers_current = db.relationship('Farmer', foreign_keys='Farmer.current_crop_id', backref='current_crop_ref')
    farmers_previous = db.relationship('Farmer', foreign_keys='Farmer.previous_crop_id', backref='previous_crop_ref')

    def __repr__(self):
        return f'<Crop {self.name}>'

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.String(50), db.ForeignKey('farmers.id'))
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    fertilizer_recommendation = db.Column(db.Text)
    water_requirement = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    farmer = db.relationship('Farmer', back_populates='recommendations')
    crop = db.relationship('Crop', back_populates='recommendations')

    def __repr__(self):
        return f'<Recommendation for {self.farmer_id} on {self.date}>'

class DiseaseReport(db.Model):
    __tablename__ = 'disease_reports'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farmer_id = db.Column(db.String(50), db.ForeignKey('farmers.id'))
    image_path = db.Column(db.String(255), nullable=False)
    detection_date = db.Column(db.DateTime, default=datetime.utcnow)
    disease_name = db.Column(db.String(100))
    confidence = db.Column(db.String(50))  # High/Medium/Low
    symptoms = db.Column(db.Text)
    treatment = db.Column(db.Text)
    prevention = db.Column(db.Text)

    def __repr__(self):
        return f'<DiseaseReport {self.disease_name} for {self.farmer_id}>'

@event.listens_for(Farmer.current_crop, 'set')
def update_previous_crop(target, value, oldvalue, initiator):
    if oldvalue and oldvalue != value:
        target.previous_crop = oldvalue