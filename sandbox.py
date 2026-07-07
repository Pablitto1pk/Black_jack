from blackjack.cards import Card
from blackjack.hand import Hand
from blackjack.participants import Player, Dealer

print("--- TESTOWANIE LOGIKI ASÓW ---")

# Tworzymy pustą rękę
test_hand = Hand()

# Dajemy graczowi Króla (10) i Asa (11)
test_hand.add_card(Card('Spades', '6', 6))
test_hand.add_card(Card('Hearts', 'Ace', 11))


# Dodajemy drugiego Asa (11)
print("\nDobieramy drugiego Asa...")
test_hand.add_card(Card('Clubs', '5', 5))
print(f"Suma przed korektą: {test_hand.value}") 

# Odpalamy naszą funkcję naprawczą
test_hand.adjust_for_ace()
print(f"Suma po korekcie: {test_hand.value}") 