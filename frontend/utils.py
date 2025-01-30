import os
import requests

TOKEN_FILE = "token.txt"
API_BASE_URL = "http://127.0.0.1:8000"  # Update this if needed

def save_token(token):
    """Save the token to a file."""
    with open(TOKEN_FILE, "w") as file:
        file.write(token)

def load_token():
    """Load the token from the file."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return file.read().strip()
    return None


def get_user_role(token):
    url = "http://127.0.0.1:8000/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    try:
        user_data = response.json()
        print("User Data Response:", user_data)  # Debugging line

        if not isinstance(user_data, dict):  # Ensure it's a dictionary
            print("Unexpected response format:", user_data)
            return "guest"

        return user_data.get("role", "guest")  # Default to "guest"
    
    except Exception as e:
        print("Error fetching user role:", e)
        return "guest"  # Safe fallback
