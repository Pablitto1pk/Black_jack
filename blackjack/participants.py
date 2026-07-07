from blackjack.hand import Hand

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