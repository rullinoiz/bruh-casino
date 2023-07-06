import random
import time
import typing
from typing import Union
from enum import Enum, auto

random.seed(time.time())

class Suit(Enum):
    spades = auto()
    clubs = auto()
    diamonds = auto()
    hearts = auto()

    def __str__(self) -> str:
        symbols = list('♤♧♢♡')
        return symbols[self.value-1]
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self.name}'
    
Suits = typing.NewType('Suits', Suit)

class CardValue():
    FACE = ["A",2,3,4,5,6,7,8,9,10,"J","Q","K"]
    RANK = [2,3,4,5,6,7,8,9,10,'J','Q','K','A']
    BJ_VALUES = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,"J":10,"Q":10,"K":10,"A":11}

    def __init__(self, value: Union[str, int]) -> None:
        self._value = None
        self.value = value
        
    def __str__(self) -> str:
        return self.face_value
    
    def __repr__(self) -> str:
        return f'CardValue({self.face_value})'
    
    def __eq__(self, __value: object) -> bool:
        return self.bj_face_value == __value.bj_face_value
    
    @property
    def value(self) -> int:
        return self._value
    
    @value.setter
    def value(self, v: Union[str, int]) -> None:
        if type(v) == str:
            self._value = CardValue.FACE.index(v.upper())
        elif v <= len(CardValue.FACE):
            self._value = v - 1
        else:
            raise ValueError(f'Invalid card value {v}')
        
    @property
    def rank(self) -> int:
        return CardValue.RANK.index(self.face_value)
        
    @property
    def face_value(self) -> str:
        return str(CardValue.FACE[self.value])
    
    @property
    def bj_face_value(self) -> int:
        return CardValue.BJ_VALUES[self.face_value]
    
    @property
    def bj_face_str(self) -> str:
        return str(self.bj_face_value) if self.face_value != 'A' else str(self.bj_face_value)
        

class Card():
    def __init__(self, value:CardValue=CardValue('A'), suit:Suits=Suit(1)) -> None:
        self._value = value
        self._suit = suit

    def __str__(self) -> str:
        return str(self._suit)+str(self.value.face_value)
    
    def __repr__(self) -> str:
        return f'Card({str(self._suit)}{str(self._value)})'
    
    def __eq__(self, __value: object) -> bool:
        return self.value.value == __value.value.value and self.suit == __value.suit

    @property
    def value(self) -> int:
        return self._value
    
    @value.setter
    def value(self, v: int) -> None:
        self._value = v

    @property
    def suit(self) -> Suits:
        return self._suit
    
    @suit.setter
    def suit(self, v: Suits) -> None:
        self._suit = v

    @property
    def rank(self) -> int:
        return self.value.rank

class Deck():
    def __init__(self, shuffle:bool=True, decks:int=1) -> None:
        self._deck: list[Card] = [Card(CardValue(v),s) for v in CardValue.FACE for s in Suit] * decks
        if shuffle: self.shuffle()

    def __str__(self) -> str:
        return str(self._deck)
    
    def __repr__(self) -> str:
        return f'<Deck with {len(self._deck)} cards>'
    
    def __sizeof__(self) -> int:
        return len(self._deck)

    def shuffle(self) -> None:
        random.shuffle(self._deck)

    def draw(self, amount:int=1) -> Union[list[Card], Card]:
        data = [self._deck.pop(0) for x in range(0,amount)]
        return data if len(data) > 1 else data[0]
    
    def list(self) -> list[Card]:
        return self._deck
    
    def add(self, card:Card, index:int=0) -> None:
        self._deck.insert(index,card)


def shuffle():
    shuffled = []
    _deck = []
    suits = list("♡♤♧♢")
    numbers = [2,3,4,5,6,7,8,9,10,"J","Q","K","A"]
    values = {2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,"J":10,"Q":10,"K":10,"A":11}
    for s in suits:
        for n in range(0,len(numbers)):
            _deck.append([str(s) + str(numbers[n]), n+2, values[numbers[n]]])

    tdeck = _deck
    for i in range(0,len(_deck)):
        lent = len(tdeck)
        t = random.randint(1,lent) - 1
        shuffled.append(tdeck[t])
        tdeck.remove(tdeck[t])

    return shuffled

def shuffle_poker():
    shuffled = []
    _deck = []
    suits = list("♡♤♧♢")
    _suits = {"♡":"H","♤":"S","♧":"C","♢":"D"}
    numbers = [2,3,4,5,6,7,8,9,10,"J","Q","K","A"]
    #values = {2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,"J":11,"Q":12,"K":13,"A":14}
    for s in suits:
        for n in range(0,len(numbers)):
            _deck.append([str(s) + str(numbers[n]), _suits[s]], n+2)

    tdeck = _deck
    for i in range(0,len(_deck)):
        lent = len(tdeck)
        t = random.randint(1,lent) - 1
        shuffled.append(tdeck[t])
        tdeck.remove(tdeck[t])

    return shuffled