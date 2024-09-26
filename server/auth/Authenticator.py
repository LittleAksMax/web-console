from hashlib import sha512


class Authenticator:
    def __init__(self, secret_key: str):
        self.secret_key_hash = sha512(secret_key.encode('utf-8'))
    
    def validate(self, authentication_message_hash: str) -> bool:
        expected_hex_digest = self.secret_key_hash.hexdigest()
        return expected_hex_digest == authentication_message_hash
