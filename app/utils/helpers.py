from flask import flash
from app.models import GovtUser, Farmer, Location, Crop
from datetime import datetime
from app import db
from sqlalchemy import func


def flash_errors(form):
    """Flash all form errors"""
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
    # Get all govt users linked to this location
    govt_users = GovtUser.query.all()
    updated = False
    for govt_user in govt_users:
        if location_id in govt_user.location_ids:
            # Total farmers in this location
            total_farmers = Farmer.query.filter_by(location_id=location_id).count()
            # Active farmers (with crops assigned)
            active_farmers = Farmer.query.filter(
                Farmer.location_id == location_id,
                Farmer.current_crop_id.isnot(None)
            ).count()
            govt_user.no_farmers_assigned = total_farmers
            govt_user.no_farmers_active = active_farmers
            updated = True
    if updated:
        db.session.commit()
    return updated


def update_govt_user_counts(govt_user):
    """
    Update farmer counts for a government user based on all their locations
    Update farmer counts for a single government user efficiently
    """
    location_ids = govt_user.location_ids or []

    if not location_ids:
        govt_user.no_farmers_assigned = 0
        govt_user.no_farmers_active = 0
        db.session.commit()
        return 0, 0

    # Single query to get total and active farmers for all locations
    counts = (
        db.session.query(
            func.count(Farmer.id).label('total'),
            func.count(Farmer.current_crop_id).label('active')
        )
        .filter(Farmer.location_id.in_(location_ids))
        .first()
    )

    total_farmers = counts.total or 0
    active_farmers = counts.active or 0

    govt_user.no_farmers_assigned = total_farmers
    govt_user.no_farmers_active = active_farmers
    db.session.commit()

    return total_farmers, active_farmers


def update_location_users_counts(location_id):
    """
    Update all user counts for a specific location

    Args:
        location_id: The ID of the location to update counts for

    Updates:
        - no_of_farmers: Total farmers in the location
        - no_of_govt_users: Total government users in the location
    
    Update farmer and govt user counts for a single location efficiently
    """
    # Count farmers in this location
    counts = (
        db.session.query(
            func.count(Farmer.id).label('farmer_count')
        )
        .filter(Farmer.location_id == location_id)
        .first()
    )
    farmer_count = counts.farmer_count or 0

    # Count govt users associated with this location
    govt_users_count = (
        db.session.query(func.count(GovtUser.id))
        .filter(GovtUser.location_ids.contains([location_id]))  # JSON/ARRAY field
        .scalar() or 0
    )

    # Update location
    location = Location.query.get(location_id)
    if location:
        location.no_of_farmers = farmer_count
        location.no_of_govt_users = govt_users_count
        db.session.commit()
        return True

    return False


# Helper functions for locations
def get_locations_by_pincode(pincode):
    """Get all locations for a given pincode"""
    return Location.query.filter_by(pincode=pincode).all()


def get_location_ids_by_pincode(pincode):
    """Get all location IDs for a given pincode"""
    locations = get_locations_by_pincode(pincode)
    return [loc.id for loc in locations]


# Alias for backward compatibility
update_farmer_counts_by_user = update_govt_user_counts
