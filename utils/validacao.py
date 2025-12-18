import re

EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

def email_valido(email: str) -> bool:
    if not email:
        return False
    email = email.strip()
    return bool(EMAIL_REGEX.match(email))
