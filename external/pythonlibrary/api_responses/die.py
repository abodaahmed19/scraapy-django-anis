from rest_framework.response import Response as RESTResponse
from rest_framework import serializers


class Response(RESTResponse):
    def __init__(self, message:str, data=None, errors=None, warnings=None, status=None, serializer=False):
        if data and errors:
            raise ValueError('Data and errors cannot be included in the same response')
        if errors:
            errors = error_formatter(errors, serializer)
        response = {
            'message': message,
            'data': data if data else {},
            'errors': errors if errors else [],
            'warnings': warnings if warnings else [],
        }

        super().__init__(response, status=status)

def error_formatter(errors, serializer=False):
    if isinstance(errors, dict) and not serializer:
        errors = [errors]
    if serializer:
        error_list = []
        for field, message in errors.items():
            if isinstance(message, dict):
                for key, value in message.items():
                    error_list.append({
                        'type': field,
                        'message': value[0],
                    })
            else:
                if field == 'non_field_errors':
                    field = 'Validation'
                error_list.append({
                    'type': field,
                    'message': message[0],
                })
        errors = error_list
    if not isinstance(errors, list):
        raise ValueError('Errors must be a list or dictionary')
    for error in errors:
        if 'type' not in error:
            error['type'] = 'unknown'
        if 'message' not in error:
            error['message'] = 'An unknown error occurred'
    return errors
