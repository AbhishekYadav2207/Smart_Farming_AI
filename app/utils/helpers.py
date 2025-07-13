from flask import flash
from app.models import GovtUser, Farmer, Location, Crop
from datetime import datetime
from app import db

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')

def update_farmer_counts(location_id):
    """
    Update all farmer counts for a government user's location
    
    Args:
        location_id: The ID of the location to update counts for
        
    Updates:
        - no_farmers_assigned: Total farmers in the location
        - no_farmers_active: Farmers with active crops in the location
    """
    govt_user = GovtUser.query.filter_by(location_id=location_id).first()
    if govt_user:
        # Update total assigned farmers count
        govt_user.no_farmers_assigned = Farmer.query.filter_by(
            location_id=location_id
        ).count()
        
        # Update active farmers count (those with crops assigned)
        govt_user.no_farmers_active = Farmer.query.filter(
            Farmer.location_id == location_id,
            Farmer.current_crop_id.isnot(None)
        ).count()
        
        db.session.commit()
        return True
    return False

def update_govt_user_counts(govt_user):
    farmer_count = Farmer.query.filter_by(location_id=govt_user.location_id).count()
    active_farmer_count = Farmer.query.filter(
        Farmer.location_id == govt_user.location_id,
        Farmer.current_crop_id.isnot(None)
    ).count()
    
    govt_user.no_farmers_assigned = farmer_count
    govt_user.no_farmers_active = active_farmer_count
    db.session.commit()

def update_location_users_counts(location_id):
    """
    Update all user counts for a specific location

    Args:
        location_id: The ID of the location to update counts for

    Updates:
        - no_farmers_assigned: Total farmers in the location
        - no_govt_users: Total government users in the location
    """
    farmers = Farmer.query.filter_by(location_id=location_id).all()
    farmer_count = len(farmers)
    govt_users_count = GovtUser.query.filter_by(location_id=location_id).count()

    # Update the location's farmer counts
    location = Location.query.get(location_id)
    if location:
        location.no_of_farmers = farmer_count
        location.no_of_govt_users = govt_users_count
        db.session.commit()
        return True
    return False