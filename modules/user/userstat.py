from modules.user.user_sqlite import user

class UserStat(object):
    __name__ = "UserStat"
    # __slots__ = ('id', 'stat')

    def __init__(self, userid: int, stat: str) -> None:
        self.id: int = userid
        self.stat: str = stat

    def __add__(self, o: int) -> int:
        return user.read_from_stat(self) + o

    def __sub__(self, o: int) -> int:
        return user.read_from_stat(self) - o

    def __mul__(self, o: int) -> int:
        return user.read_from_stat(self) * o

    def __iadd__(self, o: int) -> None:
        user.add_from_stat(self, o)

    def __isub__(self, o: int) -> None:
        user.subtract_from_stat(self, o)

    def __lt__(self, o: int) -> bool:
        return user.read_from_stat(self) < o

    def __gt__(self, o: int) -> bool:
        return user.read_from_stat(self) > o

    def __ge__(self, o: int) -> bool:
        return user.read_from_stat(self) >= o

    def __le__(self, o: int) -> bool:
        return user.read_from_stat(self) <= o

    def __bool__(self) -> bool:
        return bool(user.read_from_stat(self))

    def __int__(self) -> int:
        return int(user.read_from_stat(self))

    def __str__(self) -> str:
        return str(user.read_from_stat(self))
