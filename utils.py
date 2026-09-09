import secrets


def generate_pin() -> str:
    """Generate a cryptographically secure random 6-digit PIN."""
    return f"{secrets.randbelow(1_000_000):06d}"