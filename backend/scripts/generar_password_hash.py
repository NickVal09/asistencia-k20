import base64
import hashlib
import os
import sys
import getpass

# Genera un hash ADMIN_PASSWORD_HASH (pbkdf2_sha256) para poner en .env
password = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("Password: ")
iteraciones = 200_000
salt = os.urandom(16)
calculado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iteraciones)
print("ADMIN_PASSWORD_HASH=pbkdf2_sha256${}${}${}".format(
    iteraciones,
    base64.urlsafe_b64encode(salt).rstrip(b"=").decode(),
    base64.urlsafe_b64encode(calculado).rstrip(b"=").decode(),
))
