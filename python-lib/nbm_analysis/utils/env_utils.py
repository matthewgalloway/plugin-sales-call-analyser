import os


def is_dku_runtime():
    flask_environment = os.getenv("FLASK_ENVIRONMENT")
    return True if ("PROD" in flask_environment.upper()) else False


def dku_runtime_only(func):

    def wrapper(*args, **kwargs):
        result = None
        if is_dku_runtime():
            result = func(*args, **kwargs)
        return result

    return wrapper
