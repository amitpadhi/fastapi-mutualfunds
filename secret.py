import secrets

SECRET_KEY = secrets.token_hex(32)  # 64-character hex string
print(SECRET_KEY)
