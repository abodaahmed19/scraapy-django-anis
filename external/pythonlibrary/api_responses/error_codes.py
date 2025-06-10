# Error codes for the API responses are defined in the error_codes.py file.

class ErrorCodes:
    SUCCESS = 0
    INVALID_REQUEST = 1
    INVALID_CREDENTIALS = 2
    INVALID_TOKEN = 3
    NOT_AUTHORIZED = 4
    OTP_ALREADY_SENT = 5
    OTP_EXPIRED = 6
    OTP_INVALID = 7
    OTP_NOT_VERIFIED = 8
    OTP_NOT_SENT = 9
    INVALID_EMAIL = 10
    INVALID_INPUT = 11
    USER_NOT_LOGGED_IN = 12

    def message(code):
        return ERROR_MESSAGES.get(code, 'Unknown error')


ERROR_MESSAGES = {
    ErrorCodes.SUCCESS: 'Success',
    ErrorCodes.INVALID_REQUEST: 'Invalid request',
    ErrorCodes.INVALID_CREDENTIALS: 'Invalid credentials',
    ErrorCodes.INVALID_TOKEN: 'Invalid token',
    ErrorCodes.NOT_AUTHORIZED: 'Not authorized',
    ErrorCodes.OTP_ALREADY_SENT: 'OTP already sent',
    ErrorCodes.OTP_EXPIRED: 'OTP expired',
    ErrorCodes.OTP_INVALID: 'Invalid OTP',
    ErrorCodes.OTP_NOT_VERIFIED: 'OTP not verified',
    ErrorCodes.OTP_NOT_SENT: 'OTP not sent',
    ErrorCodes.INVALID_EMAIL: 'Invalid email',
    ErrorCodes.INVALID_INPUT: 'Invalid input',
    ErrorCodes.USER_NOT_LOGGED_IN: 'User not logged in',
}
