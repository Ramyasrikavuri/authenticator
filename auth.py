from database import load_users, save_users
from utils import hash_password, check_password

def register_user(username, email, password):
    users = load_users()

    for user in users:
        if user["email"] == email:
            return False

    hashed = hash_password(password).decode()

    users.append({
        "username": username,
        "email": email,
        "password": hashed
    })

    save_users(users)
    return True


def login_user(email, password):
    users = load_users()

    for user in users:
        if user["email"] == email:
            return check_password(password, user["password"].encode())

    return False