import base64
import hashlib
import smtplib


def encrypt(clear, key="Nothing"):
    enc = []
    for i, c in enumerate(clear):
        key_c = key[i % len(key)]
        enc_c = chr((ord(c) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()


def encrypt_password(password):
    password_bytes = password.encode('utf-8')
    encoded_bytes = base64.b64encode(password_bytes)
    return encoded_bytes.decode('utf-8')


def hash2(password):
    sha512_hash = hashlib.sha3_512(password.encode()).hexdigest()
    return sha512_hash


def hash0(password):
    sha256 = hashlib.sha3_256(password.encode()).hexdigest()
    return sha256


def hash1(password):
    sha384 = hashlib.sha3_384(password.encode()).hexdigest()
    return sha384


def mail(email, content, sub):
    MY_EMAIL = ""
    MY_PASSWORD = ""
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_PASSWORD)
        message = f"Subject:{sub}\n\n{content}"
        message = message.encode('utf-8')
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=email,
            msg=message
        )


def decrypt(enc, key="Nothing"):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i, c in enumerate(enc):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(c) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def final_encrypt(a):
    salt = 'wqPDlMOPw5PChcOkwoHDn8OZw6I='
    final_out = hash2(hash1(hash0(encrypt(key="5b40117d08e+646606a733e=1f0c078c6b87",
                                          clear=encrypt_password(a) + salt))))
    return final_out
