from models import Deck
from player import Player, Dealer, Hand
import ui

#Inicjalizacja
player = Player(name="Gracz", bankroll=1000)
dealer = Dealer()
shoe = Deck(num_decks=5)
shoe.shuffle()

    
# --- POCZĄTEK RUNDY ---
print(f"Twój portfel: {player.bankroll} PLN")

# 1. Pobieranie zakładu
bet = int(input("Ile obstawiasz? "))
player.bankroll -= bet

# 2. Resetowanie stołu przed nowym rozdaniem
player.hands = []            # Czyścimy stare ręce gracza
first_hand = Hand()          # Tworzymy nową pustą rękę...
player.add_hand(first_hand)  # ...i przypisujemy ją graczowi
dealer.hand = Hand()         # Czyścimy rękę krupiera

# 3. Rozdanie początkowe (po 2 karty naprzemiennie)
for _ in range(2):
    player.hands[0].add_card(shoe.deal_one())
    dealer.hand.add_card(shoe.deal_one())

# 4. Pokazanie stołu (krupier ukrywa jedną kartę)
ui.show_board(player, dealer, reveal_dealer=False)

# Sprawdzenie Black Jackow graczy
player_hands_bj = []
for i in range len(player.hands):
    player_hands_bj = (len(player.hands[i].cards) == 2 and player.hands[i].value == 21)

dealer_has_bj = dealer.check_for_blackjack()