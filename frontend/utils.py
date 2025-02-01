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

import requests

def api_request(endpoint, method="GET", data=None, token=None):
    url = f"http://127.0.0.1:8000{endpoint}"  # Ensure this is the correct API base URL
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return None

        if response.status_code == 200:
            return response.json()  # Ensure correct JSON handling
        else:
            print(f"Error: {response.status_code}, Response: {response.text}")  # Print error details
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

import requests

def perform_booking_action(endpoint, data, token):
    """ Perform API requests for booking management """
    url = f"http://127.0.0.1:8000/bookings/{endpoint}"  # Adjust base URL if needed
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=data, headers=headers)  # Change method if necessary
        return response.json()
    except Exception as e:
        return {"error": str(e)}