from django.core.cache import cache
import random

OTP_EXPIRE_MINUTES = 10  # OTP valid for 10 minutes

def generate_otp(email: str) -> str:
    """Generate and store OTP in cache"""
    otp = str(random.randint(1001, 9999))
    cache.set(f"otp_{email}", otp, timeout=OTP_EXPIRE_MINUTES * 60)
    return otp

def verify_otp(email: str, otp_input: str) -> bool:
    """Check OTP validity"""
    otp = cache.get(f"otp_{email}")
    if otp and otp == otp_input:
        cache.delete(f"otp_{email}")  # invalidate after successful verification
        return True
    return False
