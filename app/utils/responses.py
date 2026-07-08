def success_response(data):
    return {
        "success": True,
        "data": data,
        "error": None,
    }


def error_response(code, message):
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }