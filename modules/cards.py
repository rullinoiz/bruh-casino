import random
import time
import typing
from typing import Union
from enum import Enum, auto

random.seed(time.time())

class Suit(Enum):
    spades: auto = auto()
    clubs: auto = auto()
    diamonds: auto = auto()
    hearts: auto = auto()

    def __str__(self) -> str:
        symbols = list('♤♧♢♡')
        return symbols[self.value-1]

    @property
    def videopoker_value(self) -> str:
        symbols = list('scdh')
        return symbols[self.value-1]
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self.name}'
    
Suits = typing.NewType('Suits', Suit)

class CardValue(object):
    FACE = ["A",2,3,4,5,6,7,8,9,10,"J","Q","K"]
    RANK = [2,3,4,5,6,7,8,9,10,'J','Q','K','A']
    BJ_VALUES = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,"J":10,"Q":10,"K":10,"A":11}
    VIDEOPOKER_VALUES = ['A',2,3,4,5,6,7,8,9,'T','J','Q','K']

    def __init__(self, value: Union[str, int]) -> None:
        self._value = None
        self.value = value
        
    def __str__(self) -> str:
        return self.face_value
    
    def __repr__(self) -> str:
        return f'CardValue({self.face_value})'
    
    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, CardValue): return False
        return self.bj_face_value == __value.bj_face_value
    
    @property
    def value(self) -> int:
        return self._value
    
    @value.setter
    def value(self, v: Union[str, int]) -> None:
        if isinstance(v, str):
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

    @property
    def videopoker_value(self) -> str:
        return str(self.VIDEOPOKER_VALUES[self.value])


class Card(object):
    def __init__(self, value:CardValue=CardValue('A'), suit:Suit=Suit(1)) -> None:
        self._value: CardValue = value
        self._suit: Suit = suit

    def __str__(self) -> str:
        return str(self._suit)+str(self.value.face_value)
    
    def __repr__(self) -> str:
        return f'Card({str(self._suit)}{str(self._value)})'
    
    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Card): return False
        return self.value.value == __value.value.value and self.suit == __value.suit

    @property
    def value(self) -> CardValue:
        return self._value
    
    @value.setter
    def value(self, v: int) -> None:
        self._value = v

    @property
    def suit(self) -> Suit:
        return self._suit
    
    @suit.setter
    def suit(self, v: Suit) -> None:
        self._suit = v

    @property
    def rank(self) -> int:
        return self.value.rank

    @property
    def videopoker_value(self) -> str:
        return self.value.videopoker_value + self.suit.videopoker_value

class Deck(object):
    def __init__(self, decks:int=None, deck:list[Card]=None) -> None:
        if decks:
            self._deck: list[Card] = [Card(CardValue(v),s) for v in CardValue.FACE for s in Suit] * decks
        elif deck:
            self._deck: list[Card] = deck if type(deck) is list else [deck]

    def __str__(self) -> str:
        return str(self._deck)
    
    def __repr__(self) -> str:
        return f'<Deck with {len(self)} cards>'
    
    def __len__(self) -> int:
        return len(self._deck)

    def __getitem__(self, index: int) -> Card:
        return self._deck[index]

    def __setitem__(self, index: int, value: Card) -> None:
        self._deck[index] = value

    def __add__(self, obj) -> None:
        self._deck += obj.list()

    def shuffle(self) -> None:
        random.shuffle(self._deck)

    def draw(self, amount:int=1) -> Union[list[Card], Card]:
        data = [self._deck.pop(0) for _ in range(0,amount)]
        return data if len(data) > 1 else data[0]
    
    def list(self) -> list[Card]:
        return self._deck
    
    def add(self, card:Card, index:int=0) -> None:
        self._deck.insert(index,card)

    def append(self, card:Card) -> None:
        self._deck.append(card)


class BlackjackHand(Deck):
    def __init__(self, deck:list[Card]) -> None:
        super().__init__(deck=deck)
        self._doubled: bool = False

    def __int__(self) -> int:
        return int(str(self.toVal()).split('/')[0])

    def __str__(self) -> str:
        t = [str(i) for i in self.list()]
        if self.doubled: t[-1] = '[' + str(t[-1]) + ']'
        return ('⭐️' if self.is_blackjack() else '') + ' '.join(t)

    @property
    def busted(self) -> bool:
        return int(self) > 21

    def is_blackjack(self) -> bool:
        return len(self) == 2 and int(self) == 21

    @property
    def doubled(self) -> bool:
        return self._doubled

    @doubled.setter
    def doubled(self, val:bool) -> None:
        self._doubled = val

    def toVal(self) -> Union[str, int]:
        t: typing.Union[str, int] = 0
        t2: int = 0
        a: bool = False
        for i in self.list():
            if i.value.bj_face_value == 11:
                if t + 11 <= 21:
                    t += 11
                else:
                    t += 1
                t2 += 1
                a = True
            else:
                t += i.value.bj_face_value
                t2 += i.value.bj_face_value

        if t > 21: t = t2
        elif t == t2: pass
        elif a: t = f'{t}/{t2}'

        return t



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
