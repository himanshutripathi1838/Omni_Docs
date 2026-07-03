def success_response(message: str, **payload):
    return {"success": True, "message": message, **payload}


def error_response(message: str, **payload):
    return {"success": False, "message": message, **payload}
