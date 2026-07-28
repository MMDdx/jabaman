# utils/security.py
"""توابع امنیتی مشترک: هش رمز عبور با PBKDF2 + salt.

این ماژول جایگزین SHA-256 خام است و در برابر rainbow table و brute-force مقاوم‌تر است.
بدون نیاز به کتابخانه خارجی (فقط hashlib و secrets از استاندارد کتابخانه‌ی پایتون).
"""
import hashlib
import os
import secrets

# پارامترهای PBKDF2
PBKDF2_ITERATIONS = 200_000
HASH_ALGORITHM = "sha256"
SALT_BYTES = 16
HASH_BYTES = 32

# فرمت ذخیره‌سازی: pbkdf2$iterations$salt_hex$hash_hex
DELIMITER = "$"


def hash_password(password: str) -> str:
    """رمز عبور را با PBKDF2 و salt تصادفی هش می‌کند.

    خروجی به شکل: pbkdf2$200000$<salt_hex>$<hash_hex>
    """
    if not password:
        raise ValueError("رمز عبور نمی‌تواند خالی باشد.")
    salt = secrets.token_bytes(SALT_BYTES)
    hash_bytes = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=HASH_BYTES,
    )
    return f"pbkdf2{DELIMITER}{PBKDF2_ITERATIONS}{DELIMITER}{salt.hex()}{DELIMITER}{hash_bytes.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:

    if not password or not stored_hash:
        return False

    try:
        parts = stored_hash.split(DELIMITER)
        if len(parts) != 4 or parts[0] != "pbkdf2":
            # پشتیبانی از هش‌های قدیمی SHA-256 (برای backward compat)
            if len(stored_hash) == 64:
                legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
                return secrets.compare_digest(legacy, stored_hash)
            return False

        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])

        actual_hash = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected_hash),
        )
        return secrets.compare_digest(actual_hash, expected_hash)
    except (ValueError, TypeError):
        return False
