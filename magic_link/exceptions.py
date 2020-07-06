class InvalidTokenUse(Exception):
    pass


class InactiveToken(InvalidTokenUse):
    pass


class ExpiredToken(InvalidTokenUse):
    pass


class UsedToken(InvalidTokenUse):
    pass


class UserMismatch(InvalidTokenUse):
    pass
