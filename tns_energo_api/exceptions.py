class TNSEnergoException(Exception):
    pass


class ResponseException(TNSEnergoException):
    """Generic response exception"""


class ResponseResultException(ResponseException):
    """Response contains a false-valued result status"""


class RequestException(TNSEnergoException):
    """Generic request exception"""


class RequestTimeoutException(RequestException):
    """Request timed out"""


class EmptyResultException(ResponseResultException):
    """Response contains empty result"""
