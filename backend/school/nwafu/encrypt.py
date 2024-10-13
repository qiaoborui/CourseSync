import base64
import random
import string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

def get_aes_string(data, key0, iv0):
    key0 = key0.strip()
    key = key0.encode('utf-8')
    iv = iv0.encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')

def encrypt_aes(data, aes_key):
    if not aes_key:
        return data
    random_prefix = random_string(64)
    encrypted = get_aes_string(random_prefix + data, aes_key, random_string(16))
    return encrypted

def encrypt_password(pwd0, key):
    try:
        return encrypt_aes(pwd0, key)
    except Exception:
        return pwd0

def random_string(length):
    chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
    return ''.join(random.choice(chars) for _ in range(length))

# Example usage
if __name__ == "__main__":
    password = ""
    key = "tWicfzMbfz5euwH9"
    encrypted_password = encrypt_password(password, key)
    print(f"Original password: {password}")
    print(f"Encrypted password: {encrypted_password}")