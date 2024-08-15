# https://github.com/Luffich/st-comunity-music/blob/main/music_rus.py

from modules.exceptions import BruhCasinoError

class VoiceError(BruhCasinoError):
    def __init__(self, msg:str, codestyle:bool=True) -> None:
        super().__init__(msg, codestyle)

class YTDLError(BruhCasinoError):
    def __init__(self, msg:str, codestyle:bool=True) -> None:
        super().__init__(msg, codestyle)

class SongTooLong(BruhCasinoError):
    def __init__(self, msg:str='that song is too long for me', codestyle:bool=False) -> None:
        super().__init__(msg, codestyle)
