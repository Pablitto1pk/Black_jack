class Hand:
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0


    def add_card(self, card):
        self.cards.append(card)
        self.value += card.value

        if card.rank == 'Ace':
            self.aces += 1

    def adjust_for_ace(self):
        while self.value > 21 and self.aces > 0:
            self.value -= 10
            self.aces -= 1
    def get_display_value(self):
        if self.aces > 0 and self.value < 21:
            return f"{self.value - 10}/{self.value}"

class Player:
    def __init__ (self, name = "Gracz", bankroll = 1000):
        self.name = name
        self.bankroll = bankroll
        self.hands = [] #lista rąk

    def add_hand(self, hand):
        self.hands.append(hand)

class Dealer:
    def __init__ (self):
        self.name = "Krupier"
        self.hand = Hand()
    def check_for_blackjack(self):
        if len(self.hand.cards) == 2 and self.hand.value == 21:
            up_card = self.hand.card[0]

            if up_card.value == 10 or up_card.value == 11:
                return True
        return False