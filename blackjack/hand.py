class Hand:
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0
        self.bet = 0

    def add_card(self, card):
        self.cards.append(card)
        self.value += card.value

        if card.rank == 'Ace':
            self.aces += 1
        self.adjust_for_ace()

    def adjust_for_ace(self):
        while self.value > 21 and self.aces > 0:
            self.value -= 10
            self.aces -= 1
    def get_display_value(self):
        if self.aces > 0 and self.value < 21:
            return f"{self.value - 10}/{self.value}"
        elif self.value <22:
            return f"{self.value}"
        else:
            return f"Bust"