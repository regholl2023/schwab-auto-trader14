from cryptography.fernet import Fernet
import Path
import yaml

# Generate a key and write it to a file (do this only once)
def write_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Function to load the key from the secret file
def load_key():
    return open("secret.key", "rb").read()

# Encrypt the YAML file
def encrypt_file(file_path, key):
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open("encrypted_yaml.yaml", 'wb') as encrypted_file:
        encrypted_file.write(encrypted)

# Uncomment to create the key file
# write_key()

key = load_key()
encrypt_file("your_yaml_file.yaml", key)

# Load the key
def load_key():
    return open("secret.key", "rb").read()

# Decrypt the YAML file
def decrypt_file(file_path, key):
    fernet = Fernet(key)
    with open(file_path, 'rb') as encrypted_file:
        encrypted = encrypted_file.read()

    decrypted = fernet.decrypt(encrypted)

    return yaml.safe_load(decrypted.decode())

# Load the key
key = load_key()

# Decrypt and parse the YAML file
decrypted_data = decrypt_file("encrypted_yaml.yaml", key)

# Assign variables from the YAML data
your_variable = decrypted_data['your_key']

print(decrypted_data)  # Display the decrypted YAML content
print(f"Assigned Variable: {your_variable}")


def setup():

    path_to_key = Path("Users/cal/Desktop/schwab-stinky.yaml")
    if path_to_key.is_file():
        print("fuuuhhhrrrrrrr")
    