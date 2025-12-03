
from django.utils.crypto import get_random_string

def generate_order_number():
    return f"ORD-{get_random_string(10).upper()}"
