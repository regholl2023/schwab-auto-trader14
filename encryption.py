# Cryptography imports beep beep boop yu2hakme. 
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# Basic imports 
import base64
import os
import yaml

# From Imports 
from getpass import getpass
from pathlib import Path

def derive_key_from_password(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key 

def encrypt_file_with_password(file_path):
    password = os.getenv("super_secret_sauce")
    salt = os.urandom(16)  # Generate a new salt
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    
    with open(file_path, 'rb') as file:
        original_data = file.read()
    
    encrypted_data = fernet.encrypt(original_data)
    
    # Write the salt and encrypted data to a new file
    with open(file_path, 'wb') as encrypted_file:
        encrypted_file.write(salt + encrypted_data)

def decrypt_file_with_password(file_path):
    password = os.getenv("super_secret_sauce")
    try:
        with open(file_path, 'rb') as encrypted_file:
            # First 16 bytes are the salt
            salt = encrypted_file.read(16)
            encrypted_data = encrypted_file.read()
        
        key = derive_key_from_password(password, salt)
        fernet = Fernet(key)
        
        decrypted_data = fernet.decrypt(encrypted_data)
        return yaml.safe_load(decrypted_data.decode())
    except InvalidToken:
        print("Uh oh, looks like your encryption password was wrong. \n" 
              "If you forget this it's okay to just blowaway the credentials, use --startup. and redo the schwab login.")
        exit()

def is_file_encrypted(file_path):
    if not os.path.isfile(file_path):
        return False
    with open(file_path, 'rb') as file:
        file_header = file.read(16)  # Read the first 16 bytes (the salt size)
    return len(file_header) == 16  # If there are 16 bytes, it's likely encrypted

# Call to set encryption of both schwab and token.
def set_encryption(file_path):
    password = getpass("Enter encryption password to secure schwab-credentials and schwab-tokens.")
    # We will have finite schwab.yaml files so its okay to just pass these two in. 
    app_path = os.path.join(file_path, "schwab-credentials.yaml")
    token_path = os.path.join(file_path, "tokens.yaml")
    encrypt_file_with_password(app_path, password)
    encrypt_file_with_password(token_path, password)

def retrieve_encrypted_data(password, file_path):
    password = password
    #token_path = os.path.join(file_path, "tokens.yaml")
    decrypted_data = decrypt_file_with_password(token_path, password)
    # Just a print to test if data is corrently decrypted.
    #print(decrypted_data)