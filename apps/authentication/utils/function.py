import secrets
import string

def generate_random_token(length=20):
    """Generate a secure random token of given length"""
    characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    return ''.join(secrets.choice(characters) for _ in range(length))
