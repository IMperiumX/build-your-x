from enum import IntEnum


class HTTPStatus(IntEnum):
    """HTTP status codes and reason phrases"""

    def __new__(cls, value, phrase, description=""):
        obj = int.__new__(cls, value)
        obj._value_ = value

        obj.phrase = phrase
        obj.description = description
        return obj

    # success
    OK = 200, "OK", "Request fulfilled, document follows"

    # client error
    REQUEST_URI_TOO_LONG = (414, "Request-URI Too Long", "URI is too long")

    # server errors
    INTERNAL_SERVER_ERROR = (
        500,
        "Internal Server Error",
        "Server got itself in trouble",
    )
    NOT_IMPLEMENTED = (501, "Not Implemented", "Server does not support this operation")
