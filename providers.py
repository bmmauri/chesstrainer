import re
import requests


class Provider(object):

    __url = "https://api.chess.com/pub/puzzle/random"

    def __init__(self) -> None:
        response: dict = requests.get(url=self.__url).json()
        for k, v in response.items():
            setattr(self, k, v)

    def get_solution(self):
        match = re.search('(1\.)(.*)(#)', self.pgn)
        return match.group(0)

    def white_to_move(self):
        _move = self.get_solution().split(' ')[0]
        if '...' in _move:
            return False
        else:
            return True
