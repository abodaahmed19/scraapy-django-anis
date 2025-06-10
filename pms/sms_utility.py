import requests

# SMS Provider Configuration
SMS_API_URL = "http://www.jawalbsms.ws/api.php/sendsms"
BALANCE_API_URL = "http://www.jawalbsms.ws/api.php/chk_balance"
SMS_USER = "your_username"  # Replace with your SMS provider username
SMS_PASS = "your_password"  # Replace with your SMS provider password
SMS_SENDER = "your_sender_id"  # Replace with your approved sender ID




def send_sms(phone_number, message):
    """
    Send an SMS using the Max Media HTTP API.
    """
    params = {
        "user": SMS_USER,
        "pass": SMS_PASS,
        "to": phone_number,
        "message": message,
        "sender": SMS_SENDER,
    }

    try:
        response = requests.get(SMS_API_URL, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.text  # Returns the API response (e.g., MSG_ID, STATUS)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send SMS: {e}")
        return None


def check_balance():
    """
    Check the remaining balance/credits on the SMS provider account.
    """
    params = {
        "user": SMS_USER,
        "pass": SMS_PASS,
    }

    try:
        response = requests.get(BALANCE_API_URL, params=params)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to check balance: {e}")
        return None