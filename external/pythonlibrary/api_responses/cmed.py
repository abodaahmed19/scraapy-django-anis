from rest_framework.response import Response as RESTResponse

# Custom Response include code, message, errors, data


class Response(RESTResponse):
    def __init__(self, code, message, errors=None, data=None, status=None):
        response = {
            'code': code,
            'message': message,
            'errors': errors,
            'data': data
        }
        if not errors:
            response['errors'] = {}
        if not data:
            response['data'] = {}
        super().__init__(response, status=status)