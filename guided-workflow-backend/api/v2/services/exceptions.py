class ServiceException(Exception):
    """Follows a standard pattern that translates well to a HTTPException without being one"""

    def __init__(self, msg: str, code: int):
        self.msg = msg
        self.code = code
