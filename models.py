import random

SUITS = ('Hearts', 'Diamonds', 'Clubs', 'Spades')
VALUES = {'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6, 'Seven': 7, 'Eight': 8, 
    'Nine': 9, 'Ten': 10, 'Jack': 10, 'Queen': 10, 'King': 10, 'Ace': 11
}


class Card:
    def  __init__(self, suit, rank, value):
        self.suit = suit
        self.rank = rank
        self.value = value

    def __str__ (self):
        return f"{self.rank} of {self.suit}"
    
class Deck:
    def __init__(self, num_decks = 1):
        self.all_cards = []
        for i in range(num_decks):
            for suit in SUITS:
                for rank, value in VALUES.items():
                    created_card = Card(suit,rank,value)
                    self.all_cards.append(created_card)

    def shuffle(self):
        random.shuffle(self.all_cards)

    def deal_one(self):
        return self.all_cards.pop()