from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# AES Decryption for Midway/Nodes
import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def decrypt_aes_256_cbc(encrypted_base64: str) -> dict:
    """
    Decrypts AES-256-CBC encrypted string sent from ESP32.
    Expects decrypted payload to be JSON.
    """
    try:
        # Convert hex key/iv to bytes
        key = bytes.fromhex(settings.AES_KEY)
        iv = bytes.fromhex(settings.AES_IV)
        
        # Decode base64 encrypted data
        encrypted_bytes = base64.b64decode(encrypted_base64)
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        
        return json.loads(decrypted_bytes.decode('utf-8'))
    except Exception as e:
        print(f"Decryption Error: {e}")
        return None

def decrypt_aes_256_cbc_raw(encrypted_base64: str) -> str:
    """
    Decrypts AES-256-CBC encrypted string sent from ESP32.
    Returns the raw string (e.g., "SOS" or "CP:...") instead of JSON data.
    """
    try:
        # Convert hex key/iv to bytes
        key = bytes.fromhex(settings.AES_KEY)
        iv = bytes.fromhex(settings.AES_IV)
        
        # Decode base64 encrypted data
        encrypted_bytes = base64.b64decode(encrypted_base64)
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Raw Decryption Error: {e}")
        return None
