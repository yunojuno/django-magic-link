class InvalidToken(Exception):
    pass


class InactiveToken(InvalidToken):
    pass


class ExpiredToken(InvalidToken):
    pass


class UsedToken(InvalidToken):
    pass
