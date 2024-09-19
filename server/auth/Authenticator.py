import os
from hashlib import sha512


class Authenticator:
    def __init__(self, secret_key: str):
        self.secret_key_hash = sha512(secret_key.encode('utf-8'))
    
    def validate(self, authentication_message_hash: bytes) -> bool:
        return self.secret_key_hash.digest() == authentication_message_hash
