# utils/validation.py
def validate_and_format_phone(phone):
    if not phone:
        return None, "Phone number is required"
    
    if phone.startswith('0') and len(phone) == 11:
        phone = phone[1:]
    
    if not phone.isdigit() and len(phone) != 13:
        return None, "Invalid phone number"
    elif phone.startswith('+91') and len(phone) != 13:
        return None, "Phone number must be in +91XXXXXXXXXX format"
    elif len(phone) == 10 and not phone.startswith('+91'):
        phone = '+91' + phone
    
    return phone, None