import re
import requests


class Provider(object):

    __url = "https://api.chess.com/pub/puzzle/random"

    def __init__(self) -> None:
        response: dict = requests.get(url=self.__url).json()
        for k, v in response.items():
            setattr(self, k, v)

    def get_solution(self):
        match = re.search('(1\.)(.*)', self.pgn)
        res = match.group(0).replace('\r\n*', '')
        return res

    def white_to_move(self):
        _move = self.get_solution().split(' ')[0]
        if '...' in _move:
            return False
        else:
            return True

class Player(object):

    username = None
    active = False
    score = 0
    locked = False

    def __init__(self, username) -> None:
        self.username = username
        self.active = True
        import random
        self.score = random.randint(1, 30)

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def _ca(self):
        self.score += 2

    def _u(self):
        self.score = self.score

    def _wa(self):
        self.score -= 1

    def is_active(self):
        return self.active

    def is_locked(self):
        return self.locked
